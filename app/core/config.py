from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="AgentGo Biz AI")
    app_version: str = Field(default="0.1.0")
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:3000")
    min_analysis_days: int = Field(default=14)
    min_analysis_records: int = Field(default=50)
    pii_masking_enabled: bool = Field(default=True)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
