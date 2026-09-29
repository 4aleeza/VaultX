"""
SecureVault - Session & Dashboard Tests
=======================================

Tests for session management, the protected dashboard, and logout, covering
authentication state, session contents, and access control.
"""

import uuid

from app.auth.session import SESSION_SESSION_VERSION, SESSION_USER_ID, get_current_user
from app.models.user import User
from extensions import db


def _create_user(
    db_session,
    username="alice",
    email="alice@example.com",
    password="correct-password",
    is_active=True,
):
    """Create and persist a user with the given credentials."""
    user = User(username=username, email=email, is_active=is_active)
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


def test_unauthenticated_dashboard_redirects_to_login(client, db_session):
    """An unauthenticated request to /dashboard redirects to /login."""
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_successful_login_creates_authenticated_session(client, db_session, csrf_token):
    """A successful login stores the user ID in the session."""
    user = _create_user(db_session)

    response = _login(client, csrf_token, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/dashboard"

    with client.session_transaction() as sess:
        assert sess[SESSION_USER_ID] == str(user.id)


def test_authenticated_user_can_access_dashboard(client, db_session, csrf_token):
    """An authenticated user can access /dashboard."""
    _create_user(db_session)
    _login(client, csrf_token)

    response = client.get("/dashboard")

    assert response.status_code == 200


def test_dashboard_displays_user_information(client, db_session, csrf_token):
    """The dashboard displays the current user's username and email."""
    _create_user(db_session, username="alice", email="alice@example.com")
    _login(client, csrf_token)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"alice" in response.data
    assert b"alice@example.com" in response.data


def test_logout_removes_authentication(client, db_session, csrf_token):
    """Logout removes the user ID from the session."""
    _create_user(db_session)
    _login(client, csrf_token)

    response = client.get("/logout", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    with client.session_transaction() as sess:
        assert SESSION_USER_ID not in sess


def test_dashboard_inaccessible_after_logout(client, db_session, csrf_token):
    """The dashboard cannot be accessed after logout."""
    _create_user(db_session)
    _login(client, csrf_token)
    client.get("/logout")

    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_session_contains_only_user_identifier(client, db_session, csrf_token):
    """The session contains only the user identifier (plus Flask's flash storage)."""
    _create_user(db_session)
    _login(client, csrf_token)

    with client.session_transaction() as sess:
        # The only meaningful data is the user ID and the session-version
        # snapshot. Flask's flash mechanism may add an internal "_flashes" key
        # for the success message; no other data (password, hash, email, user
        # object) is stored. The CSRF token is also expected in the session
        # (Flask-WTF stores the raw token there for validation); it is not
        # sensitive user data. The "_permanent" key is set by
        # session.permanent = True (A.6.1 session-expiry hardening).
        assert SESSION_USER_ID in sess
        assert SESSION_SESSION_VERSION in sess
        assert set(sess.keys()) <= {
            SESSION_USER_ID,
            SESSION_SESSION_VERSION,
            "_flashes",
            "csrf_token",
            "_permanent",
        }


def test_password_and_hash_never_stored_in_session(client, db_session, csrf_token):
    """The password and password hash are never stored in the session."""
    _create_user(db_session)
    _login(client, csrf_token)

    with client.session_transaction() as sess:
        assert "password" not in sess
        assert "password_hash" not in sess
        assert "correct-password" not in str(sess)
        assert "$argon2" not in str(sess)


def test_dashboard_does_not_display_password_or_hash(client, db_session, csrf_token):
    """The dashboard never displays the password or password hash."""
    _create_user(db_session)
    _login(client, csrf_token)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"correct-password" not in response.data
    assert b"$argon2" not in response.data


def test_invalid_user_id_in_session_is_unauthenticated(client, db_session):
    """A session with a nonexistent user ID is treated as unauthenticated."""
    _create_user(db_session)

    # Seed the session with a user ID that does not exist in the database.
    with client.session_transaction() as sess:
        sess[SESSION_USER_ID] = str(uuid.uuid4())

    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_get_current_user_returns_none_for_invalid_session(app, db_session):
    """get_current_user returns None when the session user no longer exists."""
    user = _create_user(db_session)

    with app.test_request_context():
        from flask import session

        session[SESSION_USER_ID] = str(user.id)
        session[SESSION_SESSION_VERSION] = user.session_version
        assert get_current_user() is not None

        # Simulate the user being deleted.
        db_session.delete(user)
        db_session.commit()
        assert get_current_user() is None


def test_successful_login_establishes_permanent_session(client, db_session, csrf_token):
    """A successful login marks the session as permanent (expiry enforced)."""
    _create_user(db_session)

    _login(client, csrf_token, follow_redirects=False)

    with client.session_transaction() as sess:
        assert sess.permanent is True


def test_successful_login_clears_pre_login_session_data(client, db_session, csrf_token):
    """A successful login clears arbitrary pre-login session data (fixation)."""
    _create_user(db_session)

    # Seed the session with attacker-controlled pre-login data.
    with client.session_transaction() as sess:
        sess["attacker_controlled"] = "malicious-value"

    _login(client, csrf_token, follow_redirects=False)

    with client.session_transaction() as sess:
        # The pre-login value must be gone after a successful login.
        assert "attacker_controlled" not in sess


def test_authenticated_session_contains_only_expected_user_id(
    client, db_session, csrf_token
):
    """After login, the session contains only the expected user ID."""
    user = _create_user(db_session)

    _login(client, csrf_token, follow_redirects=False)

    with client.session_transaction() as sess:
        assert sess[SESSION_USER_ID] == str(user.id)
        assert sess[SESSION_SESSION_VERSION] == user.session_version
        # Only the user ID, session-version snapshot, flash storage, CSRF
        # token, and the "_permanent" marker (set by session.permanent = True)
        # are present.
        assert set(sess.keys()) <= {
            SESSION_USER_ID,
            SESSION_SESSION_VERSION,
            "_flashes",
            "csrf_token",
            "_permanent",
        }


def test_logout_still_clears_authenticated_session(client, db_session, csrf_token):
    """Logout continues to clear the authenticated session after hardening."""
    _create_user(db_session)
    _login(client, csrf_token, follow_redirects=False)

    response = client.get("/logout", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    with client.session_transaction() as sess:
        assert SESSION_USER_ID not in sess
