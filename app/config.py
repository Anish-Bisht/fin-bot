from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    groq_api_key: str
    serpapi_api_key: str
    groq_model: str
    sqlite_db_path: str
    secret_key: str = "placeholder_replace_in_prod"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def validate_keys(self):
        if not self.groq_api_key or "gsk_" not in self.groq_api_key:
            raise ValueError("Invalid GROQ_API_KEY detected.")
        if not self.serpapi_api_key:
            raise ValueError("SERPAPI_API_KEY is missing.")

settings = Settings()

    

    
    