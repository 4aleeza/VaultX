"""
SecureVault - Database Seed Script
==================================

Idempotent script that creates an admin user (and optionally a demo user) if
they do not already exist.

Credentials are read from environment variables. There are NO hardcoded
default credentials: if the required admin credentials are missing, the seed
command fails clearly with a configuration error rather than silently creating
an admin with an insecure default password.

Passwords are hashed with Argon2 via the ``User`` model. Plaintext passwords
are never printed, logged, or stored.

Run with:
    flask seed
or directly:
    python -m app.models.seed
"""

from __future__ import annotations

import os

from app import create_app
from app.models.user import User
from config import Config
from extensions import db

# ---------------------------------------------------------------------------
# Seed credentials (from environment only — no insecure defaults).
# ---------------------------------------------------------------------------
# Admin credentials are REQUIRED. If any are missing, seed fails clearly.
ADMIN_USERNAME = os.environ.get("SEED_ADMIN_USERNAME")
ADMIN_EMAIL = os.environ.get("SEED_ADMIN_EMAIL")
ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD")

# Demo credentials are OPTIONAL. If all three are provided, a demo user is
# created; otherwise the demo user is skipped. There is no hardcoded fallback.
DEMO_USERNAME = os.environ.get("SEED_DEMO_USERNAME")
DEMO_EMAIL = os.environ.get("SEED_DEMO_EMAIL")
DEMO_PASSWORD = os.environ.get("SEED_DEMO_PASSWORD")


class SeedConfigurationError(RuntimeError):
    """Raised when required seed credentials are missing or incomplete."""


def _require_admin_credentials() -> None:
    """
    Validate that all required admin seed credentials are present.

    Raises:
        SeedConfigurationError: If any required admin credential is missing.
            The message names the missing variable(s) but never includes any
            password value.
    """
    missing = [
        name
        for name, value in (
            ("SEED_ADMIN_USERNAME", ADMIN_USERNAME),
            ("SEED_ADMIN_EMAIL", ADMIN_EMAIL),
            ("SEED_ADMIN_PASSWORD", ADMIN_PASSWORD),
        )
        if not value
    ]
    if missing:
        raise SeedConfigurationError(
            "Missing required seed configuration: "
            + ", ".join(missing)
            + ". Set these environment variables before running `flask seed`."
        )


def _demo_configured() -> bool:
    """Return True only if all demo credentials are provided."""
    return bool(DEMO_USERNAME and DEMO_EMAIL and DEMO_PASSWORD)


def _create_user_if_missing(
    username: str, email: str, password: str, *, is_admin: bool
) -> bool:
    """
    Create a user if one with the given username or email does not exist.

    Args:
        username: The username to create.
        email: The email address to create.
        password: The plaintext password to hash and store.
        is_admin: Whether the user should have admin privileges.

    Returns:
        True if a new user was created, False if one already existed.
    """
    existing = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()
    if existing is not None:
        return False

    user = User(username=username, email=email, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    return True


def seed_users() -> None:
    """
    Create the admin user (and optional demo user) if they do not already exist.

    Idempotent: safe to run multiple times. Existing users are left untouched
    and their passwords are never overwritten.

    Raises:
        SeedConfigurationError: If required admin credentials are missing.
    """
    _require_admin_credentials()

    created_admin = _create_user_if_missing(
        ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD, is_admin=True
    )

    created_demo = False
    if _demo_configured():
        created_demo = _create_user_if_missing(
            DEMO_USERNAME, DEMO_EMAIL, DEMO_PASSWORD, is_admin=False
        )

    db.session.commit()

    if created_admin:
        print(f"Created admin user: {ADMIN_USERNAME}")
    else:
        print(f"Admin user already exists: {ADMIN_USERNAME}")

    if _demo_configured():
        if created_demo:
            print(f"Created demo user: {DEMO_USERNAME}")
        else:
            print(f"Demo user already exists: {DEMO_USERNAME}")


def main() -> None:
    """Entry point for running the seed script directly."""
    app = create_app(Config)
    with app.app_context():
        seed_users()


if __name__ == "__main__":
    main()
