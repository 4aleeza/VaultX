"""
SecureVault - User Model Tests
==============================

Unit tests for the ``User`` model, covering creation, password hashing, and
uniqueness constraints.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from extensions import db


def test_user_creation(db_session):
    """A user can be created and persisted with default flags."""
    user = User(username="alice", email="alice@example.com")
    user.set_password("correct-horse-battery-staple")
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.is_active is True
    assert user.is_admin is False
    assert user.created_at is not None
    assert user.updated_at is not None


def test_password_is_hashed_not_plaintext(db_session):
    """The stored password_hash must not contain the plaintext password."""
    user = User(username="bob", email="bob@example.com")
    user.set_password("super-secret-password")
    db_session.add(user)
    db_session.commit()

    assert user.password_hash != "super-secret-password"
    assert "super-secret-password" not in user.password_hash
    # Argon2 hashes start with the "$argon2" prefix.
    assert user.password_hash.startswith("$argon2")


def test_verify_password_correct(db_session):
    """verify_password returns True for the correct password."""
    user = User(username="carol", email="carol@example.com")
    user.set_password("my-password")
    db_session.add(user)
    db_session.commit()

    assert user.verify_password("my-password") is True


def test_verify_password_incorrect(db_session):
    """verify_password returns False for an incorrect password."""
    user = User(username="dave", email="dave@example.com")
    user.set_password("right-password")
    db_session.add(user)
    db_session.commit()

    assert user.verify_password("wrong-password") is False


def test_username_uniqueness(db_session):
    """Two users cannot share the same username."""
    user1 = User(username="eve", email="eve@example.com")
    user1.set_password("password1")
    db_session.add(user1)
    db_session.commit()

    user2 = User(username="eve", email="eve2@example.com")
    user2.set_password("password2")
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_email_uniqueness(db_session):
    """Two users cannot share the same email address."""
    user1 = User(username="frank", email="frank@example.com")
    user1.set_password("password1")
    db_session.add(user1)
    db_session.commit()

    user2 = User(username="frank2", email="frank@example.com")
    user2.set_password("password2")
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        db_session.commit()


# ---------------------------------------------------------------------------
# Session-version field (A.6.3.1)
# ---------------------------------------------------------------------------


def test_new_user_session_version_defaults_to_zero(db_session):
    """A newly created user has session_version == 0."""
    user = User(username="grace", email="grace@example.com")
    user.set_password("password1")
    db_session.add(user)
    db_session.commit()

    assert user.session_version == 0


def test_session_version_is_persisted(db_session):
    """session_version is persisted to the database."""
    user = User(username="heidi", email="heidi@example.com")
    user.set_password("password1")
    db_session.add(user)
    db_session.commit()

    # Re-fetch from the database to confirm the value is persisted, not just
    # held in memory on the instance.
    db_session.expire_all()
    fetched = db_session.get(User, user.id)
    assert fetched.session_version == 0


def test_session_version_can_be_incremented_and_persisted(db_session):
    """session_version can be incremented and the new value persisted."""
    user = User(username="ivan", email="ivan@example.com")
    user.set_password("password1")
    db_session.add(user)
    db_session.commit()

    # Simulate an authentication-state invalidation (e.g. a future password
    # change) by incrementing the version.
    user.session_version += 1
    db_session.commit()

    db_session.expire_all()
    fetched = db_session.get(User, user.id)
    assert fetched.session_version == 1
