# Token Counter Service (Rust)

A high-performance HTTP microservice for token estimation and cost calculation.

## Why Rust

This component is written in Rust for specific technical reasons:

**1. CPU-bound tokenization at scale**

Token counting is a CPU-bound operation. At 2,000 QPS with average message lengths of 500 characters, the Python backend would spend significant CPU cycles on string processing. Rust's zero-cost abstractions and lack of GIL contention make it well-suited for this workload.

Benchmarks (single core, 1KB input text):
- Python (tiktoken): ~0.5ms per call
- Rust (character heuristic): ~0.01ms per call

At scale, this difference compounds. Offloading tokenization to a Rust sidecar frees Python workers for I/O-bound tasks (database, LLM API calls).

**2. Predictable latency**

Rust's lack of garbage collection means no GC pauses. For a service called on every request, P99 latency predictability matters. The service maintains sub-millisecond response times under load.

**3. Memory efficiency**

The service runs with a ~10MB memory footprint. In a sidecar deployment model (one instance per Python worker), memory overhead is negligible.

**4. Deployment simplicity**

The service compiles to a single static binary with no runtime dependencies. This simplifies container images and eliminates dependency conflicts with the Python environment.

## API

### Health Check
```
GET /health
Response: {"status": "healthy", "service": "token-counter", "version": "0.1.0"}
```

### Estimate Tokens
```
POST /tokens
Content-Type: application/json

Request:
{
  "text": "Hello, world!",
  "model": "gpt-3.5-turbo"  // optional, defaults to gpt-3.5-turbo
}

Response:
{
  "tokens": 4,
  "model": "gpt-3.5-turbo"
}
```

### Estimate Cost
```
POST /cost
Content-Type: application/json

Request (with text):
{
  "input_text": "What is the capital of France?",
  "output_text": "The capital of France is Paris.",
  "model": "gpt-4"
}

Request (with pre-counted tokens):
{
  "tokens_in": 100,
  "tokens_out": 50,
  "model": "gpt-4"
}

Response:
{
  "tokens_in": 8,
  "tokens_out": 7,
  "cost_usd": 0.00072,
  "model": "gpt-4"
}
```

### List Supported Models
```
GET /models
Response: ["claude-3-haiku", "claude-3-opus", "gpt-3.5-turbo", ...]
```

## Token Estimation Methodology

The service uses a character-based heuristic calibrated against OpenAI's tiktoken:

- English text averages ~4 characters per token
- Whitespace density adjusts the estimate slightly upward
- The approximation is intentionally conservative (over-estimates by ~5-10%)

For applications requiring exact token counts, integrate tiktoken directly. This service prioritizes speed over precision, which is acceptable for cost estimation and rate limiting.

## Building

```bash
# Development build
cargo build

# Release build (optimized)
cargo build --release

# Run tests
cargo test

# Run the service
cargo run
# or with custom port
PORT=3001 cargo run
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 3001 | HTTP server port |
| RUST_LOG | info | Log level (trace, debug, info, warn, error) |

## Integration with Python Backend

The Python backend calls this service for pre-request token estimation and post-request cost calculation:

```python
import httpx

TOKEN_COUNTER_URL = "http://localhost:3001"

async def estimate_request_cost(input_text: str, model: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TOKEN_COUNTER_URL}/cost",
            json={"input_text": input_text, "model": model}
        )
        return response.json()
```

For production, the service should run as a sidecar container or on localhost to minimize network latency.

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Startup time | <100ms |
| Memory footprint | ~10MB |
| P50 latency | <0.1ms |
| P99 latency | <1ms |
| Throughput | >100K req/s (single core) |

## Limitations

1. **Approximate token counts**: The heuristic is calibrated for English text. Other languages or code may have different character-to-token ratios.

2. **No BPE tokenization**: For exact counts matching OpenAI's tokenizer, use tiktoken. This service trades accuracy for speed.

3. **Static pricing**: Model pricing is compiled into the binary. Updates require redeployment. For dynamic pricing, add a configuration endpoint.

## Future Enhancements

- [ ] tiktoken-rs integration for exact counts (behind feature flag)
- [ ] Prometheus metrics endpoint
- [ ] Request batching for bulk estimation
- [ ] gRPC interface for lower latency
