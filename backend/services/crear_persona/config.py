
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    PGHOST: str = "127.0.0.1"
    PGPORT: int = 15432
    PGDATABASE: str = "gestion_personas"
    PGUSER: str = "gestion_api"
    PGPASSWORD: str
    model_config = SettingsConfigDict(
        env_file=Path(__file__).with_name(".env"),
        extra="ignore",
    )


config = Config()
