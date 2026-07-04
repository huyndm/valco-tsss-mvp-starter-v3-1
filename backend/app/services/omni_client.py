"""OmniRoute OpenAI-compatible LLM gateway client.

OmniRoute is the LLM gateway only. It does not perform verified web search by itself.
This module provides an async OpenAI /v1/chat/completions compatible client.
"""

from typing import Any

import httpx

from app.config import settings
from app.services.llm_client import GatewayUnavailableError, assert_no_direct_provider_url


class OmniRouteClient:
    """OpenAI-compatible async client for OmniRoute LLM gateway.

    Reads environment variables:
      OMNIROUTE_BASE_URL  default http://localhost:20128/v1
      OMNIROUTE_API_KEY   optional (raises GatewayUnavailableError if missing)
      OMNIROUTE_MODEL     default groq/llama-3.3-70b-versatile
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30.0,
    ):
        self.base_url = (base_url or settings.omniroute_base_url).rstrip("/")
        self.api_key = api_key or settings.omniroute_api_key
        self.model = model or settings.omniroute_model
        self.timeout_seconds = timeout_seconds

        if not self.api_key:
            raise GatewayUnavailableError(
                "OMNIROUTE_API_KEY is not set. OmniRoute gateway requires an API key."
            )

        # Safety: ensure we are not calling provider APIs directly
        assert_no_direct_provider_url(self.base_url)

        self.chat_endpoint = f"{self.base_url}/chat/completions"

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        response_format_json: bool = False,
    ) -> dict[str, Any]:
        """Send a chat completion request to the OmniRoute gateway.

        Compatible with OpenAI /v1/chat/completions.
        """
        assert_no_direct_provider_url(self.base_url)
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format_json:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(self.chat_endpoint, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            raise GatewayUnavailableError(f"OmniRoute gateway call failed: {exc}") from exc
        except ValueError as exc:
            raise GatewayUnavailableError(
                f"OmniRoute gateway returned invalid response: {exc}"
            ) from exc

    async def check_health(self) -> dict[str, Any]:
        """Check if the OmniRoute gateway is reachable via /models endpoint."""
        assert_no_direct_provider_url(self.base_url)
        models_endpoint = f"{self.base_url}/models"
        assert_no_direct_provider_url(models_endpoint)
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(models_endpoint, headers=headers)
                return {
                    "reachable": response.status_code < 500,
                    "status_code": response.status_code,
                    "endpoint": self.chat_endpoint,
                    "model": self.model,
                    "gateway": "omniroute",
                }
        except httpx.HTTPError as exc:
            return {
                "reachable": False,
                "status_code": None,
                "endpoint": self.chat_endpoint,
                "model": self.model,
                "gateway": "omniroute",
                "error": str(exc),
            }
