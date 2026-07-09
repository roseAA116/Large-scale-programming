from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError("AUTH_REQUIRED", "请先登录", status_code=401)

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise AppError("INVALID_TOKEN", str(exc), status_code=401) from exc

    user_id = payload.get("sub")
    token_version = payload.get("token_version")
    if not isinstance(user_id, str) or not isinstance(token_version, int):
        raise AppError("INVALID_TOKEN", "Token 内容缺少用户信息", status_code=401)

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None or not user.is_active:
        raise AppError("INVALID_TOKEN", "用户不存在或已停用", status_code=401)
    if user.token_version != token_version:
        raise AppError("TOKEN_REVOKED", "登录状态已失效，请重新登录", status_code=401)

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def ensure_owner(resource_user_id: str, current_user: User) -> None:
    if resource_user_id != current_user.id:
        raise AppError("FORBIDDEN_RESOURCE", "无权访问其他用户的数据", status_code=403)
