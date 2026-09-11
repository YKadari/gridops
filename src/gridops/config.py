from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    eia_api_key: str
    eia_base_url: str = "https://api.eia.gov/v2/electricity/rto/region-data/data/"

    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    aws_profile: str | None = None
    aws_region: str = "us-east-1"
    s3_raw_bucket: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def postgres_dsn(self) -> str:
        return (
            f"host={self.postgres_host} "
            f"port={self.postgres_port} "
            f"dbname={self.postgres_db} "
            f"user={self.postgres_user} "
            f"password={self.postgres_password}"
        )