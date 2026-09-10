# GridOps

GridOps is a production-style data engineering and MLOps platform for U.S. electricity demand forecasting.

## Stage 1 goal

- Configure the project locally
- Connect to the U.S. Energy Information Administration API
- Ingest hourly PJM electricity demand
- Handle retries and pagination
- Save a reproducible local raw extract

Later stages will add PostgreSQL, S3, Prefect, dbt, MLflow, FastAPI, Docker, CI/CD, monitoring, and deployment.

## Local setup

1. Create a Python 3.11+ virtual environment.
2. Install the project in editable mode:
   `pip install -e ".[dev]"`
3. Copy `.env.example` to `.env`.
4. Put your EIA API key in `.env`.
5. Run:
   `python scripts/fetch_eia.py`

Raw extracts are written to `data/raw/eia/`.
