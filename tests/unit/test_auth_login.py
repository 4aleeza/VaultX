"""
SecureVault - Login Tests
=========================

Tests for the user login flow (route + service), covering authentication,
validation, inactive-user rejection, password security, and Redis-backed
account lockout.
"""

import time

import pytest
from flask import session
from flask_wtf.csrf import generate_csrf

from app import create_app
from app.models.user import User
from config import Config
from extensions import db


def _create_user(
    db_session,
    username="alice",
    email="alice@example.com",
    password="correct-password",
    is_active=True,
):
    """Create and persist a user with the given credentials."""
    user = User(username=username, email=email, is_active=is_active)
    user.set_password(password)
    db_session.add(user)
    db_session.commit()
    return user


def _login(client, csrf_token, follow_redirects=True, **overrides):
    """Submit a login request with sensible defaults."""
    data = {
        "username": "alice",
        "password": "correct-password",
        "csrf_token": csrf_token,
    }
    data.update(overrides)
    return client.post("/login", data=data, follow_redirects=follow_redirects)


def test_successful_login(client, db_session, csrf_token):
    """Correct credentials authenticate the user and redirect to /dashboard."""
    _create_user(db_session)

    response = _login(client, csrf_token, follow_redirects=False)

    # The /dashboard route does not exist yet, so assert the redirect target.
    assert response.status_code == 302
    assert response.headers["Location"] == "/dashboard"


def test_login_fails_with_incorrect_password(client, db_session, csrf_token):
    """An incorrect password is rejected."""
    _create_user(db_session)

    response = _login(client, csrf_token, password="wrong-password")

    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_login_fails_with_nonexistent_username(client, db_session, csrf_token):
    """A username that does not exist is rejected."""
    response = _login(client, csrf_token, username="ghost")

    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_login_fails_for_inactive_user(client, db_session, csrf_token):
    """An inactive account cannot log in."""
    _create_user(db_session, is_active=False)

    response = _login(client, csrf_token)

    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_missing_username(client, db_session, csrf_token):
    """A missing username is rejected."""
    _create_user(db_session)

    response = _login(client, csrf_token, username="")

    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_missing_password(client, db_session, csrf_token):
    """A missing password is rejected."""
    _create_user(db_session)

    response = _login(client, csrf_token, password="")

    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_generic_error_message_for_invalid_credentials(client, db_session, csrf_token):
    """The error message does not reveal whether the username exists."""
    _create_user(db_session)

    # Wrong password for an existing user.
    wrong_password = _login(client, csrf_token, password="wrong-password")
    # Nonexistent username.
    nonexistent = _login(client, csrf_token, username="ghost")

    # Both cases produce the identical generic message.
    assert b"Invalid username or password" in wrong_password.data
    assert b"Invalid username or password" in nonexistent.data
    # The message must not hint that the username exists.
    assert b"does not exist" not in wrong_password.data
    assert b"not found" not in wrong_password.data


def test_password_not_preserved_on_failure(client, db_session, csrf_token):
    """On login failure, the submitted password is not echoed back."""
    _create_user(db_session)

    response = _login(client, csrf_token, password="wrong-password")

    assert response.status_code == 200
    assert b"wrong-password" not in response.data
    assert b"correct-password" not in response.data


def test_password_not_stored_in_plaintext(client, db_session, csrf_token):
    """The stored password is an Argon2 hash, never plaintext."""
    _create_user(db_session)

    user = User.query.filter_by(username="alice").first()
    assert user is not None
    assert user.password_hash != "correct-password"
    assert "correct-password" not in user.password_hash
    assert user.password_hash.startswith("$argon2")
    # The plaintext password must verify against the stored hash.
    assert user.verify_password("correct-password") is True


def test_username_is_trimmed(client, db_session, csrf_token):
    """Leading/trailing whitespace is stripped from the username."""
    _create_user(db_session)

    response = _login(client, csrf_token, follow_redirects=False, username="  alice  ")

    assert response.status_code == 302
    assert response.headers["Location"] == "/dashboard"


# ---------------------------------------------------------------------------
# Account lockout tests (Redis-backed)
# ---------------------------------------------------------------------------
# These tests use a local config with a low failure threshold and a short
# lockout duration so the behavior can be exercised quickly. The existing
# `_fake_redis` autouse fixture in conftest.py backs the shared `redis_client`
# with an in-memory fake, so no real Redis server is required.


class LockoutTestConfig(Config):
    """Local config for lockout tests: low threshold and short TTL."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = "redis://localhost:6379/15"
    RATELIMIT_STORAGE_URI = "memory://"
    LOGIN_RATE_LIMIT = "10 per minute"
    REGISTER_RATE_LIMIT = "5 per hour"
    UPLOAD_RATE_LIMIT = "30 per minute"
    MAX_LOGIN_ATTEMPTS = 3
    LOGIN_LOCKOUT_DURATION = 1  # 1 second, short enough to test expiry


@pytest.fixture()
def lockout_app():
    """A fresh app using the local lockout config."""
    app = create_app(LockoutTestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def lockout_client(lockout_app):
    """A test client bound to the lockout app."""
    return lockout_app.test_client()


@pytest.fixture()
def lockout_csrf_token(lockout_app, lockout_client):
    """A valid CSRF token bound to the lockout client's session."""
    with lockout_app.test_request_context():
        token = generate_csrf()
        raw_token = session["csrf_token"]
    with lockout_client.session_transaction() as sess:
        sess["csrf_token"] = raw_token
    return token


def _lockout_user():
    """Create the default 'alice' user in the lockout app's database."""
    return _create_user(db.session, username="alice")


def test_failed_login_attempts_trigger_account_lockout(
    lockout_client, lockout_csrf_token
):
    """Three failed attempts lock the account (correct password then fails)."""
    _lockout_user()

    for _ in range(3):
        _login(lockout_client, lockout_csrf_token, password="wrong-password")

    # The account is now locked: even the correct password is rejected.
    response = _login(lockout_client, lockout_csrf_token, password="correct-password")
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_locked_account_rejects_correct_password(
    lockout_client, lockout_csrf_token
):
    """A locked account rejects the correct password."""
    _lockout_user()

    for _ in range(3):
        _login(lockout_client, lockout_csrf_token, password="wrong-password")

    response = _login(lockout_client, lockout_csrf_token, password="correct-password")
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_successful_login_resets_failure_counter(
    lockout_client, lockout_csrf_token
):
    """A successful login clears the failure counter; a fresh sequence starts."""
    _lockout_user()

    # Two failures (below the threshold of 3).
    for _ in range(2):
        _login(lockout_client, lockout_csrf_token, password="wrong-password")

    # Successful login clears the counter.
    response = _login(
        lockout_client,
        lockout_csrf_token,
        password="correct-password",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/dashboard"

    # A fresh sequence starts from zero: two more failures must NOT lock yet.
    for _ in range(2):
        _login(lockout_client, lockout_csrf_token, password="wrong-password")

    response = _login(
        lockout_client,
        lockout_csrf_token,
        password="correct-password",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/dashboard"


def test_lockout_expires(lockout_client, lockout_csrf_token):
    """The lockout automatically expires after the configured TTL."""
    _lockout_user()

    for _ in range(3):
        _login(lockout_client, lockout_csrf_token, password="wrong-password")

    # Locked: correct password fails.
    response = _login(lockout_client, lockout_csrf_token, password="correct-password")
    assert b"Invalid username or password" in response.data

    # Wait only as long as necessary for the short TTL to expire.
    time.sleep(1.2)

    # Correct credentials work after the lockout expires.
    response = _login(
        lockout_client,
        lockout_csrf_token,
        password="correct-password",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/dashboard"


def test_locked_account_uses_generic_error(lockout_client, lockout_csrf_token):
    """A locked account produces the same generic error as any other failure."""
    _lockout_user()

    for _ in range(3):
        _login(lockout_client, lockout_csrf_token, password="wrong-password")

    response = _login(lockout_client, lockout_csrf_token, password="correct-password")

    # Identical generic message; must not reveal lockout or account existence.
    assert b"Invalid username or password" in response.data
    assert b"locked" not in response.data.lower()
    assert b"lockout" not in response.data.lower()
    assert b"does not exist" not in response.data
    assert b"not found" not in response.data
