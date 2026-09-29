"""
SecureVault - Configuration
===========================

Central configuration for the SecureVault application.

Configuration values are loaded from environment variables (via python-dotenv)
so that secrets and environment-specific settings are never hard-coded in the
source code. A `.env.example` file documents all required variables.

The base `Config` class is suitable for development. Additional configuration
classes (e.g. `TestingConfig`, `ProductionConfig`) can be added later to
override values for specific environments.
"""

import os
from datetime import timedelta


class Config:
    """
    Base application configuration.

    All values are read from environment variables with sensible defaults
    suitable for local development via Docker Compose.
    """

    # ------------------------------------------------------------------
    # Flask core settings
    # ------------------------------------------------------------------
    # Secret key used for session signing and other cryptographic operations.
    # It MUST be provided via the SECRET_KEY environment variable. There is NO
    # hardcoded fallback: if it is missing, the application fails clearly
    # rather than silently using an insecure default. A random value is NOT
    # generated at runtime because that would invalidate sessions whenever the
    # application restarts.
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY environment variable is not set. "
            "Generate a strong random value and set it, e.g. "
            "python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    # Debug mode. Production-safe default is False. It may be explicitly
    # enabled for local development via DEBUG=true. The value is parsed
    # strictly so that only recognized truthy values enable debug mode (any
    # other value, including an empty string, disables it).
    DEBUG = os.environ.get("DEBUG", "false").lower() in ("1", "true", "yes")

    # ------------------------------------------------------------------
    # SQLAlchemy / PostgreSQL settings
    # ------------------------------------------------------------------
    # Database connection string. Defaults to the PostgreSQL service defined
    # in docker-compose.yml.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://securevault:securevault@db:5432/securevault",
    )

    # Disable the SQLAlchemy event system that tracks object modifications.
    # This saves memory and is recommended for production.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ------------------------------------------------------------------
    # Redis settings
    # ------------------------------------------------------------------
    # Redis connection URL used for caching and as the Celery broker.
    REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

    # ------------------------------------------------------------------
    # Celery settings
    # ------------------------------------------------------------------
    # Celery broker and result backend both use Redis.
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)

    # Timezone for Celery scheduling.
    CELERY_TIMEZONE = os.environ.get("CELERY_TIMEZONE", "UTC")

    # ------------------------------------------------------------------
    # Session settings
    # ------------------------------------------------------------------
    # Session lifetime. Defaults to 1 day.
    PERMANENT_SESSION_LIFETIME = timedelta(
        days=int(os.environ.get("SESSION_LIFETIME_DAYS", "1"))
    )

    # Session cookie security settings.
    # The cookie is not readable from JavaScript (mitigates XSS).
    SESSION_COOKIE_HTTPONLY = True
    # Restrict when the cookie is sent to mitigate CSRF. "Lax" is a safe
    # default that still allows top-level navigations.
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    # Whether the cookie is only sent over HTTPS. Production-safe default is
    # True. It may be explicitly disabled (SESSION_COOKIE_SECURE=false) for
    # local development over plain HTTP.
    SESSION_COOKIE_SECURE = os.environ.get(
        "SESSION_COOKIE_SECURE", "true"
    ).lower() in ("1", "true", "yes")

    # ------------------------------------------------------------------
    # CSRF protection settings
    # ------------------------------------------------------------------
    # CSRF protection is always enabled. Flask-WTF's CSRFProtect validates a
    # per-session token on every state-changing request (POST, PUT, PATCH,
    # DELETE). This is a production-safe default and is never disabled at
    # runtime; tests must supply valid tokens rather than disabling it.
    WTF_CSRF_ENABLED = True
    # Tokens expire after 1 hour. This limits the window in which a stolen
    # token can be replayed while remaining generous enough for normal forms.
    WTF_CSRF_TIME_LIMIT = int(os.environ.get("WTF_CSRF_TIME_LIMIT", "3600"))
    # When True (default), the Referer/Origin header is checked on HTTPS
    # requests to further mitigate CSRF. Kept at the secure default.
    WTF_CSRF_SSL_STRICT = True
    # The session key under which the CSRF token is stored. Defaults to
    # "csrf_token"; left explicit for clarity.
    WTF_CSRF_FIELD_NAME = "csrf_token"

    # ------------------------------------------------------------------
    # Rate limiting settings (Flask-Limiter)
    # ------------------------------------------------------------------
    # Rate limiting is always enabled. Flask-Limiter's Limiter is initialized
    # in extensions.py and reads these settings on init_app. It is never
    # disabled in debug or test mode; tests exercise the real limiter.
    RATELIMIT_ENABLED = True
    # Storage backend for rate-limit counters. Production uses Redis (the same
    # instance already used for caching and the Celery broker). Tests override
    # this to an in-memory backend (see tests/conftest.py) because Redis is not
    # available during unit tests. This does NOT weaken the production config.
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", REDIS_URL)
    # Strategy used to enforce limits. "fixed-window" is a simple, predictable
    # default that resets the counter at the start of each window.
    RATELIMIT_STRATEGY = os.environ.get("RATELIMIT_STRATEGY", "fixed-window")

    # Per-endpoint rate limits. Each is configurable via environment variables
    # with sensible production-safe defaults that do not impede normal
    # development. Limits apply ONLY to the POST method of each endpoint (GET
    # requests are not limited).
    #
    # Login: slow brute-force attempts. 10 attempts per minute per IP is
    # generous for a human but throttles automated guessing.
    LOGIN_RATE_LIMIT = os.environ.get("LOGIN_RATE_LIMIT", "10 per minute")
    # Registration: slow automated account-creation abuse. 5 per hour per IP
    # is a reasonable cap for legitimate signups while deterring bulk abuse.
    REGISTER_RATE_LIMIT = os.environ.get("REGISTER_RATE_LIMIT", "5 per hour")
    # Upload: slow upload abuse. 30 per minute per IP is generous for normal
    # use while throttling bulk uploads.
    UPLOAD_RATE_LIMIT = os.environ.get("UPLOAD_RATE_LIMIT", "30 per minute")

    # ------------------------------------------------------------------
    # File storage settings
    # ------------------------------------------------------------------
    # Absolute path to the temporary upload directory. Uploaded files are
    # placed here before any security validation (which is deferred to later
    # modules). This is resolved relative to the project root so it works in
    # both development and tests.
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage", "uploads"),
    )

    # Maximum size (in bytes) of a single uploaded file. Defaults to 10 MB.
    # This is enforced by the upload service (not only by Flask's global
    # MAX_CONTENT_LENGTH).
    MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))

    # Maximum length (in characters) of an original filename. Filenames longer
    # than this are rejected as untrusted input.
    MAX_FILENAME_LENGTH = int(os.environ.get("MAX_FILENAME_LENGTH", 255))

    # ------------------------------------------------------------------
    # MIME type validation settings
    # ------------------------------------------------------------------
    # Allowlist of MIME types accepted for upload. The MIME type supplied by
    # the client/browser is treated as UNTRUSTED: it is checked against this
    # allowlist only and is NOT proof of the file's actual contents. Magic-byte
    # validation is implemented separately (Module 3.5).
    #
    # The value is a comma-separated list read from the SUPPORTED_MIME_TYPES
    # environment variable. It is normalized to lowercase so validation is
    # case-consistent.
    SUPPORTED_MIME_TYPES = tuple(
        mime.strip().lower()
        for mime in os.environ.get(
            "SUPPORTED_MIME_TYPES",
            "application/pdf,image/jpeg,image/png,text/plain",
        ).split(",")
        if mime.strip()
    )

    # ------------------------------------------------------------------
    # Security settings (foundation only)
    # ------------------------------------------------------------------
    # These are placeholders for future security features. They are defined
    # now so the configuration surface is stable as the project grows.
    # Maximum upload size (bytes). Defaults to 100 MB.
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 100 * 1024 * 1024))

    # ------------------------------------------------------------------
    # Password policy settings
    # ------------------------------------------------------------------
    # Minimum required length (in characters) for a user's password. Enforced
    # server-side during registration (see app/auth/services.py). A minimum
    # length is the smallest safe baseline; complexity requirements are not
    # enforced yet.
    PASSWORD_MIN_LENGTH = int(os.environ.get("PASSWORD_MIN_LENGTH", "12"))

    # ------------------------------------------------------------------
    # Account lockout settings (failed-login protection)
    # ------------------------------------------------------------------
    # Number of consecutive failed login attempts (per username) before the
    # account is temporarily locked. Tracked in Redis; see
    # app/auth/services.py.
    MAX_LOGIN_ATTEMPTS = int(
        os.environ.get("MAX_LOGIN_ATTEMPTS", "5")
    )
    # Lockout duration in seconds. After this many seconds the failure counter
    # (and thus the lockout) automatically expires via the Redis TTL.
    LOGIN_LOCKOUT_DURATION = int(
        os.environ.get("LOGIN_LOCKOUT_DURATION", "900")
    )
