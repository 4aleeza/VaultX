"""
SecureVault - File Model Tests
==============================

Unit tests for the ``File`` model, covering creation, ownership, required
fields, constraints, and the User/File relationship.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.file import File
from app.models.user import User
from extensions import db


def _create_user(db_session, username="alice", email="alice@example.com"):
    """Create and persist a user to own files."""
    user = User(username=username, email=email)
    user.set_password("correct-horse-battery-staple")
    db_session.add(user)
    db_session.commit()
    return user


def _create_file(db_session, owner, **overrides):
    """Create and persist a File with sensible defaults."""
    data = {
        "owner": owner,
        "original_filename": "report.pdf",
        "stored_filename": "abc123-report.pdf",
        "storage_path": "/storage/encrypted/abc123",
        "file_size": 1024,
        "mime_type": "application/pdf",
    }
    data.update(overrides)
    file = File(**data)
    db_session.add(file)
    db_session.commit()
    return file


def test_file_creation(db_session):
    """A file can be created and persisted with default status."""
    user = _create_user(db_session)
    file = _create_file(db_session, user)

    assert file.id is not None
    assert file.owner_id == user.id
    assert file.original_filename == "report.pdf"
    assert file.stored_filename == "abc123-report.pdf"
    assert file.storage_path == "/storage/encrypted/abc123"
    assert file.file_size == 1024
    assert file.mime_type == "application/pdf"
    assert file.status == "pending"
    assert file.file_hash is None
    assert file.created_at is not None
    assert file.updated_at is not None


def test_file_belongs_to_user(db_session):
    """A file's owner relationship resolves to the owning user."""
    user = _create_user(db_session)
    file = _create_file(db_session, user)

    assert file.owner is user
    assert file.owner.username == "alice"


def test_user_can_access_files_through_relationship(db_session):
    """A user can access their files via user.files."""
    user = _create_user(db_session)
    file1 = _create_file(db_session, user, original_filename="a.txt")
    file2 = _create_file(db_session, user, original_filename="b.txt")

    assert len(user.files) == 2
    assert file1 in user.files
    assert file2 in user.files


def test_owner_id_required(db_session):
    """A file without an owner is rejected."""
    with pytest.raises(IntegrityError):
        _create_file(db_session, owner=None)
        db_session.commit()


def test_original_filename_required(db_session):
    """A file without an original_filename is rejected."""
    user = _create_user(db_session)
    with pytest.raises(IntegrityError):
        _create_file(db_session, user, original_filename=None)
        db_session.commit()


def test_stored_filename_required(db_session):
    """A file without a stored_filename is rejected."""
    user = _create_user(db_session)
    with pytest.raises(IntegrityError):
        _create_file(db_session, user, stored_filename=None)
        db_session.commit()


def test_storage_path_required(db_session):
    """A file without a storage_path is rejected."""
    user = _create_user(db_session)
    with pytest.raises(IntegrityError):
        _create_file(db_session, user, storage_path=None)
        db_session.commit()


def test_file_size_required(db_session):
    """A file without a file_size is rejected."""
    user = _create_user(db_session)
    with pytest.raises(IntegrityError):
        _create_file(db_session, user, file_size=None)
        db_session.commit()


def test_mime_type_required(db_session):
    """A file without a mime_type is rejected."""
    user = _create_user(db_session)
    with pytest.raises(IntegrityError):
        _create_file(db_session, user, mime_type=None)
        db_session.commit()


def test_negative_file_size_rejected(db_session):
    """A file with a negative file_size is rejected by the check constraint."""
    user = _create_user(db_session)
    with pytest.raises(IntegrityError):
        _create_file(db_session, user, file_size=-1)
        db_session.commit()


def test_default_status_is_pending(db_session):
    """A file's default status is 'pending'."""
    user = _create_user(db_session)
    file = _create_file(db_session, user)

    assert file.status == "pending"


def test_file_hash_can_be_null(db_session):
    """file_hash is nullable and defaults to None."""
    user = _create_user(db_session)
    file = _create_file(db_session, user)

    assert file.file_hash is None


def test_uuid_primary_key_generated(db_session):
    """The UUID primary key is generated automatically and is unique."""
    user = _create_user(db_session)
    file1 = _create_file(db_session, user, original_filename="a.txt")
    file2 = _create_file(db_session, user, original_filename="b.txt")

    assert isinstance(file1.id, type(file2.id))
    assert file1.id is not None
    assert file2.id is not None
    assert file1.id != file2.id
