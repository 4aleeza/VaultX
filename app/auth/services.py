"""
SecureVault - Auth Services
===========================

Business logic for the authentication feature.

This module implements user registration, login, and password change. Logout,
session management, and role-based access control are deferred to later
modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from flask import current_app

from app.models.user import User
from extensions import db, redis_client


@dataclass
class RegistrationResult:
    """
    Result of a registration attempt.

    Attributes:
        user: The created user, or None if validation failed.
        errors: A list of human-readable error messages (empty on success).
    """

    user: User | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """True if registration succeeded (no errors and a user was created)."""
        return self.user is not None and not self.errors


@dataclass
class PasswordChangeResult:
    """
    Result of a password-change attempt.

    Attributes:
        errors: A list of human-readable error messages (empty on success).
    """

    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """True if the password change succeeded (no errors)."""
        return not self.errors


def _is_blank(value: str | None) -> bool:
    """
    Return True if a value is None, empty, or whitespace-only.

    Args:
        value: The value to check.

    Returns:
        True if the value is blank, False otherwise.
    """
    return value is None or not value.strip()


def register_user(
    username: str | None,
    email: str | None,
    password: str | None,
    confirm_password: str | None,
) -> RegistrationResult:
    """
    Validate registration input and create a new user.

    Performs server-side validation: all fields required, no blank values,
    username/email uniqueness, and password confirmation match. On success,
    creates a ``User``, hashes the password via ``User.set_password``, and
    commits the transaction.

    Args:
        username: The desired username.
        email: The desired email address.
        password: The plaintext password.
        confirm_password: The password confirmation.

    Returns:
        A ``RegistrationResult`` containing the created user (on success) or
        a list of validation errors (on failure).
    """
    errors: list[str] = []

    # Trim leading/trailing whitespace from username and email.
    username = username.strip() if username else ""
    email = email.strip() if email else ""

    # All fields are required and must not be blank.
    if _is_blank(username):
        errors.append("Username is required.")
    if _is_blank(email):
        errors.append("Email is required.")
    if _is_blank(password):
        errors.append("Password is required.")
    if _is_blank(confirm_password):
        errors.append("Confirm password is required.")

    # Password confirmation must match.
    if password is not None and confirm_password is not None and password != confirm_password:
        errors.append("Passwords do not match.")

    # Enforce the configured minimum password length. This is the centralized
    # server-side policy check; the length is read from config so it is not
    # hardcoded here. Complexity requirements are intentionally not enforced.
    if password is not None and not _is_blank(password):
        min_length = current_app.config["PASSWORD_MIN_LENGTH"]
        if len(password) < min_length:
            errors.append(
                f"Password must be at least {min_length} characters long."
            )

    # Uniqueness checks (only if the fields are non-blank).
    if username and User.query.filter_by(username=username).first() is not None:
        errors.append("Username is already taken.")
    if email and User.query.filter_by(email=email).first() is not None:
        errors.append("Email is already registered.")

    if errors:
        return RegistrationResult(errors=errors)

    # Create and persist the user.
    user = User(username=username, email=email)
    user.set_password(password)  # type: ignore[arg-type]  # password is non-blank here
    db.session.add(user)
    db.session.commit()

    return RegistrationResult(user=user)


def _failure_key(username: str) -> str:
    """Return the Redis key tracking failed logins for a username."""
    return f"login_failures:{username}"


def _is_locked(username: str) -> bool:
    """
    Return True if the account is currently locked out.

    The lockout is represented by the failure counter reaching
    ``MAX_LOGIN_ATTEMPTS``. The counter carries a TTL of
    ``LOGIN_LOCKOUT_DURATION`` seconds, so the lockout automatically expires
    when the key does. No separate lockout key is needed.
    """
    max_attempts = current_app.config["MAX_LOGIN_ATTEMPTS"]
    failures = redis_client.get(_failure_key(username))
    if failures is None:
        return False
    return int(failures) >= max_attempts


def authenticate_user(username: str | None, password: str | None) -> User | None:
    """
    Authenticate a user by username and password.

    Finds the user by username, rejects inactive accounts, and verifies the
    supplied password using ``User.verify_password`` (Argon2). The password is
    never logged or stored in plaintext.

    Failed attempts are tracked per username in Redis. After
    ``MAX_LOGIN_ATTEMPTS`` consecutive failures the account is temporarily
    locked for ``LOGIN_LOCKOUT_DURATION`` seconds (enforced via the Redis TTL).
    A successful login clears the failure counter. Lockout state is never
    revealed to the caller: a locked account returns ``None`` exactly like any
    other authentication failure.

    Args:
        username: The submitted username.
        password: The submitted plaintext password.

    Returns:
        The authenticated ``User`` on success, or ``None`` on failure.
    """
    # Both fields are required and must not be blank.
    if _is_blank(username) or _is_blank(password):
        return None

    # Strip leading/trailing whitespace from the username. The password is
    # intentionally left unmodified before verification.
    username = username.strip()

    # Reject locked accounts before doing any work. This returns None without
    # revealing that the account is locked (identical to a generic failure).
    if _is_locked(username):
        return None

    # Find the user by username. A missing user is treated identically to a
    # wrong password so the response does not reveal whether the user exists.
    user = User.query.filter_by(username=username).first()
    if user is None:
        return None

    # Reject inactive accounts.
    if not user.is_active:
        return None

    # Verify the password using the existing Argon2 verification method.
    if not user.verify_password(password):
        # Record the failed attempt. Increment the counter and refresh its TTL
        # so the lockout window is measured from the most recent failure. When
        # the counter reaches MAX_LOGIN_ATTEMPTS the account is locked (the
        # next attempt is rejected by _is_locked above).
        key = _failure_key(username)
        failures = redis_client.incr(key)
        redis_client.expire(key, current_app.config["LOGIN_LOCKOUT_DURATION"])
        return None

    # Successful login: clear any accumulated failure state so a fresh
    # sequence of attempts starts from zero.
    redis_client.delete(_failure_key(username))

    return user


def change_password(
    user: User,
    current_password: str | None,
    new_password: str | None,
    confirm_password: str | None,
) -> PasswordChangeResult:
    """
    Change an authenticated user's password.

    Validates the supplied current password and the new password, then, on
    success, hashes the new password via ``User.set_password`` (Argon2),
    increments ``user.session_version`` to revoke all previously issued
    authenticated sessions, and clears the account's Redis login-failure
    counter. The password hash and session_version are committed atomically.

    The current password is verified with ``User.verify_password`` (Argon2);
    the plaintext password is never logged, returned, or stored. The new
    password must not be blank, must match its confirmation, must meet the
    configured ``PASSWORD_MIN_LENGTH``, and must differ from the current
    password.

    Args:
        user: The authenticated user whose password is being changed.
        current_password: The user's current plaintext password.
        new_password: The desired new plaintext password.
        confirm_password: The new password confirmation.

    Returns:
        A ``PasswordChangeResult`` with no errors on success, or a list of
        validation errors on failure. On failure the user is left unchanged
        (password_hash, session_version, and the Redis failure counter are
        untouched).
    """
    errors: list[str] = []

    # The current password is required and must not be blank.
    if _is_blank(current_password):
        errors.append("Current password is required.")

    # The new password is required and must not be blank.
    if _is_blank(new_password):
        errors.append("New password is required.")
    if _is_blank(confirm_password):
        errors.append("Confirm new password is required.")

    # New password confirmation must match.
    if (
        new_password is not None
        and confirm_password is not None
        and new_password != confirm_password
    ):
        errors.append("Passwords do not match.")

    # Enforce the configured minimum password length. This is the same
    # centralized policy used by registration; the length is read from config
    # so it is not hardcoded here.
    if new_password is not None and not _is_blank(new_password):
        min_length = current_app.config["PASSWORD_MIN_LENGTH"]
        if len(new_password) < min_length:
            errors.append(
                f"Password must be at least {min_length} characters long."
            )

    if errors:
        return PasswordChangeResult(errors=errors)

    # Verify the current password. This is done only after the basic field
    # validation above so a blank current password is reported as a validation
    # error rather than a generic authentication failure. On mismatch, reject
    # the change without modifying anything.
    if not user.verify_password(current_password):  # type: ignore[arg-type]
        errors.append("Current password is incorrect.")
        return PasswordChangeResult(errors=errors)

    # Reject a new password identical to the current password. The current
    # password is not available in plaintext, so compare via the verifier.
    if user.verify_password(new_password):  # type: ignore[arg-type]
        errors.append("New password must be different from the current password.")
        return PasswordChangeResult(errors=errors)

    # Persist the new password hash and increment the session version in the
    # same transaction. Incrementing session_version revokes all previously
    # issued authenticated sessions (A.6.3.1). The commit is atomic: if it
    # fails, neither the hash nor the version is persisted and the change is
    # not reported as successful.
    user.set_password(new_password)  # type: ignore[arg-type]  # new_password is non-blank here
    user.session_version += 1
    db.session.commit()

    # Clear the account's login-failure counter so a fresh sequence of login
    # attempts starts from zero after a successful password change. The
    # username is normalized the same way as in authenticate_user.
    redis_client.delete(_failure_key(user.username.strip()))

    return PasswordChangeResult()

