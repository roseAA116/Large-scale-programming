from minio import Minio

from app.core.config import settings


def get_storage_client() -> Minio:
    return Minio(
        endpoint=settings.s3_endpoint,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        secure=settings.s3_secure,
    )


def storage_settings_ready() -> dict:
    missing = [
        name
        for name, value in {
            "s3_endpoint": settings.s3_endpoint,
            "s3_access_key": settings.s3_access_key,
            "s3_secret_key": settings.s3_secret_key,
            "s3_bucket": settings.s3_bucket,
        }.items()
        if not value
    ]
    return {"ok": not missing, "bucket": settings.s3_bucket, "missing": missing}

