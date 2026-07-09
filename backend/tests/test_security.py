from datetime import timedelta

import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_verification_round_trip():
    hashed_password = hash_password("strong-password")

    assert hashed_password != "strong-password"
    assert verify_password("strong-password", hashed_password)
    assert not verify_password("wrong-password", hashed_password)


def test_jwt_round_trip_contains_subject_and_token_version():
    token = create_access_token(
        subject="user-1",
        token_version=3,
        expires_delta=timedelta(minutes=5),
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "user-1"
    assert payload["token_version"] == 3


def test_expired_jwt_is_rejected():
    token = create_access_token(
        subject="user-1",
        token_version=0,
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(ValueError, match="过期"):
        decode_access_token(token)
