"""
SecureVault - Magic Byte / File Signature Validation Tests
==========================================================

Tests for Module 3.5: magic-byte / file-signature validation.

Covers the reusable ``validate_magic_bytes`` helper and its integration into
the upload flow, including the guarantee that rejected files leave no physical
file and no database record behind.

Security note: magic-byte validation confirms the file's leading bytes match
the declared MIME type's signature. It is NOT a full content scan and does NOT
prove the file is safe. ClamAV and content disarm (CDR) remain required.

All tests use a temporary upload directory (via ``tmp_path``) so the real
project storage directories are never written to.
"""

import io
from pathlib import Path

import pytest

from app.files.validation import validate_magic_bytes
from app.models.file import File
from app.models.user import User
from extensions import db


# ---------------------------------------------------------------------------
# Test content constants (valid magic-byte signatures)
# ---------------------------------------------------------------------------

PDF_CONTENT = b"%PDF-1.4\n"
PNG_CONTENT = b"\x89PNG\r\n\x1a\n"
JPEG_CONTENT = b"\xff\xd8\xff\xe0\x00\x10JFIF"
TEXT_CONTENT = b"hello-world"


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


def _upload(client, csrf_token, filename="report.pdf", content=PDF_CONTENT, **overrides):
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
# validate_magic_bytes (unit tests)
# ---------------------------------------------------------------------------


def test_valid_pdf_signature_accepted(app):
    """A valid PDF signature is accepted as application/pdf."""
    result = validate_magic_bytes(io.BytesIO(PDF_CONTENT), "application/pdf")
    assert result.valid is True
    assert result.error is None


def test_valid_png_signature_accepted(app):
    """A valid PNG signature is accepted as image/png."""
    result = validate_magic_bytes(io.BytesIO(PNG_CONTENT), "image/png")
    assert result.valid is True
    assert result.error is None


def test_valid_jpeg_signature_accepted(app):
    """A valid JPEG signature is accepted as image/jpeg."""
    result = validate_magic_bytes(io.BytesIO(JPEG_CONTENT), "image/jpeg")
    assert result.valid is True
    assert result.error is None


def test_valid_text_file_accepted(app):
    """A text file (no NUL bytes) is accepted as text/plain."""
    result = validate_magic_bytes(io.BytesIO(TEXT_CONTENT), "text/plain")
    assert result.valid is True
    assert result.error is None


def test_pdf_content_declared_as_png_rejected(app):
    """PDF content declared as image/png is rejected."""
    result = validate_magic_bytes(io.BytesIO(PDF_CONTENT), "image/png")
    assert result.valid is False
    assert "do not match" in result.error


def test_png_content_declared_as_pdf_rejected(app):
    """PNG content declared as application/pdf is rejected."""
    result = validate_magic_bytes(io.BytesIO(PNG_CONTENT), "application/pdf")
    assert result.valid is False
    assert "do not match" in result.error


def test_jpeg_content_declared_as_pdf_rejected(app):
    """JPEG content declared as application/pdf is rejected."""
    result = validate_magic_bytes(io.BytesIO(JPEG_CONTENT), "application/pdf")
    assert result.valid is False
    assert "do not match" in result.error


def test_random_binary_rejected_for_binary_mime(app):
    """Random binary content is rejected for binary MIME types."""
    result = validate_magic_bytes(io.BytesIO(b"\x00\x01\x02\x03\x04"), "application/pdf")
    assert result.valid is False
    assert "do not match" in result.error


def test_empty_file_rejected(app):
    """An empty file is rejected."""
    result = validate_magic_bytes(io.BytesIO(b""), "application/pdf")
    assert result.valid is False
    assert "empty" in result.error


def test_missing_mime_type_rejected(app):
    """A missing MIME type is rejected."""
    result = validate_magic_bytes(io.BytesIO(PDF_CONTENT), None)
    assert result.valid is False
    assert "MIME type is missing" in result.error


def test_unsupported_mime_type_rejected(app):
    """An unsupported MIME type is rejected."""
    result = validate_magic_bytes(io.BytesIO(PDF_CONTENT), "application/x-msdownload")
    assert result.valid is False
    assert "not supported" in result.error


def test_text_file_with_nul_byte_rejected(app):
    """A text file containing a NUL byte is rejected as text/plain."""
    result = validate_magic_bytes(io.BytesIO(b"hello\x00world"), "text/plain")
    assert result.valid is False
    assert "do not match" in result.error


# ---------------------------------------------------------------------------
# Upload-flow integration tests
# ---------------------------------------------------------------------------


def test_valid_pdf_upload_accepted(client, db_session, tmp_path, csrf_token):
    """A valid PDF upload is accepted."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    response = _upload(client, csrf_token, content=PDF_CONTENT, content_type="application/pdf")

    assert b"File uploaded successfully" in response.data
    assert File.query.count() == 1


def test_valid_png_upload_accepted(client, db_session, tmp_path, csrf_token):
    """A valid PNG upload is accepted."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    response = _upload(client, csrf_token, content=PNG_CONTENT, content_type="image/png")

    assert b"File uploaded successfully" in response.data
    assert File.query.count() == 1


def test_valid_text_upload_accepted(client, db_session, tmp_path, csrf_token):
    """A valid text upload is accepted."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    response = _upload(client, csrf_token, filename="notes.txt", content=TEXT_CONTENT, content_type="text/plain")

    assert b"File uploaded successfully" in response.data
    assert File.query.count() == 1


def test_mismatched_content_rejected(client, db_session, tmp_path, csrf_token):
    """Content that does not match the declared MIME type is rejected."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    # PDF content declared as image/png.
    response = _upload(client, csrf_token, content=PDF_CONTENT, content_type="image/png")

    assert b"File uploaded successfully" not in response.data
    assert b"do not match" in response.data
    assert File.query.count() == 0


def test_rejected_magic_creates_no_file_record(client, db_session, tmp_path, csrf_token):
    """A rejected magic-byte validation creates no File record."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    _upload(client, csrf_token, content=PDF_CONTENT, content_type="image/png")

    assert File.query.count() == 0


def test_rejected_magic_leaves_no_physical_file(client, db_session, tmp_path, csrf_token):
    """A rejected magic-byte validation leaves no physical file behind."""
    upload_dir = _set_upload_folder(client.application, tmp_path)
    # Pre-create the upload directory so we can assert it stays empty.
    upload_dir.mkdir(parents=True, exist_ok=True)
    _create_user(db_session)
    _login(client, csrf_token)

    _upload(client, csrf_token, content=PDF_CONTENT, content_type="image/png")

    assert File.query.count() == 0
    assert list(upload_dir.iterdir()) == []


def test_existing_filename_validation_still_works(client, db_session, tmp_path, csrf_token):
    """Filename validation still rejects path traversal."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    response = _upload(client, csrf_token, filename="../../secret.txt", content_type="text/plain")

    assert b"must not contain path separators" in response.data
    assert File.query.count() == 0


def test_existing_size_validation_still_works(client, db_session, tmp_path, csrf_token):
    """Size validation still rejects oversized files."""
    _set_upload_folder(client.application, tmp_path)
    client.application.config["MAX_UPLOAD_SIZE"] = 10
    _create_user(db_session)
    _login(client, csrf_token)

    response = _upload(client, csrf_token, content=b"x" * 11, content_type="text/plain")

    assert b"exceeds the maximum upload size" in response.data
    assert File.query.count() == 0


def test_existing_mime_allowlist_still_works(client, db_session, tmp_path, csrf_token):
    """MIME allowlist validation still rejects unsupported types."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    response = _upload(client, csrf_token, content_type="application/x-msdownload")

    assert b"not supported" in response.data
    assert File.query.count() == 0
