from fastapi import APIRouter, Request
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, ensure_owner
from app.core.errors import AppError
from app.core.responses import ok
from app.models import User
from app.schemas import UserProfileUpdate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def read_profile(current_user: CurrentUser, request: Request):
    return ok(request, UserRead.model_validate(current_user).model_dump(mode="json"))


@router.patch("/me")
async def update_profile(
    payload: UserProfileUpdate,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    ensure_owner(current_user.id, current_user)

    if payload.username is not None and payload.username != current_user.username:
        existing_user = await db.scalar(select(User).where(User.username == payload.username))
        if existing_user is not None:
            raise AppError("USERNAME_ALREADY_EXISTS", "用户名已被使用", status_code=409)
        current_user.username = payload.username

    if payload.full_name is not None:
        current_user.full_name = payload.full_name or None

    await db.commit()
    await db.refresh(current_user)
    return ok(request, UserRead.model_validate(current_user).model_dump(mode="json"))
