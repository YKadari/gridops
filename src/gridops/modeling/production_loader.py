from __future__ import annotations

import hashlib
import json
import tarfile
import tempfile
from pathlib import Path

import boto3
import mlflow.sklearn


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def _safe_extract(
    archive_path: Path,
    destination: Path,
) -> None:
    with tarfile.open(
        archive_path,
        "r:gz",
    ) as archive:

        destination_resolved = (
            destination.resolve()
        )

        for member in archive.getmembers():
            member_path = (
                destination / member.name
            ).resolve()

            if destination_resolved not in (
                member_path,
                *member_path.parents,
            ):
                raise RuntimeError(
                    "Unsafe path found in model archive."
                )

        archive.extractall(
            destination
        )


def load_production_model_from_s3(
    *,
    bucket: str,
    horizon_hours: int,
    profile_name: str | None = None,
    region_name: str | None = None,
):
    if horizon_hours not in (24, 48):
        raise ValueError(
            "horizon_hours must be 24 or 48."
        )

    session = boto3.Session(
        profile_name=profile_name,
        region_name=region_name,
    )

    s3 = session.client("s3")

    pointer_key = (
        "models/production/"
        f"horizon={horizon_hours}h/"
        "champion.json"
    )

    pointer_object = s3.get_object(
        Bucket=bucket,
        Key=pointer_key,
    )

    pointer = json.loads(
        pointer_object["Body"]
        .read()
        .decode("utf-8")
    )

    model_key = pointer[
        "model_s3_key"
    ]

    expected_sha256 = pointer[
        "sha256"
    ]

    temp_dir = tempfile.mkdtemp(
        prefix=f"gridops-{horizon_hours}h-"
    )

    temp_root = Path(temp_dir)

    archive_path = (
        temp_root / "model.tar.gz"
    )

    extract_root = (
        temp_root / "extracted"
    )

    extract_root.mkdir()

    s3.download_file(
        bucket,
        model_key,
        str(archive_path),
    )

    actual_sha256 = _sha256_file(
        archive_path
    )

    if actual_sha256 != expected_sha256:
        raise RuntimeError(
            "Downloaded model checksum "
            "does not match champion manifest."
        )

    _safe_extract(
        archive_path,
        extract_root,
    )

    model_path = (
        extract_root / "model"
    )

    if not model_path.exists():
        raise RuntimeError(
            "Extracted model directory "
            "was not found."
        )

    model = mlflow.sklearn.load_model(
        str(model_path)
    )

    return model, pointer