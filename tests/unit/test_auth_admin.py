"""
SecureVault - Admin Authorization Tests
=======================================

Tests for the admin authorization decorator and the protected /admin route,
covering access control for unauthenticated, normal, and admin users.
"""

import pytest

from app.auth.session import SESSION_SESSION_VERSION, SESSION_USER_ID, admin_required
from app.models.user import User
from extensions import db


def _create_user(
    db_session,
    username="alice",
    email="alice@example.com",
    password="correct-password",
    is_active=True,
    is_admin=False,
):
    """Create and persist a user with the given credentials."""
    user = User(
        username=username,
        email=email,
        is_active=is_active,
        is_admin=is_admin,
    )
    user.set_password(password)
    db_session.add(user)
    db_session.commit()
    return user


def _login(client, csrf_token, follow_redirects=False, **overrides):
    """Submit a login request with sensible defaults."""
    data = {
        "username": "alice",
        "password": "correct-password",
        "csrf_token": csrf_token,
    }
    data.update(overrides)
    return client.post("/login", data=data, follow_redirects=follow_redirects)


def test_unauthenticated_admin_redirects_to_login(client, db_session):
    """An unauthenticated request to /admin redirects to /login."""
    response = client.get("/admin", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_normal_user_admin_returns_403(client, db_session, csrf_token):
    """An authenticated non-admin user receives HTTP 403 on /admin."""
    _create_user(db_session, is_admin=False)
    _login(client, csrf_token)

    response = client.get("/admin")

    assert response.status_code == 403


def test_admin_user_can_access_admin(client, db_session, csrf_token):
    """An authenticated admin user can access /admin."""
    _create_user(db_session, is_admin=True)
    _login(client, csrf_token)

    response = client.get("/admin")

    assert response.status_code == 200


def test_admin_dashboard_displays_admin_username(client, db_session, csrf_token):
    """The admin dashboard displays the current admin user's username."""
    _create_user(db_session, username="root", is_admin=True)
    _login(client, csrf_token, username="root")

    response = client.get("/admin")

    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data
    assert b"root" in response.data


def test_admin_required_does_not_grant_access_to_normal_user(app, db_session):
    """admin_required does not grant access to a normal (non-admin) user."""
    user = _create_user(db_session, is_admin=False)

    # A protected view that returns a marker on success.
    @admin_required
    def protected_view():
        return "admin-ok"

    with app.test_request_context():
        from flask import session
        from werkzeug.exceptions import Forbidden

        # Authenticate as the normal user. The session must carry both the
        # user ID and a matching session_version snapshot to be valid.
        session[SESSION_USER_ID] = str(user.id)
        session[SESSION_SESSION_VERSION] = user.session_version

        # Calling the decorated view directly raises Forbidden (which Flask
        # converts to an HTTP 403 response when the view is routed).
        with pytest.raises(Forbidden):
            protected_view()


def test_admin_required_allows_admin_user(app, db_session):
    """admin_required allows an authenticated admin user through."""
    user = _create_user(db_session, is_admin=True)

    @admin_required
    def protected_view():
        return "admin-ok"

    with app.test_request_context():
        from flask import session

        session[SESSION_USER_ID] = str(user.id)
        session[SESSION_SESSION_VERSION] = user.session_version

        response = protected_view()

        assert response == "admin-ok"


def test_admin_required_redirects_unauthenticated(app, db_session):
    """admin_required redirects unauthenticated users to /login."""
    @admin_required
    def protected_view():
        return "admin-ok"

    with app.test_request_context():
        response = protected_view()

        assert response.status_code == 302
        assert response.headers["Location"] == "/login"


def test_admin_page_does_not_expose_sensitive_info(client, db_session, csrf_token):
    """The admin page does not expose the password or password hash."""
    _create_user(db_session, is_admin=True)
    _login(client, csrf_token)

    response = client.get("/admin")

    assert response.status_code == 200
    assert b"correct-password" not in response.data
    assert b"$argon2" not in response.data
