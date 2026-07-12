from fastapi import APIRouter, Request
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.errors import AppError
from app.core.responses import ok
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas import AuthToken, UserCreate, UserLogin, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register_user(payload: UserCreate, db: DbSession, request: Request):
    existing_user = await db.scalar(
        select(User).where(or_(User.email == payload.email, User.username == payload.username))
    )
    if existing_user is not None:
        raise AppError("USER_ALREADY_EXISTS", "邮箱或用户名已被使用", status_code=409)

    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        is_admin=payload.email in {email.lower() for email in settings.admin_emails},
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise AppError("USER_ALREADY_EXISTS", "邮箱或用户名已被使用", status_code=409) from exc
    await db.refresh(user)

    return ok(request, _auth_payload(user), status_code=201)


@router.post("/login")
async def login_user(payload: UserLogin, db: DbSession, request: Request):
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise AppError("INVALID_CREDENTIALS", "邮箱或密码错误", status_code=401)
    if not user.is_active:
        raise AppError("USER_DISABLED", "用户已停用", status_code=403)

    return ok(request, _auth_payload(user))


@router.post("/logout")
async def logout_user(current_user: CurrentUser, db: DbSession, request: Request):
    current_user.token_version += 1
    await db.commit()
    return ok(request, {"message": "已退出登录"})


@router.get("/me")
async def read_current_user(current_user: CurrentUser, request: Request):
    return ok(request, UserRead.model_validate(current_user).model_dump(mode="json"))


def _auth_payload(user: User) -> dict:
    token = create_access_token(subject=user.id, token_version=user.token_version)
    return AuthToken(
        access_token=token,
        user=UserRead.model_validate(user),
    ).model_dump(mode="json")
