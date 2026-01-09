"""LLM service for chat completions with streaming."""
import openai
from typing import AsyncGenerator, List, Dict, Tuple
import time


class LLMService:
    """Service for interacting with LLM APIs (OpenAI)."""

    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7
    ) -> AsyncGenerator[Tuple[str, Dict], None]:
        """
        Stream chat completion tokens from OpenAI.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (e.g., "gpt-3.5-turbo", "gpt-4")
            temperature: Sampling temperature (0.0 to 2.0)

        Yields:
            Tuples of (token: str, metadata: dict)
            Final yield contains complete response metadata

        Example:
            >>> service = LLMService(api_key)
            >>> messages = [{"role": "user", "content": "Hello!"}]
            >>> async for token, metadata in service.stream_chat(messages):
            >>>     print(token, end="", flush=True)
        """
        start_time = time.time()
        full_content = ""

        # Rough token estimation (tokens_in)
        tokens_in = sum(len(msg.get("content", "").split()) for msg in messages)
        tokens_out = 0

        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=True
            )

            async for chunk in stream:
                # Handle content tokens
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_content += token
                    tokens_out += 1  # Rough estimate
                    yield token, {}

                # Handle usage metadata (sent in final chunk)
                if hasattr(chunk, 'usage') and chunk.usage:
                    tokens_in = chunk.usage.prompt_tokens
                    tokens_out = chunk.usage.completion_tokens

            # Calculate latency and cost
            latency_ms = int((time.time() - start_time) * 1000)
            cost = self._calculate_cost(model, tokens_in, tokens_out)

            # Yield final metadata
            yield "", {
                "done": True,
                "full_content": full_content,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "latency_ms": latency_ms,
                "cost": cost,
                "model": model
            }

        except Exception as e:
            # Re-raise with context
            raise Exception(f"LLM streaming error: {str(e)}") from e

    def _calculate_cost(self, model: str, tokens_in: int, tokens_out: int) -> float:
        """
        Calculate cost in USD for API call.

        Pricing as of Jan 2024 (update as needed):
        - gpt-3.5-turbo: $0.0005 / 1K input, $0.0015 / 1K output
        - gpt-4: $0.03 / 1K input, $0.06 / 1K output
        - gpt-4-turbo: $0.01 / 1K input, $0.03 / 1K output
        """
        pricing = {
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        }

        # Default to gpt-3.5-turbo pricing if model not found
        model_pricing = pricing.get(model, pricing["gpt-3.5-turbo"])

        cost_in = (tokens_in / 1000) * model_pricing["input"]
        cost_out = (tokens_out / 1000) * model_pricing["output"]

        return round(cost_in + cost_out, 6)

    async def get_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo"
    ) -> Dict:
        """
        Get non-streaming completion (for testing or simple use cases).

        Returns:
            Dict with 'content', 'tokens_in', 'tokens_out', 'cost', 'latency_ms'
        """
        start_time = time.time()

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages
        )

        latency_ms = int((time.time() - start_time) * 1000)
        tokens_in = response.usage.prompt_tokens
        tokens_out = response.usage.completion_tokens
        cost = self._calculate_cost(model, tokens_in, tokens_out)

        return {
            "content": response.choices[0].message.content,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": cost,
            "latency_ms": latency_ms,
            "model": model
        }
