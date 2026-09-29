"""
SecureVault - Extensions
========================

Centralized instantiation of all Flask extensions.

Extensions are created here WITHOUT being bound to a specific application
instance. They are initialized in the application factory via `init_app`.
This pattern (the "extension" pattern) is the recommended way to share
extensions across multiple application instances and blueprints.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_redis import FlaskRedis
from flask_wtf.csrf import CSRFProtect
from celery import Celery


# SQLAlchemy ORM instance for database models and queries.
db = SQLAlchemy()

# Alembic migration integration. Bound to `db` so migrations are generated
# against the same metadata.
migrate = Migrate()

# Redis client for caching and general-purpose key/value storage.
redis_client = FlaskRedis()

# CSRF protection for state-changing POST requests. Uses Flask-WTF's
# well-established CSRFProtect implementation (no custom crypto).
csrf = CSRFProtect()

# NOTE: There is intentionally NO module-level Limiter singleton here.
# Flask-Limiter's Limiter accumulates decorated-limit registrations on the
# instance it is bound to. A module-level singleton shared across multiple
# Flask application instances (as created by the application factory, and by
# the test suite) would accumulate a new /login rate-limit rule on every
# create_app() call. Each application instance therefore creates and owns its
# own Limiter inside the application factory (see app/__init__.py), so every
# app gets independent rate-limiter state and independent decorated-limit
# registrations.

# Celery task queue instance. Configured in the application factory using the
# application's config. No tasks are defined yet.
celery = Celery(__name__)
