from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./valco_tsss.db"
    freellmapi_chat_endpoint: str = "http://localhost:3001/v1/chat/completions"
    max_raw_candidates: int = 1000
    top_recommended_count: int = 10
    final_main_count: int = 3
    max_main_adjustment_ratio: float = 0.40

    # OmniRoute LLM gateway settings (Phase 3.4)
    omniroute_base_url: str = "http://localhost:20128/v1"
    omniroute_api_key: str | None = None
    omniroute_model: str = "groq/llama-3.3-70b-versatile"


settings = Settings()
