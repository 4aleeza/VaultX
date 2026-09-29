"""
SecureVault - Registration Tests
================================

Tests for the user registration flow (route + service), covering validation,
user creation, and password hashing.
"""

from app.models.user import User
from extensions import db


def _register(client, csrf_token, follow_redirects=True, **overrides):
    """Submit a registration request with sensible defaults."""
    data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "correct-password",
        "confirm_password": "correct-password",
        "csrf_token": csrf_token,
    }
    data.update(overrides)
    return client.post(
        "/auth/register", data=data, follow_redirects=follow_redirects
    )


def test_successful_registration(client, db_session, csrf_token):
    """A valid registration creates a user and redirects to login."""
    response = _register(client, csrf_token, follow_redirects=False)

    # The /login route does not exist yet, so assert the redirect target.
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    user = User.query.filter_by(username="newuser").first()
    assert user is not None
    assert user.email == "newuser@example.com"
    assert user.is_active is True
    assert user.is_admin is False


def test_duplicate_username(client, db_session, csrf_token):
    """Registering with an existing username is rejected."""
    # Create an existing user with the same username.
    existing = User(username="newuser", email="other@example.com")
    existing.set_password("some-password")
    db_session.add(existing)
    db_session.commit()

    response = _register(client, csrf_token)

    assert response.status_code == 200
    assert b"Username is already taken" in response.data
    # No second user with that username should exist.
    assert User.query.filter_by(username="newuser").count() == 1


def test_duplicate_email(client, db_session, csrf_token):
    """Registering with an existing email is rejected."""
    # Create an existing user with the same email.
    existing = User(username="otheruser", email="newuser@example.com")
    existing.set_password("some-password")
    db_session.add(existing)
    db_session.commit()

    response = _register(client, csrf_token)

    assert response.status_code == 200
    assert b"Email is already registered" in response.data
    # No second user with that email should exist.
    assert User.query.filter_by(email="newuser@example.com").count() == 1


def test_password_mismatch(client, db_session, csrf_token):
    """Passwords that do not match are rejected."""
    response = _register(client, csrf_token, confirm_password="different-password")

    assert response.status_code == 200
    assert b"Passwords do not match" in response.data
    # No user should be created.
    assert User.query.filter_by(username="newuser").first() is None


def test_empty_required_fields(client, db_session, csrf_token):
    """Missing required fields are rejected."""
    response = client.post(
        "/auth/register",
        data={
            "username": "",
            "email": "",
            "password": "",
            "confirm_password": "",
            "csrf_token": csrf_token,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Username is required" in response.data
    assert b"Email is required" in response.data
    assert b"Password is required" in response.data
    assert b"Confirm password is required" in response.data
    assert User.query.count() == 0


def test_whitespace_only_values_rejected(client, db_session, csrf_token):
    """Whitespace-only values are treated as blank and rejected."""
    response = client.post(
        "/auth/register",
        data={
            "username": "   ",
            "email": "   ",
            "password": "   ",
            "confirm_password": "   ",
            "csrf_token": csrf_token,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Username is required" in response.data
    assert b"Email is required" in response.data
    assert User.query.count() == 0


def test_password_stored_as_hash(client, db_session, csrf_token):
    """The stored password is an Argon2 hash, never plaintext."""
    _register(client, csrf_token)

    user = User.query.filter_by(username="newuser").first()
    assert user is not None
    assert user.password_hash != "correct-password"
    assert "correct-password" not in user.password_hash
    assert user.password_hash.startswith("$argon2")
    # The plaintext password must verify against the stored hash.
    assert user.verify_password("correct-password") is True


def test_username_and_email_are_trimmed(client, db_session, csrf_token):
    """Leading/trailing whitespace is trimmed from username and email."""
    response = _register(
        client,
        csrf_token,
        follow_redirects=False,
        username="  paddeduser  ",
        email="  padded@example.com  ",
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    user = User.query.filter_by(username="paddeduser").first()
    assert user is not None
    assert user.email == "padded@example.com"


def test_passwords_not_preserved_on_failure(client, db_session, csrf_token):
    """On validation failure, the form does not echo passwords back."""
    response = _register(client, csrf_token, confirm_password="different-password")

    assert response.status_code == 200
    # The password values must not appear in the rendered form.
    assert b"correct-password" not in response.data
    assert b"different-password" not in response.data


def test_password_shorter_than_minimum_rejected(client, db_session, csrf_token):
    """A password shorter than PASSWORD_MIN_LENGTH is rejected."""
    short_password = "short"  # 5 characters, below the 12-char minimum.
    response = _register(
        client,
        csrf_token,
        password=short_password,
        confirm_password=short_password,
    )

    assert response.status_code == 200
    assert b"Password must be at least 12 characters long" in response.data
    # No user should be created.
    assert User.query.filter_by(username="newuser").first() is None


def test_password_exactly_minimum_length_accepted(client, db_session, csrf_token):
    """A password exactly at PASSWORD_MIN_LENGTH is accepted."""
    exact_password = "a" * 12  # Exactly 12 characters.
    response = _register(
        client,
        csrf_token,
        follow_redirects=False,
        password=exact_password,
        confirm_password=exact_password,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    user = User.query.filter_by(username="newuser").first()
    assert user is not None
    assert user.verify_password(exact_password) is True


def test_existing_valid_registration_still_works(client, db_session, csrf_token):
    """A valid registration with a sufficiently long password still succeeds."""
    response = _register(client, csrf_token, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    user = User.query.filter_by(username="newuser").first()
    assert user is not None
    assert user.email == "newuser@example.com"
    assert user.is_active is True
    assert user.is_admin is False
