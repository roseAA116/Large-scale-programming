from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.core.errors import AppError


def get_storage_client() -> Minio:
    return Minio(
        endpoint=settings.s3_endpoint,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        secure=settings.s3_secure,
    )


def ensure_bucket(client: Minio) -> None:
    try:
        if not client.bucket_exists(settings.s3_bucket):
            client.make_bucket(settings.s3_bucket)
    except S3Error as exc:
        raise AppError(
            "STORAGE_BUCKET_UNAVAILABLE",
            "对象存储 bucket 不可用",
            status_code=503,
            details={"bucket": settings.s3_bucket},
        ) from exc


def put_material_object(
    *,
    object_key: str,
    file_stream,
    file_size: int,
    content_type: str | None,
) -> str:
    client = get_storage_client()
    ensure_bucket(client)
    try:
        client.put_object(
            settings.s3_bucket,
            object_key,
            file_stream,
            file_size,
            content_type=content_type or "application/octet-stream",
        )
    except S3Error as exc:
        raise AppError(
            "MATERIAL_UPLOAD_FAILED",
            "资料上传到对象存储失败",
            status_code=502,
            details={"object_key": object_key},
        ) from exc
    return object_key


def delete_material_object(object_key: str) -> None:
    client = get_storage_client()
    ensure_bucket(client)
    try:
        client.remove_object(settings.s3_bucket, object_key)
    except S3Error as exc:
        raise AppError(
            "MATERIAL_DELETE_FAILED",
            "资料文件删除失败",
            status_code=502,
            details={"object_key": object_key},
        ) from exc


def download_material_object(*, object_key: str, destination_path: str) -> str:
    client = get_storage_client()
    ensure_bucket(client)
    response = None
    try:
        response = client.get_object(settings.s3_bucket, object_key)
        with open(destination_path, "wb") as file:
            for chunk in response.stream(32 * 1024):
                file.write(chunk)
    except S3Error as exc:
        raise AppError(
            "PARSE_FILE_NOT_FOUND",
            "Material object could not be downloaded.",
            status_code=404,
            details={"object_key": object_key},
        ) from exc
    finally:
        if response is not None:
            response.close()
            response.release_conn()
    return destination_path


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
