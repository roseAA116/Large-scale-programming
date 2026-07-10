from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from sqlalchemy import or_, select
from starlette.concurrency import run_in_threadpool

from app.api.deps import CurrentUser, DbSession
from app.core.errors import AppError
from app.core.logging import get_logger
from app.core.responses import ok
from app.models import Course, Material, MaterialStatus
from app.schemas import MaterialRead
from app.services.storage import delete_material_object, put_material_object
from app.services.task_queue import enqueue_parse_material

router = APIRouter(tags=["materials"])
logger = get_logger(__name__)

MAX_MATERIAL_FILE_SIZE = 100 * 1024 * 1024
ALLOWED_MATERIAL_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".pptx": "pptx",
    ".txt": "txt",
    ".md": "md",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "text/markdown",
    "image/png",
    "image/jpeg",
    "application/octet-stream",
}


@router.post("/courses/{course_id}/materials")
async def upload_material(
    course_id: str,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form(max_length=255)] = None,
    material_type: Annotated[str | None, Form(max_length=20)] = None,
):
    await _get_owned_course(course_id, current_user.id, db)
    original_filename = _validate_filename(file.filename)
    file_size = _get_upload_size(file)
    _validate_file_size(file_size)
    inferred_type = _validate_file_type(original_filename, file.content_type)
    normalized_type = _normalize_material_type(material_type, inferred_type)
    material_id = str(uuid4())
    object_key = _build_object_key(
        user_id=current_user.id,
        course_id=course_id,
        material_id=material_id,
        original_filename=original_filename,
    )
    normalized_title = title.strip() if title and title.strip() else Path(original_filename).stem

    file.file.seek(0)
    await run_in_threadpool(
        put_material_object,
        object_key=object_key,
        file_stream=file.file,
        file_size=file_size,
        content_type=file.content_type,
    )

    material = Material(
        id=material_id,
        user_id=current_user.id,
        course_id=course_id,
        title=normalized_title,
        material_type=normalized_type,
        original_filename=original_filename,
        content_type=file.content_type,
        file_size=file_size,
        object_key=object_key,
        status=MaterialStatus.PARSING,
    )
    db.add(material)
    await db.commit()
    await db.refresh(material)
    _enqueue_parse_material(material.id)
    return ok(request, _material_payload(material), status_code=201)


@router.get("/courses/{course_id}/materials")
async def list_materials(
    course_id: str,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
    material_type: Annotated[str | None, Query(max_length=20)] = None,
    keyword: Annotated[str | None, Query(max_length=100)] = None,
):
    await _get_owned_course(course_id, current_user.id, db)
    statement = (
        select(Material)
        .where(
            Material.user_id == current_user.id,
            Material.course_id == course_id,
            Material.deleted_at.is_(None),
        )
        .order_by(Material.updated_at.desc())
    )

    normalized_type = material_type.strip().lower() if material_type else None
    if normalized_type:
        statement = statement.where(Material.material_type == normalized_type)

    normalized_keyword = keyword.strip() if keyword else None
    if normalized_keyword:
        pattern = f"%{normalized_keyword}%"
        statement = statement.where(
            or_(
                Material.title.ilike(pattern),
                Material.original_filename.ilike(pattern),
            )
        )

    materials = (await db.scalars(statement)).all()
    return ok(request, [_material_payload(material) for material in materials])


@router.get("/materials/{material_id}")
async def read_material(
    material_id: str,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    material = await _get_owned_material(material_id, current_user.id, db)
    return ok(request, _material_payload(material))


@router.delete("/materials/{material_id}")
async def delete_material(
    material_id: str,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    material = await _get_owned_material(material_id, current_user.id, db)
    await run_in_threadpool(delete_material_object, material.object_key)
    material.deleted_at = datetime.now(UTC)
    await db.commit()
    return ok(request, {"message": "Material deleted"})


async def _get_owned_course(course_id: str, user_id: str, db: DbSession) -> Course:
    course = await db.scalar(
        select(Course).where(
            Course.id == course_id,
            Course.user_id == user_id,
            Course.deleted_at.is_(None),
        )
    )
    if course is None:
        raise AppError("COURSE_NOT_FOUND", "Course not found", status_code=404)
    return course


async def _get_owned_material(material_id: str, user_id: str, db: DbSession) -> Material:
    material = await db.scalar(
        select(Material).where(
            Material.id == material_id,
            Material.user_id == user_id,
            Material.deleted_at.is_(None),
        )
    )
    if material is None:
        raise AppError("MATERIAL_NOT_FOUND", "Material not found", status_code=404)
    return material


def _validate_filename(filename: str | None) -> str:
    if filename is None:
        raise AppError("MATERIAL_FILENAME_REQUIRED", "资料文件名不能为空", status_code=400)
    normalized = Path(filename).name.strip()
    if not normalized or len(normalized) > 255:
        raise AppError(
            "MATERIAL_FILENAME_INVALID",
            "资料文件名长度必须为 1-255 字符",
            status_code=400,
        )
    return normalized


def _get_upload_size(file: UploadFile) -> int:
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    return file_size


def _validate_file_size(file_size: int) -> None:
    if file_size <= 0:
        raise AppError("MATERIAL_EMPTY_FILE", "资料文件不能为空", status_code=400)
    if file_size > MAX_MATERIAL_FILE_SIZE:
        raise AppError(
            "MATERIAL_TOO_LARGE",
            "资料文件不能超过 100MB",
            status_code=413,
            details={"max_bytes": MAX_MATERIAL_FILE_SIZE},
        )


def _validate_file_type(filename: str, content_type: str | None) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_MATERIAL_EXTENSIONS:
        raise AppError(
            "MATERIAL_UNSUPPORTED_TYPE",
            "资料文件类型不支持",
            status_code=415,
            details={"allowed_extensions": sorted(ALLOWED_MATERIAL_EXTENSIONS)},
        )
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise AppError(
            "MATERIAL_UNSUPPORTED_TYPE",
            "资料 MIME 类型不支持",
            status_code=415,
            details={"content_type": content_type},
        )
    return ALLOWED_MATERIAL_EXTENSIONS[extension]


def _normalize_material_type(material_type: str | None, inferred_type: str) -> str:
    if material_type is None or not material_type.strip():
        return inferred_type
    normalized = material_type.strip().lower()
    allowed_types = set(ALLOWED_MATERIAL_EXTENSIONS.values())
    if normalized not in allowed_types:
        raise AppError(
            "MATERIAL_UNSUPPORTED_TYPE",
            "资料类型不支持",
            status_code=415,
            details={"allowed_types": sorted(allowed_types)},
        )
    return normalized


def _build_object_key(
    *,
    user_id: str,
    course_id: str,
    material_id: str,
    original_filename: str,
) -> str:
    safe_name = original_filename.replace("\\", "_").replace("/", "_")
    return f"{user_id}/{course_id}/{material_id}/{safe_name}"


def _enqueue_parse_material(material_id: str) -> None:
    enqueue_parse_material(material_id)
    logger.info("parse_material_task_enqueued", extra={"material_id": material_id})


def _material_payload(material: Material) -> dict:
    return MaterialRead.model_validate(material).model_dump(mode="json")
