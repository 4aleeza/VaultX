"""
SecureVault - CSRF Protection Tests
===================================

Tests for Flask-WTF CSRF protection (Module A.3).

Covers the guarantee that every state-changing request (registration, login,
upload) requires a valid CSRF token. Requests with a missing or invalid token
are rejected with HTTP 400, and a rejected request must not create any
database records or physical files.

These tests exercise the real CSRFProtect behavior: CSRF is NOT disabled in
the test configuration. Valid tokens are obtained via the ``csrf_token``
fixture, which generates a token and binds it to the test client's session.
"""

import io

from app.models.file import File
from app.models.user import User
from extensions import db


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_register_with_valid_csrf_token_succeeds(client, db_session, csrf_token):
    """A registration with a valid CSRF token succeeds."""
    response = client.post(
        "/auth/register",
        data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "correct-password",
            "confirm_password": "correct-password",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
    assert User.query.filter_by(username="newuser").first() is not None


def test_register_without_csrf_token_rejected(client, db_session):
    """A registration without a CSRF token is rejected with HTTP 400."""
    response = client.post(
        "/auth/register",
        data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "correct-password",
            "confirm_password": "correct-password",
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    # No user is created.
    assert User.query.filter_by(username="newuser").first() is None


def test_register_with_invalid_csrf_token_rejected(client, db_session):
    """A registration with an invalid CSRF token is rejected with HTTP 400."""
    response = client.post(
        "/auth/register",
        data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "correct-password",
            "confirm_password": "correct-password",
            "csrf_token": "not-a-valid-token",
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    # No user is created.
    assert User.query.filter_by(username="newuser").first() is None


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def _create_user(
    db_session,
    username="alice",
    email="alice@example.com",
    password="correct-password",
):
    """Create and persist a user with the given credentials."""
    user = User(username=username, email=email)
    user.set_password(password)
    db_session.add(user)
    db_session.commit()
    return user


def test_login_with_valid_csrf_token_succeeds(client, db_session, csrf_token):
    """A login with a valid CSRF token succeeds."""
    _create_user(db_session)

    response = client.post(
        "/login",
        data={
            "username": "alice",
            "password": "correct-password",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/dashboard"


def test_login_without_csrf_token_rejected(client, db_session):
    """A login without a CSRF token is rejected with HTTP 400."""
    _create_user(db_session)

    response = client.post(
        "/login",
        data={"username": "alice", "password": "correct-password"},
        follow_redirects=False,
    )

    assert response.status_code == 400
    # The user is not authenticated.
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_login_with_invalid_csrf_token_rejected(client, db_session):
    """A login with an invalid CSRF token is rejected with HTTP 400."""
    _create_user(db_session)

    response = client.post(
        "/login",
        data={
            "username": "alice",
            "password": "correct-password",
            "csrf_token": "not-a-valid-token",
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    # The user is not authenticated.
    with client.session_transaction() as sess:
        assert "user_id" not in sess


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


def _set_upload_folder(app, tmp_path):
    """Point the app's upload folder at a temporary directory."""
    upload_dir = tmp_path / "uploads"
    app.config["UPLOAD_FOLDER"] = str(upload_dir)
    return upload_dir


def test_upload_with_valid_csrf_token_succeeds(client, db_session, tmp_path, csrf_token):
    """An upload with a valid CSRF token succeeds."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)

    # Authenticate first (with a valid CSRF token).
    client.post(
        "/login",
        data={
            "username": "alice",
            "password": "correct-password",
            "csrf_token": csrf_token,
        },
        follow_redirects=True,
    )

    response = client.post(
        "/files/upload",
        data={
            "file": (io.BytesIO(b"%PDF-1.4\n"), "report.pdf"),
            "csrf_token": csrf_token,
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert b"File uploaded successfully" in response.data
    assert File.query.count() == 1


def test_upload_without_csrf_token_rejected(client, db_session, tmp_path, csrf_token):
    """An upload without a CSRF token is rejected with HTTP 400."""
    upload_dir = _set_upload_folder(client.application, tmp_path)
    # Pre-create the upload directory so we can assert it stays empty.
    upload_dir.mkdir(parents=True, exist_ok=True)
    _create_user(db_session)

    # Authenticate first (with a valid CSRF token).
    client.post(
        "/login",
        data={
            "username": "alice",
            "password": "correct-password",
            "csrf_token": csrf_token,
        },
        follow_redirects=True,
    )

    response = client.post(
        "/files/upload",
        data={"file": (io.BytesIO(b"%PDF-1.4\n"), "report.pdf")},
        content_type="multipart/form-data",
        follow_redirects=False,
    )

    assert response.status_code == 400
    # No File record is created.
    assert File.query.count() == 0
    # No physical file is created.
    assert list(upload_dir.iterdir()) == []


def test_upload_with_invalid_csrf_token_rejected(client, db_session, tmp_path, csrf_token):
    """An upload with an invalid CSRF token is rejected with HTTP 400."""
    upload_dir = _set_upload_folder(client.application, tmp_path)
    # Pre-create the upload directory so we can assert it stays empty.
    upload_dir.mkdir(parents=True, exist_ok=True)
    _create_user(db_session)

    # Authenticate first (with a valid CSRF token).
    client.post(
        "/login",
        data={
            "username": "alice",
            "password": "correct-password",
            "csrf_token": csrf_token,
        },
        follow_redirects=True,
    )

    response = client.post(
        "/files/upload",
        data={
            "file": (io.BytesIO(b"%PDF-1.4\n"), "report.pdf"),
            "csrf_token": "not-a-valid-token",
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )

    assert response.status_code == 400
    # No File record is created.
    assert File.query.count() == 0
    # No physical file is created.
    assert list(upload_dir.iterdir()) == []
