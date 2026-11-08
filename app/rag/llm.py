import math
import os
from collections.abc import Sequence
from typing import Protocol

import httpx


class LLMProvider(Protocol):
    def complete(self, messages: Sequence[dict[str, str]]) -> str:
        ...


class LLMError(RuntimeError):
    """The provider could not complete the request."""


class LLMTimeout(LLMError):
    pass


class LLMRateLimit(LLMError):
    def __init__(self, retry_after: str | None) -> None:
        super().__init__("LLM rate limit exceeded")
        self.retry_after = retry_after


class OpenRouterProvider:
    model = "qwen/qwen3.5-plus-02-15"

    def __init__(self, client: httpx.Client, *, timeout: float = 30.0) -> None:
        self._api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not self._api_key:
            raise ValueError("Set OPENROUTER_API_KEY")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive and finite")
        self._client = client
        self._timeout = timeout

    def complete(self, messages: Sequence[dict[str, str]]) -> str:
        try:
            response = self._client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self.model,
                    "messages": list(messages),
                    "stream": False,
                    "response_format": {"type": "json_object"},
                    "reasoning": {"effort": "none"},
                    "provider": {"require_parameters": True},
                    "max_tokens": 1024,
                },
                timeout=self._timeout,
                follow_redirects=False,
            )
        except httpx.TimeoutException:
            raise LLMTimeout("LLM request timed out") from None
        except httpx.RequestError:
            raise LLMError("LLM network request failed") from None

        if response.status_code == 429:
            raise LLMRateLimit(response.headers.get("Retry-After"))
        if not response.is_success:
            raise LLMError(f"LLM provider returned HTTP {response.status_code}")

        try:
            choice = response.json()["choices"][0]
            content = choice["message"]["content"]
            if choice["finish_reason"] == "stop" and isinstance(content, str) and content.strip():
                return content
        except (ValueError, KeyError, IndexError, TypeError):
            pass
        raise LLMError("LLM provider returned an invalid or incomplete completion")
