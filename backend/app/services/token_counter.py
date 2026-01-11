"""
Token Counter Client - Integration with Rust token counting service.

This module provides a client for the Rust token counter microservice,
with fallback to local estimation if the service is unavailable.
"""
import httpx
import structlog
from typing import Optional, Dict
from functools import lru_cache

logger = structlog.get_logger()


class TokenCounterClient:
    """
    Client for the Rust token counter service.

    Provides token estimation and cost calculation with automatic
    fallback to local estimation on service unavailability.
    """

    def __init__(self, base_url: str, timeout: float = 0.5, enabled: bool = True):
        """
        Initialize the token counter client.

        Args:
            base_url: URL of the Rust token counter service
            timeout: Request timeout in seconds (default 0.5s for fast-fail)
            enabled: Whether to use the Rust service (False = always use fallback)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.enabled = enabled
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _local_estimate_tokens(self, text: str) -> int:
        """
        Local fallback token estimation.

        Uses the same algorithm as the Rust service for consistency.
        """
        if not text:
            return 0

        char_count = len(text)
        base_estimate = (char_count + 3) // 4  # ceil(char_count / 4)

        whitespace_count = sum(1 for c in text if c.isspace())
        whitespace_factor = 1.0 + (whitespace_count / char_count) * 0.1

        return int(base_estimate * whitespace_factor + 0.5)

    def _local_calculate_cost(self, model: str, tokens_in: int, tokens_out: int) -> float:
        """
        Local fallback cost calculation.

        Mirrors the Rust service pricing for consistency.
        """
        pricing = {
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-3.5-turbo-0125": {"input": 0.0005, "output": 0.0015},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        }

        model_pricing = pricing.get(model, pricing["gpt-3.5-turbo"])
        cost_in = (tokens_in / 1000) * model_pricing["input"]
        cost_out = (tokens_out / 1000) * model_pricing["output"]

        return round(cost_in + cost_out, 8)

    async def estimate_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """
        Estimate token count for the given text.

        Args:
            text: The text to tokenize
            model: Model name (for logging, not used in estimation)

        Returns:
            Estimated token count
        """
        if not self.enabled:
            return self._local_estimate_tokens(text)

        try:
            client = await self._get_client()
            response = await client.post(
                "/tokens",
                json={"text": text, "model": model}
            )
            response.raise_for_status()
            data = response.json()
            return data["tokens"]

        except Exception as e:
            logger.warning(
                "token_counter_fallback",
                error=str(e),
                reason="rust_service_unavailable"
            )
            return self._local_estimate_tokens(text)

    async def estimate_cost(
        self,
        model: str,
        input_text: Optional[str] = None,
        output_text: Optional[str] = None,
        tokens_in: Optional[int] = None,
        tokens_out: Optional[int] = None,
    ) -> Dict:
        """
        Estimate cost for an LLM call.

        Provide either text (for token estimation) or pre-counted tokens.

        Args:
            model: Model name for pricing lookup
            input_text: Input text (will be tokenized)
            output_text: Output text (will be tokenized)
            tokens_in: Pre-counted input tokens
            tokens_out: Pre-counted output tokens

        Returns:
            Dict with tokens_in, tokens_out, cost_usd, model
        """
        if not self.enabled:
            final_tokens_in = tokens_in if tokens_in is not None else self._local_estimate_tokens(input_text or "")
            final_tokens_out = tokens_out if tokens_out is not None else self._local_estimate_tokens(output_text or "")
            cost = self._local_calculate_cost(model, final_tokens_in, final_tokens_out)
            return {
                "tokens_in": final_tokens_in,
                "tokens_out": final_tokens_out,
                "cost_usd": cost,
                "model": model,
                "source": "local"
            }

        try:
            client = await self._get_client()
            payload = {"model": model}
            if input_text is not None:
                payload["input_text"] = input_text
            if output_text is not None:
                payload["output_text"] = output_text
            if tokens_in is not None:
                payload["tokens_in"] = tokens_in
            if tokens_out is not None:
                payload["tokens_out"] = tokens_out

            response = await client.post("/cost", json=payload)
            response.raise_for_status()
            data = response.json()
            data["source"] = "rust"
            return data

        except Exception as e:
            logger.warning(
                "token_counter_cost_fallback",
                error=str(e),
                reason="rust_service_unavailable"
            )
            final_tokens_in = tokens_in if tokens_in is not None else self._local_estimate_tokens(input_text or "")
            final_tokens_out = tokens_out if tokens_out is not None else self._local_estimate_tokens(output_text or "")
            cost = self._local_calculate_cost(model, final_tokens_in, final_tokens_out)
            return {
                "tokens_in": final_tokens_in,
                "tokens_out": final_tokens_out,
                "cost_usd": cost,
                "model": model,
                "source": "local_fallback"
            }

    async def health_check(self) -> bool:
        """Check if the Rust service is healthy."""
        if not self.enabled:
            return False

        try:
            client = await self._get_client()
            response = await client.get("/health")
            return response.status_code == 200
        except Exception:
            return False


# Singleton instance management
_token_counter_client: Optional[TokenCounterClient] = None


def get_token_counter(
    base_url: str = "http://localhost:3001",
    timeout: float = 0.5,
    enabled: bool = True
) -> TokenCounterClient:
    """
    Get or create the global token counter client.

    This function provides a singleton pattern for the client,
    ensuring connection reuse across requests.
    """
    global _token_counter_client
    if _token_counter_client is None:
        _token_counter_client = TokenCounterClient(
            base_url=base_url,
            timeout=timeout,
            enabled=enabled
        )
    return _token_counter_client


async def close_token_counter():
    """Close the global token counter client."""
    global _token_counter_client
    if _token_counter_client is not None:
        await _token_counter_client.close()
        _token_counter_client = None
