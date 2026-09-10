from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    eia_api_key: str
    eia_base_url: str = "https://api.eia.gov/v2/electricity/rto/region-data/data/"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
