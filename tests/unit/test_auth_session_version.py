"""
SecureVault - Session Version Revocation Tests
===============================================

Tests for the A.6.3.1 session-version revocation mechanism.

Covers:
    - Login stores the user's current session_version in the session.
    - A session with a matching user_id + session_version is authenticated.
    - A session with a stale session_version is rejected.
    - A session with a missing session_version is rejected.
    - Incrementing user.session_version invalidates older authenticated
      sessions.
    - A newly created login session after the increment receives the new
      version and works normally.
    - Existing logout behavior still works.
"""

from app.auth.session import SESSION_SESSION_VERSION, SESSION_USER_ID, get_current_user
from app.models.user import User
from extensions import db


def _create_user(
    db_session,
    username="alice",
    email="alice@example.com",
    password="correct-password",
):
    """Create and persist a user with the given credentials."""
    user = User(username=username, email=email)
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


# ---------------------------------------------------------------------------
# A. Login stores the current session_version
# ---------------------------------------------------------------------------


def test_login_stores_current_session_version(client, db_session, csrf_token):
    """A successful login stores the user's current session_version."""
    user = _create_user(db_session)

    _login(client, csrf_token, follow_redirects=False)

    with client.session_transaction() as sess:
        assert sess[SESSION_USER_ID] == str(user.id)
        assert sess[SESSION_SESSION_VERSION] == user.session_version


# ---------------------------------------------------------------------------
# B. Correct user_id + matching session_version is authenticated
# ---------------------------------------------------------------------------


def test_matching_session_version_is_authenticated(client, db_session, csrf_token):
    """A session with the correct user_id and matching version is valid."""
    user = _create_user(db_session)
    _login(client, csrf_token)

    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# C. Stale session_version is rejected
# ---------------------------------------------------------------------------


def test_stale_session_version_is_rejected(client, db_session, csrf_token):
    """A session with a stale session_version is treated as unauthenticated."""
    user = _create_user(db_session)
    _login(client, csrf_token)

    # Corrupt the stored version to a stale value.
    with client.session_transaction() as sess:
        sess[SESSION_SESSION_VERSION] = user.session_version - 1

    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


# ---------------------------------------------------------------------------
# D. Missing session_version is rejected
# ---------------------------------------------------------------------------


def test_missing_session_version_is_rejected(client, db_session, csrf_token):
    """A session without a session_version is treated as unauthenticated."""
    _create_user(db_session)
    _login(client, csrf_token)

    # Remove the session_version key entirely.
    with client.session_transaction() as sess:
        del sess[SESSION_SESSION_VERSION]

    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_malformed_session_version_is_rejected(client, db_session, csrf_token):
    """A session with a non-integer session_version is treated as unauthenticated."""
    _create_user(db_session)
    _login(client, csrf_token)

    with client.session_transaction() as sess:
        sess[SESSION_SESSION_VERSION] = "not-an-integer"

    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


# ---------------------------------------------------------------------------
# E. Incrementing user.session_version invalidates older sessions
# ---------------------------------------------------------------------------


def test_incrementing_version_invalidates_existing_session(
    client, db_session, csrf_token
):
    """Incrementing user.session_version invalidates an older authenticated session."""
    user = _create_user(db_session)
    _login(client, csrf_token)

    # Confirm the session is currently valid.
    assert client.get("/dashboard", follow_redirects=False).status_code == 200

    # Increment the user's session_version (simulating an auth-state
    # invalidation such as a future password change).
    user.session_version += 1
    db_session.commit()

    # The previously issued session now carries a stale version and is
    # rejected.
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_incrementing_version_invalidates_other_clients_session(
    client, db_session, csrf_token
):
    """Incrementing the version invalidates a session held by another client."""
    user = _create_user(db_session)

    # A second client authenticates and holds a valid session.
    client2 = client.application.test_client()
    with client2.session_transaction() as sess:
        sess[SESSION_USER_ID] = str(user.id)
        sess[SESSION_SESSION_VERSION] = user.session_version

    # Both clients are authenticated.
    assert client2.get("/dashboard", follow_redirects=False).status_code == 200

    # Increment the version.
    user.session_version += 1
    db_session.commit()

    # The other client's session is now invalidated.
    response = client2.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


# ---------------------------------------------------------------------------
# F. New login after increment receives the new version and works
# ---------------------------------------------------------------------------


def test_new_login_after_increment_works(client, db_session, csrf_token):
    """A fresh login after an increment stores the new version and works."""
    user = _create_user(db_session)
    _login(client, csrf_token)

    # Increment the version, invalidating the existing session.
    user.session_version += 1
    db_session.commit()

    # The old session is now invalid.
    assert client.get("/dashboard", follow_redirects=False).status_code == 302

    # A fresh login stores the new version and works normally.
    _login(client, csrf_token, follow_redirects=False)

    with client.session_transaction() as sess:
        assert sess[SESSION_SESSION_VERSION] == user.session_version

    assert client.get("/dashboard", follow_redirects=False).status_code == 200


# ---------------------------------------------------------------------------
# G. Logout still works
# ---------------------------------------------------------------------------


def test_logout_still_works_after_session_version(client, db_session, csrf_token):
    """Logout clears the authenticated session including the version."""
    _create_user(db_session)
    _login(client, csrf_token)

    response = client.get("/logout", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    with client.session_transaction() as sess:
        assert SESSION_USER_ID not in sess
        assert SESSION_SESSION_VERSION not in sess


# ---------------------------------------------------------------------------
# get_current_user-level checks
# ---------------------------------------------------------------------------


def test_get_current_user_returns_none_for_stale_version(app, db_session):
    """get_current_user returns None when the stored version is stale."""
    user = _create_user(db_session)

    with app.test_request_context():
        from flask import session

        session[SESSION_USER_ID] = str(user.id)
        session[SESSION_SESSION_VERSION] = user.session_version
        assert get_current_user() is not None

        # Increment the version; the session is now stale.
        user.session_version += 1
        db_session.commit()
        assert get_current_user() is None


def test_get_current_user_returns_none_for_missing_version(app, db_session):
    """get_current_user returns None when the session has no version."""
    user = _create_user(db_session)

    with app.test_request_context():
        from flask import session

        session[SESSION_USER_ID] = str(user.id)
        # No session_version set.
        assert get_current_user() is None
