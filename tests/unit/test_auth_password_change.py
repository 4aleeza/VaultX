"""
SecureVault - Password Change Service Tests
===========================================

Tests for the A.6.3.2 password-change business logic in
``app.auth.services.change_password``.

Covers:
    - Successful password change (hash changes, new verifies, old doesn't,
      session_version increments).
    - Rejection of an incorrect current password (no changes).
    - Rejection of blank / whitespace-only current or new passwords.
    - Rejection of a confirmation mismatch.
    - Enforcement of the configured ``PASSWORD_MIN_LENGTH``.
    - Rejection of a new password identical to the current password.
    - session_version increments exactly once on success.
    - Redis login-failure counter cleared on success, untouched on failure.
    - No password values leak into returned errors/results.
    - The stored hash remains an Argon2 hash.
"""

from app.auth.services import change_password
from app.models.user import User
from extensions import db, redis_client


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


def _failure_key(username):
    """Return the Redis key tracking failed logins for a username."""
    return f"login_failures:{username}"


def _seed_failures(username, count=3):
    """Seed the Redis login-failure counter for a username."""
    for _ in range(count):
        redis_client.incr(_failure_key(username))


# ---------------------------------------------------------------------------
# A. Successful password change
# ---------------------------------------------------------------------------


def test_successful_password_change(client, db_session):
    """A valid change updates the hash, verifies the new password, and bumps the version."""
    user = _create_user(db_session)
    old_hash = user.password_hash
    old_version = user.session_version

    result = change_password(user, "correct-password", "new-password", "new-password")

    assert result.success is True
    assert result.errors == []
    # The hash changed and the new password verifies.
    assert user.password_hash != old_hash
    assert user.verify_password("new-password") is True
    # The old password no longer verifies.
    assert user.verify_password("correct-password") is False
    # The session version was incremented to revoke prior sessions.
    assert user.session_version == old_version + 1


# ---------------------------------------------------------------------------
# B. Incorrect current password
# ---------------------------------------------------------------------------


def test_incorrect_current_password_rejected(client, db_session):
    """A wrong current password is rejected with no changes."""
    user = _create_user(db_session)
    old_hash = user.password_hash
    old_version = user.session_version

    result = change_password(user, "wrong-password", "new-password", "new-password")

    assert result.success is False
    assert "Current password is incorrect." in result.errors
    # No changes were made.
    assert user.password_hash == old_hash
    assert user.session_version == old_version
    assert user.verify_password("correct-password") is True


# ---------------------------------------------------------------------------
# C. Blank / whitespace-only inputs
# ---------------------------------------------------------------------------


def test_blank_current_password_rejected(client, db_session):
    """A blank current password is rejected with no changes."""
    user = _create_user(db_session)
    old_hash = user.password_hash
    old_version = user.session_version

    result = change_password(user, "", "new-password", "new-password")

    assert result.success is False
    assert "Current password is required." in result.errors
    assert user.password_hash == old_hash
    assert user.session_version == old_version


def test_blank_new_password_rejected(client, db_session):
    """A blank new password is rejected with no changes."""
    user = _create_user(db_session)
    old_hash = user.password_hash
    old_version = user.session_version

    result = change_password(user, "correct-password", "", "new-password")

    assert result.success is False
    assert "New password is required." in result.errors
    assert user.password_hash == old_hash
    assert user.session_version == old_version


def test_whitespace_only_new_password_rejected(client, db_session):
    """A whitespace-only new password is treated as blank and rejected."""
    user = _create_user(db_session)
    old_hash = user.password_hash
    old_version = user.session_version

    result = change_password(user, "correct-password", "   ", "   ")

    assert result.success is False
    assert "New password is required." in result.errors
    assert user.password_hash == old_hash
    assert user.session_version == old_version


# ---------------------------------------------------------------------------
# D. Confirmation mismatch
# ---------------------------------------------------------------------------


def test_confirmation_mismatch_rejected(client, db_session):
    """A new password that does not match its confirmation is rejected."""
    user = _create_user(db_session)
    old_hash = user.password_hash
    old_version = user.session_version

    result = change_password(user, "correct-password", "new-password", "different")

    assert result.success is False
    assert "Passwords do not match." in result.errors
    assert user.password_hash == old_hash
    assert user.session_version == old_version


# ---------------------------------------------------------------------------
# E. Minimum length enforcement
# ---------------------------------------------------------------------------


def test_new_password_too_short_rejected(client, db_session, app):
    """A new password shorter than PASSWORD_MIN_LENGTH is rejected."""
    user = _create_user(db_session)
    old_hash = user.password_hash
    old_version = user.session_version
    min_length = app.config["PASSWORD_MIN_LENGTH"]
    short = "a" * (min_length - 1)

    result = change_password(user, "correct-password", short, short)

    assert result.success is False
    assert (
        f"Password must be at least {min_length} characters long." in result.errors
    )
    assert user.password_hash == old_hash
    assert user.session_version == old_version


def test_new_password_exactly_min_length_accepted(client, db_session, app):
    """A new password exactly PASSWORD_MIN_LENGTH long is accepted."""
    user = _create_user(db_session)
    min_length = app.config["PASSWORD_MIN_LENGTH"]
    exact = "a" * min_length

    result = change_password(user, "correct-password", exact, exact)

    assert result.success is True
    assert user.verify_password(exact) is True


# ---------------------------------------------------------------------------
# F. Same-password rejection
# ---------------------------------------------------------------------------


def test_same_password_rejected(client, db_session):
    """A new password identical to the current password is rejected."""
    user = _create_user(db_session)
    old_hash = user.password_hash
    old_version = user.session_version

    result = change_password(user, "correct-password", "correct-password", "correct-password")

    assert result.success is False
    assert (
        "New password must be different from the current password." in result.errors
    )
    # No changes were made, including no session_version increment.
    assert user.password_hash == old_hash
    assert user.session_version == old_version


# ---------------------------------------------------------------------------
# G. session_version behavior
# ---------------------------------------------------------------------------


def test_session_version_increments_exactly_once(client, db_session):
    """A successful change increments session_version by exactly one."""
    user = _create_user(db_session)
    old_version = user.session_version

    change_password(user, "correct-password", "new-password", "new-password")

    assert user.session_version == old_version + 1


def test_failed_change_does_not_increment_session_version(client, db_session):
    """A failed change leaves session_version unchanged."""
    user = _create_user(db_session)
    old_version = user.session_version

    change_password(user, "wrong-password", "new-password", "new-password")

    assert user.session_version == old_version


# ---------------------------------------------------------------------------
# H. Redis login-failure counter behavior
# ---------------------------------------------------------------------------


def test_success_clears_failure_counter(client, db_session):
    """A successful change clears the account's Redis failure counter."""
    user = _create_user(db_session)
    _seed_failures(user.username)

    result = change_password(user, "correct-password", "new-password", "new-password")

    assert result.success is True
    assert redis_client.get(_failure_key(user.username)) is None


def test_failure_does_not_clear_failure_counter(client, db_session):
    """A failed change leaves the Redis failure counter untouched."""
    user = _create_user(db_session)
    _seed_failures(user.username)

    result = change_password(user, "wrong-password", "new-password", "new-password")

    assert result.success is False
    assert redis_client.get(_failure_key(user.username)) is not None


# ---------------------------------------------------------------------------
# I. No password leakage
# ---------------------------------------------------------------------------


def test_passwords_not_in_errors(client, db_session):
    """Password values never appear in returned errors or results."""
    user = _create_user(db_session)

    result = change_password(user, "wrong-password", "new-password", "new-password")

    assert result.success is False
    joined = " ".join(result.errors)
    assert "correct-password" not in joined
    assert "wrong-password" not in joined
    assert "new-password" not in joined


# ---------------------------------------------------------------------------
# J. Hash remains Argon2
# ---------------------------------------------------------------------------


def test_hash_remains_argon2(client, db_session):
    """The stored hash after a change is still an Argon2 hash."""
    user = _create_user(db_session)

    change_password(user, "correct-password", "new-password", "new-password")

    assert user.password_hash.startswith("$argon2")
