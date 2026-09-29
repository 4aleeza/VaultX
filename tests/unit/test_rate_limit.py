"""
SecureVault - Login Rate Limiting Tests
=======================================

Focused tests for the POST /login rate limit.

These tests use a single module-scoped Flask app dedicated to this file, with
a locally-defined CSRF token fixture. Isolation between the four tests is
achieved by giving each test its own simulated client IP (RFC 5737
documentation range) rather than by resetting shared state.
"""

import pytest

from flask import session as flask_session
from flask_wtf.csrf import generate_csrf

from app import create_app
from extensions import db
from tests.conftest import TestConfig


class RateLimitTestConfig(TestConfig):
    """Test configuration with a low login rate limit for focused tests."""

    # Use in-memory storage for the rate limiter (Redis is not available
    # during unit tests). This does NOT weaken the production config.
    RATELIMIT_STORAGE_URI = "memory://"
    # A low, deterministic limit so tests can exceed it quickly.
    LOGIN_RATE_LIMIT = "3 per minute"
    # A low, deterministic registration limit so tests can exceed it quickly.
    REGISTER_RATE_LIMIT = "3 per hour"
    # A low, deterministic upload limit so tests can exceed it quickly.
    UPLOAD_RATE_LIMIT = "3 per minute"


@pytest.fixture(scope="module")
def app():
    """
    Create a single app with a low login rate limit.

    Module-scoped so the Flask-Limiter ``before_request`` handler is
    registered exactly once. The app factory wires Limiter, CSRFProtect, and
    SQLAlchemy. A single test user is inserted so login POSTs can succeed.
    """
    app = create_app(RateLimitTestConfig)

    with app.app_context():
        db.create_all()

        from app.models.user import User

        user = User(
            username="ratelimit_testuser",
            email="ratelimit_testuser@example.com",
            is_active=True,
        )
        user.set_password("RateLimit!Test123")
        db.session.add(user)
        db.session.commit()
    # App context is popped here — nothing is left pushed while tests run.

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """
    Provide a test client bound to the module-scoped app.

    Function-scoped so every test gets a fresh cookie/session jar even though
    the underlying app (and its Limiter storage) is shared for the module.
    """
    return app.test_client()


@pytest.fixture()
def get_csrf_token(app, client):
    """
    Return a callable that produces a fresh, valid CSRF token for a POST.

    Generates the token and injects the matching raw value directly into the
    client's session (mirroring conftest.py's ``csrf_token`` fixture), so the
    token validates on the following POST regardless of the GET response's
    Set-Cookie header. The ``ip`` argument is accepted for call-site
    compatibility but is not needed for session injection.
    """

    def _get(ip):
        with app.test_request_context():
            token = generate_csrf()
            raw = flask_session["csrf_token"]
        with client.session_transaction() as sess:
            sess["csrf_token"] = raw
        return token

    return _get


def _post_login(client, ip, csrf_token):
    """Submit a login POST request from the given client IP."""
    return client.post(
        "/login",
        data={
            "username": "ratelimit_testuser",
            "password": "RateLimit!Test123",
            "csrf_token": csrf_token,
        },
        environ_overrides={"REMOTE_ADDR": ip},
        follow_redirects=False,
    )


def _post_register(client, ip, csrf_token):
    """Submit a registration POST request from the given client IP."""
    return client.post(
        "/auth/register",
        data={
            "username": "new_ratelimit_user",
            "email": "new_ratelimit_user@example.com",
            "password": "RateLimit!Test123",
            "confirm_password": "RateLimit!Test123",
            "csrf_token": csrf_token,
        },
        environ_overrides={"REMOTE_ADDR": ip},
        follow_redirects=False,
    )


def _login_upload_user(client, ip, csrf_token):
    """Log in as the rate-limit test user so upload POSTs are authenticated."""
    return client.post(
        "/login",
        data={
            "username": "ratelimit_testuser",
            "password": "RateLimit!Test123",
            "csrf_token": csrf_token,
        },
        environ_overrides={"REMOTE_ADDR": ip},
        follow_redirects=False,
    )


def _post_upload(client, ip, csrf_token):
    """Submit an authenticated upload POST request from the given client IP."""
    import io

    return client.post(
        "/files/upload",
        data={
            "file": (io.BytesIO(b"%PDF-1.4\n"), "report.pdf"),
            "csrf_token": csrf_token,
        },
        content_type="multipart/form-data",
        environ_overrides={"REMOTE_ADDR": ip},
        follow_redirects=False,
    )


def test_login_rate_limit_allows_requests_under_limit(client, get_csrf_token):
    """POSTs below the configured limit are processed (not rate-limited)."""
    ip = "192.0.2.10"
    for _ in range(3):
        response = _post_login(client, ip, get_csrf_token(ip))
        assert response.status_code != 429


def test_login_rate_limit_blocks_request_over_limit(client, get_csrf_token):
    """The request exceeding the configured limit receives HTTP 429."""
    ip = "192.0.2.20"
    for _ in range(3):
        response = _post_login(client, ip, get_csrf_token(ip))
        assert response.status_code != 429

    # The 4th POST exceeds the "3 per minute" limit.
    response = _post_login(client, ip, get_csrf_token(ip))
    assert response.status_code == 429


def test_login_get_is_not_rate_limited(client, get_csrf_token):
    """GET /login does not consume the POST login rate-limit counter."""
    ip = "192.0.2.30"
    # Deliberately more than "3 per minute" GETs.
    for _ in range(5):
        response = client.get("/login", environ_overrides={"REMOTE_ADDR": ip})
        assert response.status_code != 429

    # The full POST budget is still available.
    for _ in range(3):
        response = _post_login(client, ip, get_csrf_token(ip))
        assert response.status_code != 429
    response = _post_login(client, ip, get_csrf_token(ip))
    assert response.status_code == 429


def test_login_rate_limit_is_per_client_ip(client, get_csrf_token):
    """The login rate limit is enforced per client IP address."""
    ip_a = "192.0.2.40"
    ip_b = "192.0.2.50"

    # Exhaust the limit for IP A.
    for _ in range(3):
        response = _post_login(client, ip_a, get_csrf_token(ip_a))
        assert response.status_code != 429
    response = _post_login(client, ip_a, get_csrf_token(ip_a))
    assert response.status_code == 429

    # IP B has its own independent quota and can still log in.
    response = _post_login(client, ip_b, get_csrf_token(ip_b))
    assert response.status_code != 429


def test_register_rate_limit_allows_requests_under_limit(client, get_csrf_token):
    """POSTs below the configured limit are processed (not rate-limited)."""
    ip = "192.0.2.60"
    for _ in range(3):
        response = _post_register(client, ip, get_csrf_token(ip))
        assert response.status_code != 429


def test_register_rate_limit_blocks_request_over_limit(client, get_csrf_token):
    """The request exceeding the configured limit receives HTTP 429."""
    ip = "192.0.2.70"
    for _ in range(3):
        response = _post_register(client, ip, get_csrf_token(ip))
        assert response.status_code != 429

    # The 4th POST exceeds the "3 per hour" limit.
    response = _post_register(client, ip, get_csrf_token(ip))
    assert response.status_code == 429


def test_register_get_is_not_rate_limited(client, get_csrf_token):
    """GET /auth/register does not consume the POST registration limit."""
    ip = "192.0.2.80"
    # Deliberately more than "3 per hour" GETs.
    for _ in range(5):
        response = client.get("/auth/register", environ_overrides={"REMOTE_ADDR": ip})
        assert response.status_code != 429

    # The full POST budget is still available.
    for _ in range(3):
        response = _post_register(client, ip, get_csrf_token(ip))
        assert response.status_code != 429
    response = _post_register(client, ip, get_csrf_token(ip))
    assert response.status_code == 429


def test_upload_rate_limit_allows_requests_under_limit(client, get_csrf_token):
    """Authenticated upload POSTs below the limit are processed (not 429)."""
    ip = "192.0.2.90"
    # Authenticate so the upload POSTs reach the rate-limited view.
    response = _login_upload_user(client, ip, get_csrf_token(ip))
    assert response.status_code != 429

    for _ in range(3):
        response = _post_upload(client, ip, get_csrf_token(ip))
        assert response.status_code != 429


def test_upload_rate_limit_blocks_request_over_limit(client, get_csrf_token):
    """The upload POST exceeding the configured limit receives HTTP 429."""
    ip = "192.0.2.100"
    # Authenticate so the upload POSTs reach the rate-limited view.
    response = _login_upload_user(client, ip, get_csrf_token(ip))
    assert response.status_code != 429

    for _ in range(3):
        response = _post_upload(client, ip, get_csrf_token(ip))
        assert response.status_code != 429

    # The 4th POST exceeds the "3 per minute" limit.
    response = _post_upload(client, ip, get_csrf_token(ip))
    assert response.status_code == 429


def test_upload_get_is_not_rate_limited(client, get_csrf_token):
    """GET /files/upload does not consume the POST upload rate-limit budget."""
    ip = "192.0.2.110"
    # Authenticate so the GET reaches the rate-limited view.
    response = _login_upload_user(client, ip, get_csrf_token(ip))
    assert response.status_code != 429

    # Deliberately more than "3 per minute" GETs.
    for _ in range(5):
        response = client.get("/files/upload", environ_overrides={"REMOTE_ADDR": ip})
        assert response.status_code != 429

    # The full POST budget is still available.
    for _ in range(3):
        response = _post_upload(client, ip, get_csrf_token(ip))
        assert response.status_code != 429
    response = _post_upload(client, ip, get_csrf_token(ip))
    assert response.status_code == 429
