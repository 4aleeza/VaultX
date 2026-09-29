"""
SecureVault - Seed Script Tests
===============================

Tests for the production-safe seed behavior:

    - Admin credentials are loaded from environment variables.
    - Missing admin credentials fail clearly (no insecure fallback).
    - The old password ``admin-dev-password`` is never used as a fallback.
    - Admin password is stored only as an Argon2 hash.
    - Running the seed twice is idempotent.
    - Password values are never included in error messages.

Because the seed module reads environment variables at module-definition time,
these tests reload the ``app.models.seed`` module with a controlled
environment. An autouse fixture restores a valid environment and reloads the
module after each test so the module is left in a usable state for the rest of
the suite.
"""

import importlib
import os

import pytest

import app.models.seed as seed_module
from app.models.user import User
from extensions import db


@pytest.fixture(autouse=True)
def _restore_seed_module():
    """Restore a valid seed module after each test."""
    yield
    os.environ["SEED_ADMIN_USERNAME"] = "admin"
    os.environ["SEED_ADMIN_EMAIL"] = "admin@vaultx.local"
    os.environ["SEED_ADMIN_PASSWORD"] = "test-admin-password"
    os.environ["SEED_DEMO_USERNAME"] = "demo"
    os.environ["SEED_DEMO_EMAIL"] = "demo@vaultx.local"
    os.environ["SEED_DEMO_PASSWORD"] = "test-demo-password"
    importlib.reload(seed_module)


def _reload_with_env(monkeypatch, env: dict[str, str]) -> None:
    """Set the given env vars (clearing seed vars not provided) and reload."""
    for key in (
        "SEED_ADMIN_USERNAME",
        "SEED_ADMIN_EMAIL",
        "SEED_ADMIN_PASSWORD",
        "SEED_DEMO_USERNAME",
        "SEED_DEMO_EMAIL",
        "SEED_DEMO_PASSWORD",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    importlib.reload(seed_module)


def test_admin_credentials_loaded_from_environment(monkeypatch):
    """Admin credentials are read from the environment."""
    _reload_with_env(
        monkeypatch,
        {
            "SEED_ADMIN_USERNAME": "root-admin",
            "SEED_ADMIN_EMAIL": "root@example.com",
            "SEED_ADMIN_PASSWORD": "root-secret-password",
        },
    )
    assert seed_module.ADMIN_USERNAME == "root-admin"
    assert seed_module.ADMIN_EMAIL == "root@example.com"
    assert seed_module.ADMIN_PASSWORD == "root-secret-password"


def test_missing_admin_password_fails_clearly(monkeypatch):
    """Missing admin password raises a clear configuration error."""
    _reload_with_env(
        monkeypatch,
        {
            "SEED_ADMIN_USERNAME": "admin",
            "SEED_ADMIN_EMAIL": "admin@vaultx.local",
            # SEED_ADMIN_PASSWORD intentionally omitted
        },
    )
    with pytest.raises(seed_module.SeedConfigurationError) as excinfo:
        seed_module.seed_users()
    assert "SEED_ADMIN_PASSWORD" in str(excinfo.value)


def test_missing_admin_username_fails_clearly(monkeypatch):
    """Missing admin username raises a clear configuration error."""
    _reload_with_env(
        monkeypatch,
        {
            "SEED_ADMIN_EMAIL": "admin@vaultx.local",
            "SEED_ADMIN_PASSWORD": "some-password",
            # SEED_ADMIN_USERNAME intentionally omitted
        },
    )
    with pytest.raises(seed_module.SeedConfigurationError) as excinfo:
        seed_module.seed_users()
    assert "SEED_ADMIN_USERNAME" in str(excinfo.value)


def test_missing_admin_credentials_do_not_create_admin(app, monkeypatch):
    """Missing admin config does not create an admin user."""
    _reload_with_env(
        monkeypatch,
        {
            "SEED_ADMIN_USERNAME": "admin",
            "SEED_ADMIN_EMAIL": "admin@vaultx.local",
            # SEED_ADMIN_PASSWORD intentionally omitted
        },
    )
    with app.app_context():
        with pytest.raises(seed_module.SeedConfigurationError):
            seed_module.seed_users()
        assert User.query.filter_by(username="admin").first() is None


def test_old_admin_dev_password_never_used_as_fallback(monkeypatch):
    """The old 'admin-dev-password' is never used as an implicit default."""
    _reload_with_env(
        monkeypatch,
        {
            "SEED_ADMIN_USERNAME": "admin",
            "SEED_ADMIN_EMAIL": "admin@vaultx.local",
            # SEED_ADMIN_PASSWORD intentionally omitted
        },
    )
    # Without a password, seed must fail rather than fall back to the old value.
    with pytest.raises(seed_module.SeedConfigurationError):
        seed_module.seed_users()
    assert seed_module.ADMIN_PASSWORD is None


def test_admin_password_stored_only_as_argon2_hash(app, monkeypatch):
    """Admin password is stored only as an Argon2 hash, never plaintext."""
    _reload_with_env(
        monkeypatch,
        {
            "SEED_ADMIN_USERNAME": "admin",
            "SEED_ADMIN_EMAIL": "admin@vaultx.local",
            "SEED_ADMIN_PASSWORD": "correct-horse-battery-staple",
        },
    )
    with app.app_context():
        seed_module.seed_users()
        admin = User.query.filter_by(username="admin").first()
        assert admin is not None
        assert admin.password_hash != "correct-horse-battery-staple"
        assert "correct-horse-battery-staple" not in admin.password_hash
        # Argon2 hashes start with the "$argon2" prefix.
        assert admin.password_hash.startswith("$argon2")


def test_seed_is_idempotent(app, monkeypatch):
    """Running seed twice does not create duplicate users."""
    _reload_with_env(
        monkeypatch,
        {
            "SEED_ADMIN_USERNAME": "admin",
            "SEED_ADMIN_EMAIL": "admin@vaultx.local",
            "SEED_ADMIN_PASSWORD": "admin-secret",
            "SEED_DEMO_USERNAME": "demo",
            "SEED_DEMO_EMAIL": "demo@vaultx.local",
            "SEED_DEMO_PASSWORD": "demo-secret",
        },
    )
    with app.app_context():
        seed_module.seed_users()
        seed_module.seed_users()
        assert User.query.filter_by(username="admin").count() == 1
        assert User.query.filter_by(username="demo").count() == 1


def test_seed_does_not_overwrite_existing_password(app, monkeypatch):
    """Existing users are not overwritten by a second seed run."""
    _reload_with_env(
        monkeypatch,
        {
            "SEED_ADMIN_USERNAME": "admin",
            "SEED_ADMIN_EMAIL": "admin@vaultx.local",
            "SEED_ADMIN_PASSWORD": "first-password",
        },
    )
    with app.app_context():
        seed_module.seed_users()
        admin = User.query.filter_by(username="admin").first()
        original_hash = admin.password_hash

        # Reload with a different password; the existing user must be untouched.
        _reload_with_env(
            monkeypatch,
            {
                "SEED_ADMIN_USERNAME": "admin",
                "SEED_ADMIN_EMAIL": "admin@vaultx.local",
                "SEED_ADMIN_PASSWORD": "second-password",
            },
        )
        seed_module.seed_users()
        admin = User.query.filter_by(username="admin").first()
        assert admin.password_hash == original_hash


def test_error_message_does_not_include_password(monkeypatch):
    """Password values are never included in error messages."""
    _reload_with_env(
        monkeypatch,
        {
            "SEED_ADMIN_USERNAME": "admin",
            "SEED_ADMIN_EMAIL": "admin@vaultx.local",
            # SEED_ADMIN_PASSWORD intentionally omitted
        },
    )
    with pytest.raises(seed_module.SeedConfigurationError) as excinfo:
        seed_module.seed_users()
    message = str(excinfo.value)
    # The message names the missing variable but never a password value.
    assert "SEED_ADMIN_PASSWORD" in message
    assert "admin-dev-password" not in message
    assert "test-admin-password" not in message


def test_demo_user_created_when_configured(app, monkeypatch):
    """A demo user is created when all demo credentials are provided."""
    _reload_with_env(
        monkeypatch,
        {
            "SEED_ADMIN_USERNAME": "admin",
            "SEED_ADMIN_EMAIL": "admin@vaultx.local",
            "SEED_ADMIN_PASSWORD": "admin-secret",
            "SEED_DEMO_USERNAME": "demo",
            "SEED_DEMO_EMAIL": "demo@vaultx.local",
            "SEED_DEMO_PASSWORD": "demo-secret",
        },
    )
    with app.app_context():
        seed_module.seed_users()
        demo = User.query.filter_by(username="demo").first()
        assert demo is not None
        assert demo.is_admin is False


def test_demo_user_skipped_when_not_configured(app, monkeypatch):
    """No demo user is created when demo credentials are absent."""
    _reload_with_env(
        monkeypatch,
        {
            "SEED_ADMIN_USERNAME": "admin",
            "SEED_ADMIN_EMAIL": "admin@vaultx.local",
            "SEED_ADMIN_PASSWORD": "admin-secret",
            # Demo credentials intentionally omitted
        },
    )
    with app.app_context():
        seed_module.seed_users()
        assert User.query.filter_by(username="demo").first() is None
