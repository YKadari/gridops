from __future__ import annotations

import hashlib
import json
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import boto3
import mlflow
from mlflow import MlflowClient

from gridops.config import Settings


MODEL_NAMES = {
    24: "gridops-demand-24h",
    48: "gridops-demand-48h",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def publish_model(
    *,
    client: MlflowClient,
    s3_client,
    bucket: str,
    horizon_hours: int,
    model_name: str,
) -> None:

    model_version = (
        client.get_model_version_by_alias(
            model_name,
            "champion",
        )
    )

    version = str(model_version.version)

    print()
    print("=" * 70)
    print(
        f"Publishing {model_name} "
        f"version {version}"
    )
    print("=" * 70)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)

        download_root = (
            temp_root / "download"
        )

        download_root.mkdir()

        model_path = Path(
            mlflow.artifacts.download_artifacts(
                artifact_uri=model_version.source,
                dst_path=str(download_root),
            )
        )

        archive_path = (
            temp_root
            / f"{model_name}-v{version}.tar.gz"
        )

        with tarfile.open(
            archive_path,
            "w:gz",
        ) as archive:
            archive.add(
                model_path,
                arcname="model",
            )

        checksum = sha256_file(
            archive_path
        )

        prefix = (
            f"models/production/"
            f"horizon={horizon_hours}h/"
            f"version={version}"
        )

        model_key = (
            f"{prefix}/model.tar.gz"
        )

        manifest_key = (
            f"{prefix}/manifest.json"
        )

        manifest = {
            "model_name": model_name,
            "alias": "champion",
            "version": version,
            "horizon_hours": horizon_hours,
            "mlflow_source": model_version.source,
            "sha256": checksum,
            "published_at": (
                datetime.now(timezone.utc)
                .isoformat()
            ),
        }

        s3_client.upload_file(
            str(archive_path),
            bucket,
            model_key,
        )

        s3_client.put_object(
            Bucket=bucket,
            Key=manifest_key,
            Body=json.dumps(
                manifest,
                indent=2,
            ).encode("utf-8"),
            ContentType="application/json",
        )

        # Stable pointer used by production.
        latest_key = (
            f"models/production/"
            f"horizon={horizon_hours}h/"
            "champion.json"
        )

        champion_pointer = {
            **manifest,
            "model_s3_key": model_key,
            "manifest_s3_key": manifest_key,
        }

        s3_client.put_object(
            Bucket=bucket,
            Key=latest_key,
            Body=json.dumps(
                champion_pointer,
                indent=2,
            ).encode("utf-8"),
            ContentType="application/json",
        )

        print(
            f"Uploaded: s3://{bucket}/{model_key}"
        )
        print(
            f"Champion pointer: "
            f"s3://{bucket}/{latest_key}"
        )
        print(
            f"SHA256: {checksum}"
        )


def main() -> None:
    settings = Settings()

    mlflow.set_tracking_uri(
        "http://127.0.0.1:5000"
    )

    client = MlflowClient()

    session = boto3.Session(
        profile_name=settings.aws_profile,
        region_name=settings.aws_region,
    )

    s3_client = session.client("s3")

    for horizon_hours, model_name in (
        MODEL_NAMES.items()
    ):
        publish_model(
            client=client,
            s3_client=s3_client,
            bucket=settings.s3_raw_bucket,
            horizon_hours=horizon_hours,
            model_name=model_name,
        )

    print()
    print(
        "✅ Production champion publishing complete."
    )


if __name__ == "__main__":
    main()