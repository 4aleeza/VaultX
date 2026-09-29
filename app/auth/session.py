"""
SecureVault - Auth Session Helpers
==================================

Reusable session management helpers for the authentication feature.

This module provides:
    - ``SESSION_USER_ID``: the session key that stores the authenticated
      user's identifier.
    - ``SESSION_SESSION_VERSION``: the session key that stores the
      authenticated user's session-generation counter snapshot.
    - ``get_current_user``: resolves the authenticated ``User`` from the
      session, or returns ``None`` when unauthenticated.
    - ``login_required``: a decorator that protects routes by requiring an
      authenticated user.
    - ``admin_required``: a decorator that protects routes by requiring an
      authenticated admin user.

Only the user's identifier and session-version snapshot are stored in the
session. Passwords, password hashes, and other sensitive data are never
stored. Authorization flags such as ``is_admin`` are read from the database,
never from the session.
"""

from __future__ import annotations

import uuid
from functools import wraps

from flask import abort, redirect, session, url_for

from app.models.user import User
from extensions import db

# The session key that holds the authenticated user's identifier. Only this
# minimal identifier is stored; no password, hash, or sensitive data.
SESSION_USER_ID = "user_id"

# The session key that holds the authenticated user's session-generation
# counter snapshot. It is compared against the user's current
# ``session_version`` on every authenticated request; a mismatch means the
# session was issued before the user's authentication state was invalidated
# and is therefore treated as unauthenticated. This enables multi-session
# revocation without a server-side session store.
SESSION_SESSION_VERSION = "session_version"


def get_current_user() -> User | None:
    """
    Resolve the currently authenticated user from the session.

    Reads the user ID from the session, looks up the corresponding ``User``,
    and returns it. Returns ``None`` when there is no authenticated session or
    when the stored user no longer exists (e.g. deleted).

    An authenticated session is valid only when the session stores both the
    user ID and a ``session_version`` that matches the user's current
    ``session_version``. If the stored version is missing, malformed, or stale
    (the user's version was incremented, e.g. by a password change), the
    session is treated as unauthenticated and ``None`` is returned. No error is
    exposed and nothing reveals whether the account exists.

    Returns:
        The authenticated ``User``, or ``None`` if unauthenticated.
    """
    user_id = session.get(SESSION_USER_ID)
    if user_id is None:
        return None

    # The session stores the user ID as a string (Flask sessions serialize to
    # JSON). Convert it back to a UUID for the database lookup. A malformed or
    # nonexistent ID is treated as unauthenticated.
    try:
        user_uuid = uuid.UUID(str(user_id))
    except (ValueError, TypeError, AttributeError):
        return None

    # Look up the user. A missing/deleted user is treated as unauthenticated.
    user = db.session.get(User, user_uuid)
    if user is None:
        return None

    # Session-version revocation check. The session must carry a
    # session_version that matches the user's current version. A missing,
    # malformed, or stale version invalidates the session. This is checked
    # AFTER the user lookup so a revoked session is indistinguishable from an
    # unauthenticated one (no account-existence leak).
    stored_version = session.get(SESSION_SESSION_VERSION)
    if stored_version is None:
        return None
    try:
        stored_version = int(stored_version)
    except (ValueError, TypeError):
        return None
    if stored_version != user.session_version:
        return None

    return user


def login_required(view):
    """
    Decorator that protects a route by requiring an authenticated user.

    If there is no authenticated session, the request is redirected to the
    login page.

    Args:
        view: The view function to protect.

    Returns:
        A wrapped view that enforces authentication.
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        if get_current_user() is None:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    """
    Decorator that protects a route by requiring an authenticated admin user.

    Unauthenticated users are redirected to the login page. Authenticated
    non-admin users receive an HTTP 403 Forbidden response. Admin status is
    read from the database (``User.is_admin``), never from the session.

    Args:
        view: The view function to protect.

    Returns:
        A wrapped view that enforces admin authorization.
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return redirect(url_for("login"))
        if not user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped
