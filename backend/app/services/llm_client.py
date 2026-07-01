import json
from typing import Any

import httpx

from app.config import settings

BLOCKED_PROVIDER_DOMAINS = [
    "api.openai.com",
    "generativelanguage.googleapis.com",
    "api.groq.com",
    "api.anthropic.com",
    "api.mistral.ai",
    "api.cohere.com",
]


def assert_no_direct_provider_url(url: str) -> None:
    if any(domain in url for domain in BLOCKED_PROVIDER_DOMAINS):
        raise ValueError("Direct provider calls are forbidden. Use FreeLLMAPI gateway only.")


class GatewayUnavailableError(Exception):
    pass


class FreeLLMAPIClient:
    def __init__(self, endpoint: str | None = None, timeout_seconds: float = 15.0):
        self.endpoint = endpoint or settings.freellmapi_chat_endpoint
        assert_no_direct_provider_url(self.endpoint)
        self.timeout_seconds = timeout_seconds

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str = "freellmapi-default",
        temperature: float = 0.0,
        response_format_json: bool = False,
    ) -> dict[str, Any]:
        assert_no_direct_provider_url(self.endpoint)
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format_json:
            payload["response_format"] = {"type": "json_object"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(self.endpoint, json=payload)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            raise GatewayUnavailableError(f"FreeLLMAPI gateway call failed: {exc}") from exc

    async def check_health(self) -> dict[str, Any]:
        assert_no_direct_provider_url(self.endpoint)
        health_url = self.endpoint.rsplit("/chat/completions", 1)[0] + "/models"
        assert_no_direct_provider_url(health_url)
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(health_url)
                return {
                    "reachable": response.status_code < 500,
                    "status_code": response.status_code,
                    "endpoint": self.endpoint,
                }
        except httpx.HTTPError as exc:
            return {
                "reachable": False,
                "status_code": None,
                "endpoint": self.endpoint,
                "error": str(exc),
            }
