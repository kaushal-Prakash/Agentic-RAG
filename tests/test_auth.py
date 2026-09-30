import pytest

from app.auth.jwt import (
    create_access_token,
    hash_password,
    verify_access_token,
    verify_password,
)


def test_password_hashing():
    password = "Test@12345"

    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)


def test_wrong_password_fails():
    password = "Test@12345"
    wrong_password = "WrongPassword"

    password_hash = hash_password(password)

    assert not verify_password(wrong_password, password_hash)


def test_password_too_long_fails():
    password = "a" * 73

    with pytest.raises(ValueError):
        hash_password(password)


def test_create_and_verify_access_token():
    user_id = 123

    token = create_access_token(user_id)
    decoded_user_id = verify_access_token(token)

    assert decoded_user_id == user_id


def test_invalid_token_fails():
    token = "invalid.jwt.token"

    assert verify_access_token(token) is None