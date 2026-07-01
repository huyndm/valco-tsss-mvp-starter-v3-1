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


class FreeLLMAPIClient:
    def __init__(self, endpoint: str | None = None):
        self.endpoint = endpoint or settings.freellmapi_chat_endpoint
        assert_no_direct_provider_url(self.endpoint)
