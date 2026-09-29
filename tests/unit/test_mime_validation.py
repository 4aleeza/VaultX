"""
SecureVault - MIME Type Validation Tests
========================================

Tests for Module 3.4: MIME type validation.

Covers the reusable ``validate_mime_type`` helper and its integration into the
upload flow, including the guarantee that rejected files leave no physical file
and no database record behind.

Security note: MIME validation is an **allowlist check only**. It does NOT
prove that the file's actual contents match the declared MIME type. Magic-byte
validation is implemented separately (Module 3.5).

All tests use a temporary upload directory (via ``tmp_path``) so the real
project storage directories are never written to.
"""

import io
from pathlib import Path

import pytest

from app.files.validation import validate_mime_type
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

    The MIME type is controlled explicitly via the 3-tuple
    ``(stream, filename, content_type)`` so tests do not rely on Werkzeug's
    filename-based guessing.
    """
    content_type = overrides.pop("content_type", None)
    if content_type is not None:
        file_part = (io.BytesIO(content), filename, content_type)
    else:
        file_part = (io.BytesIO(content), filename)
    data = {"file": file_part, "csrf_token": csrf_token}
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
# validate_mime_type
# ---------------------------------------------------------------------------


def test_application_pdf_accepted(app):
    """application/pdf is accepted."""
    result = validate_mime_type("application/pdf")
    assert result.valid is True
    assert result.error is None


def test_image_jpeg_accepted(app):
    """image/jpeg is accepted."""
    result = validate_mime_type("image/jpeg")
    assert result.valid is True
    assert result.error is None


def test_image_png_accepted(app):
    """image/png is accepted."""
    result = validate_mime_type("image/png")
    assert result.valid is True
    assert result.error is None


def test_text_plain_accepted(app):
    """text/plain is accepted."""
    result = validate_mime_type("text/plain")
    assert result.valid is True
    assert result.error is None


def test_missing_mime_type_rejected(app):
    """A missing (None) MIME type is rejected."""
    result = validate_mime_type(None)
    assert result.valid is False
    assert result.error == "The file's MIME type is missing."


def test_empty_mime_type_rejected(app):
    """An empty MIME type is rejected."""
    result = validate_mime_type("")
    assert result.valid is False
    assert result.error == "The file's MIME type is missing."


def test_whitespace_mime_type_rejected(app):
    """A whitespace-only MIME type is rejected."""
    result = validate_mime_type("   ")
    assert result.valid is False
    assert result.error == "The file's MIME type is missing."


def test_unsupported_mime_type_rejected(app):
    """A MIME type not in the allowlist is rejected."""
    result = validate_mime_type("application/x-msdownload")
    assert result.valid is False
    assert "not supported" in result.error


def test_mime_validation_is_case_consistent(app):
    """MIME validation is case-consistent (uppercase is treated as lowercase)."""
    result = validate_mime_type("Application/PDF")
    assert result.valid is True
    assert result.error is None


def test_mime_validation_trims_whitespace(app):
    """Leading/trailing whitespace around a MIME type is trimmed."""
    result = validate_mime_type("  image/png  ")
    assert result.valid is True
    assert result.error is None


# ---------------------------------------------------------------------------
# Integration into the upload flow
# ---------------------------------------------------------------------------


def test_upload_with_supported_mime_accepted(client, db_session, tmp_path, csrf_token):
    """An upload with a supported MIME type is accepted."""
    upload_dir = _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    response = _upload(client, csrf_token, content_type="application/pdf")

    assert b"File uploaded successfully" in response.data
    assert File.query.count() == 1
    file_record = File.query.one()
    assert (upload_dir / file_record.stored_filename).exists()


def test_upload_with_unsupported_mime_rejected(client, db_session, tmp_path, csrf_token):
    """An upload with an unsupported MIME type is rejected."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    response = _upload(client, csrf_token, content_type="application/x-msdownload")

    assert b"File uploaded successfully" not in response.data
    assert b"not supported" in response.data
    assert File.query.count() == 0


def test_rejected_mime_creates_no_file_record(client, db_session, tmp_path, csrf_token):
    """A rejected MIME type creates no File record."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    _upload(client, csrf_token, content_type="application/x-msdownload")

    assert File.query.count() == 0


def test_rejected_mime_leaves_no_physical_file(client, db_session, tmp_path, csrf_token):
    """A rejected MIME type leaves no physical file behind."""
    upload_dir = _set_upload_folder(client.application, tmp_path)
    # Pre-create the upload directory so we can assert it stays empty.
    upload_dir.mkdir(parents=True, exist_ok=True)
    _create_user(db_session)
    _login(client, csrf_token)

    _upload(client, csrf_token, content_type="application/x-msdownload")

    assert File.query.count() == 0
    assert list(upload_dir.iterdir()) == []


def test_accepted_mime_stored_in_file_record(client, db_session, tmp_path, csrf_token):
    """The validated MIME type is stored in File.mime_type."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    # Valid PNG magic bytes so the upload passes magic-byte validation.
    _upload(client, csrf_token, content=b"\x89PNG\r\n\x1a\n", content_type="image/png")

    file_record = File.query.one()
    assert file_record.mime_type == "image/png"
    assert file_record.status == "pending"


def test_upload_with_missing_mime_rejected(client, db_session, tmp_path, csrf_token):
    """An upload with a missing MIME type is rejected."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    # A content_type of "" makes Werkzeug leave mimetype as None.
    response = _upload(client, csrf_token, content_type="")

    assert b"File uploaded successfully" not in response.data
    assert b"MIME type is missing" in response.data
    assert File.query.count() == 0


def test_upload_with_case_variant_mime_accepted(client, db_session, tmp_path, csrf_token):
    """An upload with a case-variant MIME type is accepted (case-consistent)."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    response = _upload(client, csrf_token, content_type="Application/PDF")

    assert b"File uploaded successfully" in response.data
    file_record = File.query.one()
    # Werkzeug normalizes the multipart content-type to lowercase, so the
    # stored value is lowercase; the allowlist check is case-consistent.
    assert file_record.mime_type == "application/pdf"


def test_existing_filename_and_size_validation_still_works(
    client, db_session, tmp_path, csrf_token
):
    """Filename and size validation still reject invalid uploads."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    # Path-traversal filename is rejected before MIME validation.
    response = _upload(client, csrf_token, filename="../../secret.txt", content_type="text/plain")
    assert b"must not contain path separators" in response.data
    assert File.query.count() == 0

    # Oversized file is rejected before MIME validation.
    client.application.config["MAX_UPLOAD_SIZE"] = 10
    response = _upload(client, csrf_token, content=b"x" * 11, content_type="text/plain")
    assert b"exceeds the maximum upload size" in response.data
    assert File.query.count() == 0
