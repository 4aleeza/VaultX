"""
SecureVault - User Model
========================

SQLAlchemy ORM model representing an application user.

Passwords are hashed using the Argon2 algorithm (via ``argon2-cffi``). The
plaintext password is never stored; only the Argon2 hash is persisted in the
``password_hash`` column. The model exposes ``set_password`` and
``verify_password`` helpers for safe password handling.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from extensions import db

# A single shared Argon2 hasher instance. Argon2 is intentionally
# CPU/memory-intensive, so the hasher is reused rather than recreated per call.
_hasher = PasswordHasher()


class User(db.Model):
    """
    A registered user of the platform.

    Attributes:
        id: Primary key (UUID).
        username: Unique, indexed login name.
        email: Unique, indexed email address.
        password_hash: Argon2 hash of the user's password. Never plaintext.
        is_active: Whether the account is active (default True).
        is_admin: Whether the user has administrative privileges (default False).
        session_version: Per-user session-generation counter used to revoke
            previously issued authenticated sessions (default 0).
        created_at: UTC timestamp of creation.
        updated_at: UTC timestamp of last update.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        db.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    username: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        index=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Server-authoritative per-user session-generation counter. Each time the
    # user's authentication state is intentionally invalidated (e.g. a future
    # password change), this value is incremented. Authenticated sessions store
    # a snapshot of this value; a session whose stored version no longer
    # matches the user's current version is treated as unauthenticated. This
    # provides multi-session revocation without a server-side session store.
    session_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    # A user's uploaded files. The relationship is defined here and mirrored
    # on the File model via ``back_populates``. Deleting a user cascades to
    # their files (matching the ``ondelete="CASCADE"`` foreign key).
    files: Mapped[list["File"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    # ------------------------------------------------------------------
    # Password handling
    # ------------------------------------------------------------------
    def set_password(self, password: str) -> None:
        """
        Hash the given plaintext password and store the Argon2 hash.

        The plaintext password is never retained on the instance or in the
        database.

        Args:
            password: The plaintext password to hash.
        """
        self.password_hash = _hasher.hash(password)

    def verify_password(self, password: str) -> bool:
        """
        Verify a plaintext password against the stored Argon2 hash.

        Args:
            password: The plaintext password to check.

        Returns:
            True if the password matches the stored hash, False otherwise.
        """
        try:
            return _hasher.verify(self.password_hash, password)
        except VerifyMismatchError:
            return False

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        """Return a concise, non-sensitive representation of the user."""
        return f"<User id={self.id} username={self.username!r}>"
