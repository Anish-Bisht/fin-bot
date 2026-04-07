import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # ── Required ─────────────────────────────────────────────────────────────
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    sqlite_db_path: str = ".data/finbot.db"

    # ── Optional — generate a strong random key if not provided ──────────────
    # In production, always set SECRET_KEY explicitly in your .env
    secret_key: str = Field(default_factory=lambda: secrets.token_hex(32))


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def validate_keys(self) -> None:
        """Call this at startup to surface config problems early."""
        if not self.groq_api_key or not self.groq_api_key.startswith("gsk_"):
            raise ValueError(
                "GROQ_API_KEY is missing or invalid. "
                "Set it in your .env file (must start with 'gsk_')."
            )
        if self.secret_key == "placeholder_replace_in_prod":
            import warnings
            warnings.warn(
                "SECRET_KEY is using the insecure placeholder. "
                "Set a strong random SECRET_KEY in your .env for production.",
                stacklevel=2,
            )


settings = Settings()