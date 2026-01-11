//! Token Counter Service
//!
//! A high-performance HTTP service for estimating token counts and costs
//! for LLM API calls. Designed to offload tokenization from Python workers.
//!
//! Token estimation uses a character-based heuristic calibrated against
//! OpenAI's tiktoken for English text. This is an approximation—actual
//! token counts may vary by ±10% depending on content.

use axum::{
    extract::Json,
    http::StatusCode,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::net::SocketAddr;
use tower_http::cors::{Any, CorsLayer};
use tracing::info;
use tracing_subscriber::EnvFilter;

/// Model pricing configuration (USD per 1K tokens)
/// Updated: January 2024
struct ModelPricing {
    input: f64,
    output: f64,
}

fn get_model_pricing() -> HashMap<&'static str, ModelPricing> {
    let mut pricing = HashMap::new();

    // GPT-3.5 Turbo
    pricing.insert("gpt-3.5-turbo", ModelPricing { input: 0.0005, output: 0.0015 });
    pricing.insert("gpt-3.5-turbo-0125", ModelPricing { input: 0.0005, output: 0.0015 });
    pricing.insert("gpt-3.5-turbo-1106", ModelPricing { input: 0.001, output: 0.002 });

    // GPT-4
    pricing.insert("gpt-4", ModelPricing { input: 0.03, output: 0.06 });
    pricing.insert("gpt-4-0613", ModelPricing { input: 0.03, output: 0.06 });

    // GPT-4 Turbo
    pricing.insert("gpt-4-turbo", ModelPricing { input: 0.01, output: 0.03 });
    pricing.insert("gpt-4-turbo-preview", ModelPricing { input: 0.01, output: 0.03 });
    pricing.insert("gpt-4-1106-preview", ModelPricing { input: 0.01, output: 0.03 });

    // GPT-4o
    pricing.insert("gpt-4o", ModelPricing { input: 0.005, output: 0.015 });
    pricing.insert("gpt-4o-mini", ModelPricing { input: 0.00015, output: 0.0006 });

    // Claude models (for future provider support)
    pricing.insert("claude-3-opus", ModelPricing { input: 0.015, output: 0.075 });
    pricing.insert("claude-3-sonnet", ModelPricing { input: 0.003, output: 0.015 });
    pricing.insert("claude-3-haiku", ModelPricing { input: 0.00025, output: 0.00125 });

    pricing
}

/// Estimate token count from text using character-based heuristic.
///
/// Calibration methodology:
/// - English text averages ~4 characters per token with GPT tokenizers
/// - Whitespace and punctuation count as partial tokens
/// - This approximation is intentionally conservative (slightly over-estimates)
///
/// For production use with strict accuracy requirements, integrate tiktoken
/// via PyO3 bindings or use the tiktoken-rs crate.
fn estimate_tokens(text: &str) -> u32 {
    if text.is_empty() {
        return 0;
    }

    // Character-based estimation: ~4 chars per token for English
    // Add small buffer for special tokens and edge cases
    let char_count = text.chars().count();
    let base_estimate = (char_count as f64 / 4.0).ceil() as u32;

    // Account for whitespace density (more spaces = slightly more tokens)
    let whitespace_count = text.chars().filter(|c| c.is_whitespace()).count();
    let whitespace_factor = 1.0 + (whitespace_count as f64 / char_count as f64) * 0.1;

    ((base_estimate as f64) * whitespace_factor).ceil() as u32
}

/// Calculate cost based on token counts and model pricing
fn calculate_cost(model: &str, tokens_in: u32, tokens_out: u32) -> f64 {
    let pricing = get_model_pricing();

    let model_pricing = pricing.get(model).unwrap_or_else(|| {
        // Default to GPT-3.5 pricing for unknown models
        pricing.get("gpt-3.5-turbo").unwrap()
    });

    let input_cost = (tokens_in as f64 / 1000.0) * model_pricing.input;
    let output_cost = (tokens_out as f64 / 1000.0) * model_pricing.output;

    // Round to 8 decimal places for precision
    ((input_cost + output_cost) * 100_000_000.0).round() / 100_000_000.0
}

// === Request/Response Types ===

#[derive(Debug, Deserialize)]
struct TokenEstimateRequest {
    /// Input text to tokenize
    text: String,
    /// Model name for pricing lookup
    #[serde(default = "default_model")]
    model: String,
}

fn default_model() -> String {
    "gpt-3.5-turbo".to_string()
}

#[derive(Debug, Serialize)]
struct TokenEstimateResponse {
    tokens: u32,
    model: String,
}

#[derive(Debug, Deserialize)]
struct CostEstimateRequest {
    /// Input text (will be tokenized)
    input_text: Option<String>,
    /// Pre-counted input tokens (if already known)
    tokens_in: Option<u32>,
    /// Output text (will be tokenized)
    output_text: Option<String>,
    /// Pre-counted output tokens (if already known)
    tokens_out: Option<u32>,
    /// Model name for pricing lookup
    #[serde(default = "default_model")]
    model: String,
}

#[derive(Debug, Serialize)]
struct CostEstimateResponse {
    tokens_in: u32,
    tokens_out: u32,
    cost_usd: f64,
    model: String,
}

#[derive(Debug, Serialize)]
struct HealthResponse {
    status: &'static str,
    service: &'static str,
    version: &'static str,
}

#[derive(Debug, Serialize)]
struct ErrorResponse {
    error: String,
}

// === Handlers ===

async fn health() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "healthy",
        service: "token-counter",
        version: env!("CARGO_PKG_VERSION"),
    })
}

async fn estimate_tokens_handler(
    Json(req): Json<TokenEstimateRequest>,
) -> Result<Json<TokenEstimateResponse>, (StatusCode, Json<ErrorResponse>)> {
    if req.text.is_empty() {
        return Err((
            StatusCode::BAD_REQUEST,
            Json(ErrorResponse {
                error: "text field is required and cannot be empty".to_string(),
            }),
        ));
    }

    let tokens = estimate_tokens(&req.text);

    Ok(Json(TokenEstimateResponse {
        tokens,
        model: req.model,
    }))
}

async fn estimate_cost_handler(
    Json(req): Json<CostEstimateRequest>,
) -> Result<Json<CostEstimateResponse>, (StatusCode, Json<ErrorResponse>)> {
    // Determine input tokens
    let tokens_in = match (req.tokens_in, &req.input_text) {
        (Some(t), _) => t,
        (None, Some(text)) => estimate_tokens(text),
        (None, None) => 0,
    };

    // Determine output tokens
    let tokens_out = match (req.tokens_out, &req.output_text) {
        (Some(t), _) => t,
        (None, Some(text)) => estimate_tokens(text),
        (None, None) => 0,
    };

    if tokens_in == 0 && tokens_out == 0 {
        return Err((
            StatusCode::BAD_REQUEST,
            Json(ErrorResponse {
                error: "At least one of tokens_in, input_text, tokens_out, or output_text is required".to_string(),
            }),
        ));
    }

    let cost = calculate_cost(&req.model, tokens_in, tokens_out);

    Ok(Json(CostEstimateResponse {
        tokens_in,
        tokens_out,
        cost_usd: cost,
        model: req.model,
    }))
}

async fn list_models() -> Json<Vec<&'static str>> {
    let pricing = get_model_pricing();
    let mut models: Vec<&str> = pricing.keys().copied().collect();
    models.sort();
    Json(models)
}

#[tokio::main]
async fn main() {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive("info".parse().unwrap()))
        .with_target(false)
        .compact()
        .init();

    // CORS configuration for local development
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    // Build router
    let app = Router::new()
        .route("/health", get(health))
        .route("/tokens", post(estimate_tokens_handler))
        .route("/cost", post(estimate_cost_handler))
        .route("/models", get(list_models))
        .layer(cors);

    // Bind to port from environment or default
    let port: u16 = std::env::var("PORT")
        .unwrap_or_else(|_| "3001".to_string())
        .parse()
        .expect("PORT must be a valid u16");

    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    info!("Token counter service listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_estimate_tokens_empty() {
        assert_eq!(estimate_tokens(""), 0);
    }

    #[test]
    fn test_estimate_tokens_short() {
        // "Hello" = 5 chars, ~1-2 tokens
        let tokens = estimate_tokens("Hello");
        assert!(tokens >= 1 && tokens <= 3);
    }

    #[test]
    fn test_estimate_tokens_sentence() {
        // "The quick brown fox jumps over the lazy dog" = 43 chars, ~9-11 tokens
        let tokens = estimate_tokens("The quick brown fox jumps over the lazy dog");
        assert!(tokens >= 8 && tokens <= 15);
    }

    #[test]
    fn test_calculate_cost_gpt35() {
        // 1000 tokens in, 500 tokens out for gpt-3.5-turbo
        // Cost = (1000/1000 * 0.0005) + (500/1000 * 0.0015) = 0.0005 + 0.00075 = 0.00125
        let cost = calculate_cost("gpt-3.5-turbo", 1000, 500);
        assert!((cost - 0.00125).abs() < 0.0001);
    }

    #[test]
    fn test_calculate_cost_gpt4() {
        // 1000 tokens in, 500 tokens out for gpt-4
        // Cost = (1000/1000 * 0.03) + (500/1000 * 0.06) = 0.03 + 0.03 = 0.06
        let cost = calculate_cost("gpt-4", 1000, 500);
        assert!((cost - 0.06).abs() < 0.0001);
    }

    #[test]
    fn test_calculate_cost_unknown_model() {
        // Unknown model should default to gpt-3.5-turbo pricing
        let cost = calculate_cost("unknown-model", 1000, 500);
        let expected = calculate_cost("gpt-3.5-turbo", 1000, 500);
        assert_eq!(cost, expected);
    }
}
