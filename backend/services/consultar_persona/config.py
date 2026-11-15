from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    PGHOST: str = "127.0.0.1"
    PGPORT: int = 15432
    PGDATABASE: str = "gestion_personas"
    PGUSER: str = "gestion_api"
    PGPASSWORD: str
    ENTRA_TENANT_ID: str
    ENTRA_API_CLIENT_ID: str
    ENTRA_REQUIRED_SCOPE: str = "personas.leer"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


config = Config()
