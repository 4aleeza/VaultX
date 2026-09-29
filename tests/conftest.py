"""
SecureVault - Test Configuration
================================

Shared fixtures and configuration for the test suite.

Fixtures provide:
    - A test Flask application instance using an in-memory SQLite database
    - A clean database per test (tables created and dropped around each test)
"""

import os

import pytest

# The base Config class requires SECRET_KEY to be set (it fails clearly if
# missing). Provide a deterministic test-only value so the test suite does not
# depend on the developer's environment. This is NOT a production secret.
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests")

import fakeredis
import redis as redis_module

from flask import session
from flask_wtf.csrf import generate_csrf

from app import create_app
from config import Config
from extensions import db


class TestConfig(Config):
    """Test configuration using an in-memory SQLite database."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Disable Redis/Celery connections during tests.
    REDIS_URL = "redis://localhost:6379/15"
    # Use in-memory storage for the rate limiter. Redis is not available during
    # unit tests, and RATELIMIT_STORAGE_URI is evaluated at class-definition
    # time in Config (so it would otherwise keep the production "redis://redis"
    # hostname and fail to connect). This does NOT weaken the production config.
    RATELIMIT_STORAGE_URI = "memory://"
    # Realistic rate limits. Each test gets a fresh app (function-scoped
    # fixture) with its own Limiter and its own in-memory storage, so a low
    # limit is not exhausted across tests. The full suite passes with these
    # values, so the earlier very-high limits are no longer needed. Focused
    # rate-limit tests override LOGIN_RATE_LIMIT (see test_rate_limit.py).
    LOGIN_RATE_LIMIT = "10 per minute"
    REGISTER_RATE_LIMIT = "5 per hour"
    UPLOAD_RATE_LIMIT = "30 per minute"
    # NOTE: CSRF protection is intentionally left ENABLED during tests. Tests
    # must supply valid CSRF tokens (via the `csrf_token` fixture) rather than
    # disabling protection, so the real-world behavior is exercised.


@pytest.fixture(scope="module", autouse=True)
def _fake_redis():
    """
    Back the existing ``redis_client`` with an in-memory fake during tests.

    Module-scoped so the monkeypatch is active BEFORE module-scoped ``app``
    fixtures (e.g. test_rate_limit.py) call ``create_app()``. The application
    factory calls ``redis_client.init_app(app)`` (see extensions.py), which in
    turn calls ``redis.StrictRedis.from_url(...)`` to build the real client.
    No Redis server is available during unit tests, so this fixture
    monkeypatches ``from_url`` to return a fakeredis client bound to a
    ``FakeServer``. This makes the EXISTING ``redis_client`` usable in tests
    without creating a second client and without touching extensions.py or any
    production code.

    The patch is applied once per module. ``pytest.MonkeyPatch.context()`` is
    used instead of the function-scoped ``monkeypatch`` fixture because a
    module-scoped fixture cannot depend on a function-scoped fixture. A
    mutable ``holder`` dict lets the per-test ``_reset_fake_redis`` fixture
    swap in a fresh ``FakeServer`` so Redis state never leaks between tests.
    No FLUSHDB/FLUSHALL is used. Outside tests the patch is never applied, so
    production ``redis_client`` behavior is unchanged.
    """
    holder = {"server": fakeredis.FakeServer()}

    def _fake_from_url(url, *args, **kwargs):
        # Ignore the URL; bind the client to the current fake server.
        return fakeredis.FakeStrictRedis(server=holder["server"], *args, **kwargs)

    # FlaskRedis uses redis.StrictRedis as its provider class. Patch both
    # StrictRedis and Redis so any provider variant is covered.
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(redis_module.StrictRedis, "from_url", _fake_from_url)
        mp.setattr(redis_module.Redis, "from_url", _fake_from_url)

        yield holder

        # Drop the fake server so its state is fully released after the module.
        holder["server"].connected = False


@pytest.fixture(autouse=True)
def _reset_fake_redis(_fake_redis):
    """
    Give each test a fresh fake Redis server.

    The module-scoped ``_fake_redis`` patch is active for the whole module, but
    the underlying ``FakeServer`` is swapped per test so Redis state never
    leaks between tests. Function-scoped apps (which create a fresh
    ``redis_client`` per test) bind to the fresh server. No FLUSHDB/FLUSHALL
    is used.
    """
    _fake_redis["server"] = fakeredis.FakeServer()
    yield


@pytest.fixture()
def app(_fake_redis, _reset_fake_redis):
    """Create a fresh Flask application for each test."""
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Provide a test client bound to the test application."""
    return app.test_client()


@pytest.fixture()
def csrf_token(app, client):
    """
    Return a valid CSRF token bound to the test client's session.

    Flask-WTF's CSRFProtect validates the submitted (signed) token against the
    raw token stored in the session. ``generate_csrf()`` stores the raw token
    in the session and returns the signed token. This fixture captures both:
    the signed token is returned for use in POST data, and the raw token is
    persisted into the test client's session cookie so validation passes.
    """
    # generate_csrf() reads/writes the session, which requires a request
    # context (not just an app context).
    with app.test_request_context():
        token = generate_csrf()
        raw_token = session["csrf_token"]
    # Persist the raw token to the client's session cookie.
    with client.session_transaction() as sess:
        sess["csrf_token"] = raw_token
    return token


@pytest.fixture()
def db_session(app):
    """Provide a database session scoped to the test application context."""
    return db.session

