"""
SecureVault - File Model
========================

SQLAlchemy ORM model representing a stored file's metadata.

This model stores **metadata only** — the actual file contents are never
persisted in PostgreSQL. The file bytes will eventually live on disk (or
object storage) at ``storage_path`` under ``stored_filename``. The
``original_filename`` is the name supplied by the user and must never be
trusted as a filesystem path.

The ``status`` field tracks the file's lifecycle (e.g. ``pending``,
``scanning``, ``clean``, ``quarantined``, ``rejected``, ``stored``). Status
transition logic is intentionally not implemented in this module.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from extensions import db


class File(db.Model):
    """
    Metadata for a file uploaded by a user.

    Attributes:
        id: Primary key (UUID).
        owner_id: Foreign key to the owning user (indexed, required).
        original_filename: Filename supplied by the user (never a filesystem path).
        stored_filename: Internal filename used for storage.
        storage_path: Eventual storage location.
        file_size: Size of the file in bytes (must never be negative).
        mime_type: Detected/declared MIME type of the file.
        file_hash: Cryptographic hash of the file (nullable until computed).
        status: Lifecycle status (default "pending").
        created_at: UTC timestamp of creation.
        updated_at: UTC timestamp of last update.
    """

    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(
        db.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        db.Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
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
    owner: Mapped["User"] = relationship(
        back_populates="files",
    )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        # file_size must never be negative.
        db.CheckConstraint(
            "file_size >= 0",
            name="ck_files_file_size_non_negative",
        ),
    )

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        """Return a concise, non-sensitive representation of the file."""
        return (
            f"<File id={self.id} owner_id={self.owner_id} "
            f"status={self.status!r}>"
        )
