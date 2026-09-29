"""
SecureVault - Configuration Tests
=================================

Tests for the production-safe configuration behavior:

    - SECRET_KEY is loaded from the environment and has no insecure fallback.
    - A missing SECRET_KEY fails clearly instead of silently using a default.
    - DEBUG defaults to False and is parsed strictly from the DEBUG variable.
    - Session cookie flags: HTTPONLY stays True, SAMESITE stays Lax, and
      SECURE defaults to True but can be disabled for local HTTP development.

Because the Config class reads environment variables at class-definition time,
these tests reload the ``config`` module with a controlled environment. An
autouse fixture restores a valid environment and reloads the module after each
test so the module is left in a usable state for the rest of the suite.
"""

import importlib
import os

import pytest

import config as config_module
from config import Config


@pytest.fixture(autouse=True)
def _restore_config_module():
    """Restore a valid config module after each test."""
    yield
    os.environ["SECRET_KEY"] = "test-secret-key-for-tests"
    importlib.reload(config_module)


def test_secret_key_loaded_from_environment(monkeypatch):
    """SECRET_KEY is read from the environment."""
    monkeypatch.setenv("SECRET_KEY", "env-secret-key")
    reloaded = importlib.reload(config_module)
    assert reloaded.Config.SECRET_KEY == "env-secret-key"


def test_missing_secret_key_raises(monkeypatch):
    """A missing SECRET_KEY fails clearly instead of using an insecure default."""
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        importlib.reload(config_module)


def test_debug_defaults_to_false(monkeypatch):
    """DEBUG defaults to False when the DEBUG variable is unset."""
    monkeypatch.delenv("DEBUG", raising=False)
    reloaded = importlib.reload(config_module)
    assert reloaded.Config.DEBUG is False


def test_debug_true_enables_debug(monkeypatch):
    """DEBUG=true enables debug mode."""
    monkeypatch.setenv("DEBUG", "true")
    reloaded = importlib.reload(config_module)
    assert reloaded.Config.DEBUG is True


def test_debug_false_disables_debug(monkeypatch):
    """DEBUG=false disables debug mode."""
    monkeypatch.setenv("DEBUG", "false")
    reloaded = importlib.reload(config_module)
    assert reloaded.Config.DEBUG is False


def test_session_cookie_httponly_remains_true():
    """SESSION_COOKIE_HTTPONLY stays True."""
    assert Config.SESSION_COOKIE_HTTPONLY is True


def test_session_cookie_samesite_remains_lax():
    """SESSION_COOKIE_SAMESITE stays Lax."""
    assert Config.SESSION_COOKIE_SAMESITE == "Lax"


def test_session_cookie_secure_defaults_to_true(monkeypatch):
    """SESSION_COOKIE_SECURE defaults to True."""
    monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)
    reloaded = importlib.reload(config_module)
    assert reloaded.Config.SESSION_COOKIE_SECURE is True


def test_session_cookie_secure_can_be_disabled(monkeypatch):
    """SESSION_COOKIE_SECURE=false disables the Secure flag for local HTTP."""
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")
    reloaded = importlib.reload(config_module)
    assert reloaded.Config.SESSION_COOKIE_SECURE is False
