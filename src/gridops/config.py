from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    # --------------------------------------------------------
    # EIA ingestion settings
    #
    # Not required by the production forecast API.
    # Ingestion code should only use these when ingestion runs.
    # --------------------------------------------------------

    eia_api_key: str | None = None

    eia_base_url: str = (
        "https://api.eia.gov/v2/"
        "electricity/rto/region-data/data/"
    )

    # --------------------------------------------------------
    # PostgreSQL settings
    #
    # PostgreSQL is used by the offline analytics /
    # dbt / training path, but not by production inference.
    # --------------------------------------------------------

    postgres_db: str | None = None
    postgres_user: str | None = None
    postgres_password: str | None = None

    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # --------------------------------------------------------
    # AWS / production serving settings
    # --------------------------------------------------------

    aws_profile: str | None = None
    aws_region: str = "us-east-1"

    # Production forecasting requires the S3 bucket because
    # champion model artifacts are loaded from S3.
    s3_raw_bucket: str

    dynamodb_demand_table: str = (
        "gridops-demand-serving"
    )

    forecast_history_table: str = "gridops-forecast-history"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def postgres_dsn(self) -> str:
        missing = []

        if not self.postgres_db:
            missing.append("POSTGRES_DB")

        if not self.postgres_user:
            missing.append("POSTGRES_USER")

        if not self.postgres_password:
            missing.append(
                "POSTGRES_PASSWORD"
            )

        if missing:
            raise RuntimeError(
                "PostgreSQL configuration is "
                "required for this operation. "
                "Missing: "
                + ", ".join(missing)
            )

        return (
            f"host={self.postgres_host} "
            f"port={self.postgres_port} "
            f"dbname={self.postgres_db} "
            f"user={self.postgres_user} "
            f"password={self.postgres_password}"
        )