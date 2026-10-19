from pathlib import Path
from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
    app_name:str="Vul-Management"
    app_version:str="3.2.0"
    debug:bool=True
    database_url:str="sqlite:///./data/vul_management.db"
    db_schema_min:int=1
    db_schema_max:int=8
    telegram_api_id:str|None=None
    telegram_api_hash:str|None=None
    telegram_session:str="./data/telegram"
    jira_base_url:str|None=None
    jira_email:str|None=None
    jira_api_token:str|None=None
    jira_project_key:str|None=None
    jira_issue_type:str="Task"
    model_config=SettingsConfigDict(env_file=Path(__file__).resolve().parents[2]/".env",env_file_encoding="utf-8",extra="ignore")
settings=Settings()
