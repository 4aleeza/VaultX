"""
SecureVault - Models Package
============================

Database models (SQLAlchemy ORM).

Models are imported here so that Alembic can autogenerate migrations against
the full metadata. Importing the model modules registers their tables on the
shared ``db.metadata``.
"""

from app.models.file import File
from app.models.user import User

__all__ = ["File", "User"]

