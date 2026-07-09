import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import settings

JWT_ALGORITHM = "HS256"
PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_urlsafe(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    )
    encoded_digest = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"{PASSWORD_ALGORITHM}${PASSWORD_ITERATIONS}${salt}${encoded_digest}"


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        algorithm, iterations, salt, expected_digest = hashed_password.split("$", 3)
        if algorithm != PASSWORD_ALGORITHM:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        )
        encoded_digest = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return hmac.compare_digest(encoded_digest, expected_digest)
    except (ValueError, TypeError):
        return False


def create_access_token(
    *,
    subject: str,
    token_version: int,
    expires_delta: timedelta | None = None,
) -> str:
    expires_at = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {
        "sub": subject,
        "token_version": token_version,
        "exp": int(expires_at.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
    }
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    signing_input = ".".join(
        [
            _base64url_json(header),
            _base64url_json(payload),
        ]
    )
    signature = _sign(signing_input)
    return f"{signing_input}.{signature}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_segment, payload_segment, signature = token.split(".", 2)
    except ValueError as exc:
        raise ValueError("Token 格式无效") from exc

    signing_input = f"{header_segment}.{payload_segment}"
    if not hmac.compare_digest(signature, _sign(signing_input)):
        raise ValueError("Token 签名无效")

    header = _base64url_decode_json(header_segment)
    if header.get("alg") != JWT_ALGORITHM:
        raise ValueError("Token 算法不支持")

    payload = _base64url_decode_json(payload_segment)
    expires_at = payload.get("exp")
    if not isinstance(expires_at, int) or expires_at < int(datetime.now(UTC).timestamp()):
        raise ValueError("Token 已过期")

    return payload


def _base64url_json(value: dict[str, Any]) -> str:
    raw = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _base64url_decode_json(value: str) -> dict[str, Any]:
    padding = "=" * (-len(value) % 4)
    try:
        raw = base64.urlsafe_b64decode(f"{value}{padding}")
        decoded = json.loads(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Token 内容无效") from exc
    if not isinstance(decoded, dict):
        raise ValueError("Token 内容无效")
    return decoded


def _sign(signing_input: str) -> str:
    digest = hmac.new(
        settings.secret_key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
