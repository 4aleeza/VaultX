"""
SecureVault - Upload Metadata & Size Validation Tests
=====================================================

Tests for Module 3.3: upload metadata and file-size validation.

Covers the reusable validation helpers (``validate_original_filename`` and
``validate_file_size``) and their integration into the upload flow, including
the guarantee that rejected files leave no physical file and no database
record behind.

All tests use a temporary upload directory (via ``tmp_path``) so the real
project storage directories are never written to.
"""

import io
from pathlib import Path

import pytest

from app.files.validation import validate_file_size, validate_original_filename
from app.models.file import File
from app.models.user import User
from extensions import db


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


def _login(client, csrf_token, username="alice", password="correct-password"):
    """Log in as the given user."""
    return client.post(
        "/login",
        data={
            "username": username,
            "password": password,
            "csrf_token": csrf_token,
        },
        follow_redirects=True,
    )


def _upload(client, csrf_token, filename="report.pdf", content=b"%PDF-1.4\n", **overrides):
    """
    Submit a multipart upload with sensible defaults.

    The default content is a minimal valid PDF (starts with the ``%PDF`` magic
    bytes) so it passes magic-byte validation for the default ``report.pdf``
    filename. Tests that upload other types must pass matching content.
    """
    data = {"file": (io.BytesIO(content), filename), "csrf_token": csrf_token}
    data.update(overrides)
    return client.post(
        "/files/upload",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )


def _set_upload_folder(app, tmp_path):
    """Point the app's upload folder at a temporary directory."""
    upload_dir = tmp_path / "uploads"
    app.config["UPLOAD_FOLDER"] = str(upload_dir)
    return upload_dir


# ---------------------------------------------------------------------------
# validate_original_filename
# ---------------------------------------------------------------------------


def test_normal_filename_accepted(app):
    """A normal filename passes validation."""
    result = validate_original_filename("report.pdf")
    assert result.valid is True
    assert result.error is None


def test_empty_filename_rejected(app):
    """An empty filename is rejected."""
    result = validate_original_filename("")
    assert result.valid is False
    assert result.error == "The filename cannot be empty."


def test_whitespace_filename_rejected(app):
    """A whitespace-only filename is rejected."""
    result = validate_original_filename("   ")
    assert result.valid is False
    assert result.error == "The filename cannot be empty."


def test_none_filename_rejected(app):
    """A None filename is rejected."""
    result = validate_original_filename(None)
    assert result.valid is False
    assert result.error == "The filename cannot be empty."


def test_path_traversal_filename_rejected(app):
    """A Unix-style path-traversal filename is rejected."""
    result = validate_original_filename("../../secret.txt")
    assert result.valid is False
    assert result.error == "The filename must not contain path separators."


def test_windows_style_path_traversal_rejected(app):
    """A Windows-style path-traversal filename is rejected."""
    result = validate_original_filename("..\\..\\secret.txt")
    assert result.valid is False
    assert result.error == "The filename must not contain path separators."


def test_filename_exceeding_max_length_rejected(app):
    """A filename longer than MAX_FILENAME_LENGTH is rejected."""
    app.config["MAX_FILENAME_LENGTH"] = 10
    result = validate_original_filename("a" * 11)
    assert result.valid is False
    assert "too long" in result.error


def test_filename_at_max_length_accepted(app):
    """A filename exactly at MAX_FILENAME_LENGTH is accepted."""
    app.config["MAX_FILENAME_LENGTH"] = 10
    result = validate_original_filename("a" * 10)
    assert result.valid is True
    assert result.error is None


# ---------------------------------------------------------------------------
# validate_file_size
# ---------------------------------------------------------------------------


def test_zero_byte_file_rejected(app):
    """A zero-byte file is rejected."""
    result = validate_file_size(0)
    assert result.valid is False
    assert result.error == "The file is empty."


def test_none_size_rejected(app):
    """A None size is rejected."""
    result = validate_file_size(None)
    assert result.valid is False
    assert result.error == "The file is empty."


def test_negative_size_rejected(app):
    """A negative size is rejected."""
    result = validate_file_size(-1)
    assert result.valid is False
    assert result.error == "The file is empty."


def test_file_exactly_at_max_upload_size_accepted(app):
    """A file exactly at MAX_UPLOAD_SIZE is accepted."""
    app.config["MAX_UPLOAD_SIZE"] = 1024
    result = validate_file_size(1024)
    assert result.valid is True
    assert result.error is None


def test_file_larger_than_max_upload_size_rejected(app):
    """A file larger than MAX_UPLOAD_SIZE is rejected."""
    app.config["MAX_UPLOAD_SIZE"] = 1024
    result = validate_file_size(1025)
    assert result.valid is False
    assert "exceeds the maximum upload size" in result.error


# ---------------------------------------------------------------------------
# Integration into the upload flow
# ---------------------------------------------------------------------------


def test_upload_with_invalid_filename_rejected(client, db_session, tmp_path, csrf_token):
    """An upload with a path-traversal filename is rejected."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    response = _upload(client, csrf_token, filename="../../secret.txt")

    assert b"File uploaded successfully" not in response.data
    assert b"must not contain path separators" in response.data
    assert File.query.count() == 0


def test_rejected_invalid_filename_creates_no_file_record(
    client, db_session, tmp_path, csrf_token
):
    """A rejected invalid filename creates no File record."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    _upload(client, csrf_token, filename="../../secret.txt")

    assert File.query.count() == 0


def test_upload_with_oversized_file_rejected(client, db_session, tmp_path, csrf_token):
    """An upload larger than MAX_UPLOAD_SIZE is rejected."""
    _set_upload_folder(client.application, tmp_path)
    client.application.config["MAX_UPLOAD_SIZE"] = 10
    _create_user(db_session)
    _login(client, csrf_token)

    response = _upload(client, csrf_token, content=b"x" * 11)

    assert b"File uploaded successfully" not in response.data
    assert b"exceeds the maximum upload size" in response.data
    assert File.query.count() == 0


def test_rejected_oversized_file_leaves_no_physical_file(
    client, db_session, tmp_path, csrf_token
):
    """A rejected oversized file leaves no physical file behind."""
    upload_dir = _set_upload_folder(client.application, tmp_path)
    client.application.config["MAX_UPLOAD_SIZE"] = 10
    # Pre-create the upload directory so we can assert it stays empty.
    upload_dir.mkdir(parents=True, exist_ok=True)
    _create_user(db_session)
    _login(client, csrf_token)

    _upload(client, csrf_token, content=b"x" * 11)

    assert File.query.count() == 0
    assert list(upload_dir.iterdir()) == []


def test_upload_with_zero_byte_file_rejected(client, db_session, tmp_path, csrf_token):
    """A zero-byte upload is rejected."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    response = _upload(client, csrf_token, content=b"")

    assert b"File uploaded successfully" not in response.data
    assert b"The file is empty" in response.data
    assert File.query.count() == 0


def test_upload_at_max_size_accepted(client, db_session, tmp_path, csrf_token):
    """An upload exactly at MAX_UPLOAD_SIZE is accepted."""
    upload_dir = _set_upload_folder(client.application, tmp_path)
    client.application.config["MAX_UPLOAD_SIZE"] = 10
    _create_user(db_session)
    _login(client, csrf_token)

    # 10 bytes of valid PDF content (starts with the %PDF magic bytes).
    response = _upload(client, csrf_token, content=b"%PDF-1.4\n\n")

    assert b"File uploaded successfully" in response.data
    assert File.query.count() == 1
    file_record = File.query.one()
    assert file_record.file_size == 10
    assert (upload_dir / file_record.stored_filename).exists()


def test_stored_filename_independent_of_original(client, db_session, tmp_path, csrf_token):
    """The UUID-based storage filename is independent of the original filename."""
    upload_dir = _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    _upload(client, csrf_token, filename="my-document.pdf")

    file_record = File.query.one()
    assert file_record.original_filename == "my-document.pdf"
    assert file_record.stored_filename != "my-document.pdf"
    # The physical file uses the generated stored filename.
    assert (upload_dir / file_record.stored_filename).exists()
    assert not (upload_dir / "my-document.pdf").exists()


def test_file_size_recorded_from_actual_bytes(client, db_session, tmp_path, csrf_token):
    """The recorded file size reflects the actual uploaded bytes."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    _upload(client, csrf_token, filename="notes.txt", content=b"hello-world")

    file_record = File.query.one()
    assert file_record.file_size == len(b"hello-world")
