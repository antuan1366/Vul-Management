from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vul-Management"
    app_version: str = "1.2.0"
    debug: bool = True

    database_url: str = "sqlite:///./data/vul_management.db"

    db_schema_min: int = 1
    db_schema_max: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
