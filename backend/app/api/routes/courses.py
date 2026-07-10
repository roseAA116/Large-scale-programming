from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Query, Request
from sqlalchemy import or_, select

from app.api.deps import CurrentUser, DbSession
from app.core.errors import AppError
from app.core.responses import ok
from app.models import Course
from app.schemas import CourseCreate, CourseRead, CourseUpdate

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("")
async def create_course(
    payload: CourseCreate,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    course = Course(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        teacher=payload.teacher,
        semester=payload.semester,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return ok(request, _course_payload(course), status_code=201)


@router.get("")
async def list_courses(
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
    keyword: Annotated[str | None, Query(max_length=100)] = None,
):
    statement = (
        select(Course)
        .where(Course.user_id == current_user.id, Course.deleted_at.is_(None))
        .order_by(Course.updated_at.desc())
    )

    normalized_keyword = keyword.strip() if keyword else None
    if normalized_keyword:
        pattern = f"%{normalized_keyword}%"
        statement = statement.where(
            or_(
                Course.name.ilike(pattern),
                Course.description.ilike(pattern),
                Course.teacher.ilike(pattern),
                Course.semester.ilike(pattern),
            )
        )

    courses = (await db.scalars(statement)).all()
    return ok(request, [_course_payload(course) for course in courses])


@router.get("/{course_id}")
async def read_course(
    course_id: str,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    course = await _get_owned_course(course_id, current_user.id, db)
    return ok(request, _course_payload(course))


@router.patch("/{course_id}")
async def update_course(
    course_id: str,
    payload: CourseUpdate,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    course = await _get_owned_course(course_id, current_user.id, db)
    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(course, field, value)

    await db.commit()
    await db.refresh(course)
    return ok(request, _course_payload(course))


@router.delete("/{course_id}")
async def delete_course(
    course_id: str,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    course = await _get_owned_course(course_id, current_user.id, db)
    course.deleted_at = datetime.now(UTC)
    await db.commit()
    return ok(request, {"message": "Course deleted"})


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


def _course_payload(course: Course) -> dict:
    return CourseRead.model_validate(course).model_dump(mode="json")
