"""
SecureVault - File Upload Tests
===============================

Tests for the basic authenticated file-upload flow, covering authentication,
file storage, metadata creation, filename security, and rollback behavior.

All tests use a temporary upload directory (via ``tmp_path``) so the real
project storage directories are never written to.
"""

import io
import os
from pathlib import Path

import pytest

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


def test_unauthenticated_upload_redirects_to_login(client, db_session, tmp_path, csrf_token):
    """An unauthenticated upload request is redirected to /login."""
    _set_upload_folder(client.application, tmp_path)

    response = client.post(
        "/files/upload",
        data={"file": (io.BytesIO(b"data"), "a.txt"), "csrf_token": csrf_token},
        content_type="multipart/form-data",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_authenticated_user_can_upload(client, db_session, tmp_path, csrf_token):
    """An authenticated user can upload a file successfully."""
    upload_dir = _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    response = _upload(client, csrf_token)

    assert response.status_code == 200
    assert b"File uploaded successfully" in response.data


def test_file_record_is_created(client, db_session, tmp_path, csrf_token):
    """A File database record is created after a successful upload."""
    _set_upload_folder(client.application, tmp_path)
    user = _create_user(db_session)
    _login(client, csrf_token)

    _upload(client, csrf_token)

    files = File.query.all()
    assert len(files) == 1
    assert files[0].original_filename == "report.pdf"
    assert files[0].status == "pending"
    assert files[0].file_hash is None


def test_file_belongs_to_authenticated_user(client, db_session, tmp_path, csrf_token):
    """The uploaded File record belongs to the authenticated user."""
    _set_upload_folder(client.application, tmp_path)
    user = _create_user(db_session)
    _login(client, csrf_token)

    _upload(client, csrf_token)

    file_record = File.query.one()
    assert file_record.owner_id == user.id
    assert file_record.owner is user


def test_original_filename_stored_as_metadata(client, db_session, tmp_path, csrf_token):
    """The original filename is preserved as database metadata."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    _upload(client, csrf_token, filename="my-document.pdf")

    file_record = File.query.one()
    assert file_record.original_filename == "my-document.pdf"


def test_physical_filename_is_not_original(client, db_session, tmp_path, csrf_token):
    """The physical filename is a generated UUID, not the original filename."""
    upload_dir = _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    _upload(client, csrf_token, filename="secret.txt", content=b"hello-world")

    file_record = File.query.one()
    # The stored filename must differ from the original.
    assert file_record.stored_filename != "secret.txt"
    # The physical file on disk uses the stored (generated) filename.
    physical = upload_dir / file_record.stored_filename
    assert physical.exists()
    assert not (upload_dir / "secret.txt").exists()


def test_physical_file_exists_in_uploads(client, db_session, tmp_path, csrf_token):
    """The physical file exists in the upload directory."""
    upload_dir = _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    _upload(client, csrf_token, filename="notes.txt", content=b"hello-world")

    file_record = File.query.one()
    physical = upload_dir / file_record.stored_filename
    assert physical.exists()
    assert physical.read_bytes() == b"hello-world"


def test_empty_filename_rejected(client, db_session, tmp_path, csrf_token):
    """An upload with an empty filename is rejected."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    response = _upload(client, csrf_token, filename="")

    # Werkzeug drops a file with an empty filename from request.files, so the
    # upload is rejected as "no file supplied". Either way, the upload must be
    # rejected and no File record created.
    assert b"File uploaded successfully" not in response.data
    assert File.query.count() == 0


def test_no_file_supplied_rejected(client, db_session, tmp_path, csrf_token):
    """An upload with no file supplied is rejected."""
    _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    response = client.post(
        "/files/upload",
        data={"csrf_token": csrf_token},
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert b"No file was supplied" in response.data
    assert File.query.count() == 0


def test_path_traversal_filename_does_not_escape(client, db_session, tmp_path, csrf_token):
    """A path-traversal filename is rejected and cannot escape the upload dir."""
    upload_dir = _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    response = _upload(client, csrf_token, filename="../../secret.txt")

    # Module 3.3 rejects path separators in the original filename.
    assert b"File uploaded successfully" not in response.data
    assert b"must not contain path separators" in response.data
    # No File record is created.
    assert File.query.count() == 0
    # Nothing was written outside the upload directory.
    assert not (tmp_path / "secret.txt").exists()
    assert not (upload_dir.parent / "secret.txt").exists()


def test_database_failure_removes_orphaned_file(client, db_session, tmp_path, monkeypatch, csrf_token):
    """A database failure rolls back and removes the physical upload file."""
    upload_dir = _set_upload_folder(client.application, tmp_path)
    _create_user(db_session)
    _login(client, csrf_token)

    # Force the commit to fail.
    def _boom():
        raise RuntimeError("simulated db failure")

    monkeypatch.setattr(db.session, "commit", _boom)

    response = _upload(client, csrf_token)

    assert b"could not be stored" in response.data
    assert File.query.count() == 0
    # No orphaned physical file remains in the upload directory.
    assert list(upload_dir.iterdir()) == []
