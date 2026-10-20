from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vul-Management"
    app_version: str = "3.5.0"
    debug: bool = True

    # DATA_DIR is resolved from the process working directory when relative.
    # DATABASE_URL can still explicitly override the default SQLite location.
    data_dir: Path = Path("./data")
    database_url: str | None = None
    session_secret: str | None = Field(default=None, validation_alias="VULM_SESSION_SECRET")
    bootstrap_admin_username: str = Field(default="admin", validation_alias="VULM_BOOTSTRAP_ADMIN_USERNAME")

    db_schema_min: int = 1
    db_schema_max: int = 11

    telegram_api_id: str | None = None
    telegram_api_hash: str | None = None
    telegram_session: str | None = None

    jira_base_url: str | None = None
    jira_email: str | None = None
    jira_api_token: str | None = None
    jira_project_key: str | None = None
    jira_issue_type: str = "Task"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def set_default_storage_paths(self):
        resolved_data_dir = self.data_dir.expanduser().resolve()
        self.data_dir = resolved_data_dir

        if not self.database_url:
            database_path = (resolved_data_dir / "vul_management.db").as_posix()
            self.database_url = f"sqlite:///{database_path}"

        if not self.telegram_session:
            self.telegram_session = str(resolved_data_dir / "telegram")

        return self


settings = Settings()
