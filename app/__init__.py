"""
SecureVault - Application Factory
=================================

This module implements the Flask Application Factory pattern. It creates and
configures the Flask application instance, initializes extensions, and
registers blueprints.

The factory pattern allows multiple application instances to be created with
different configurations (e.g. development, testing, production), which is
essential for a production-ready, large-scale project.
"""

import os

from flask import (
    Flask,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
)

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config
from extensions import db, migrate, redis_client, celery, csrf


def create_app(config_class: type = Config) -> Flask:
    """
    Application factory that creates and configures a Flask application.

    Args:
        config_class: A configuration class (subclass of Config). Defaults to
            the base Config class, which reads from environment variables.

    Returns:
        A fully configured Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration from the provided config class.
    app.config.from_object(config_class)

    # Create a fresh Limiter for THIS application instance. Flask-Limiter's
    # Limiter accumulates decorated-limit registrations on the instance it is
    # bound to, so a module-level singleton shared across multiple apps would
    # accumulate a new /login rate-limit rule on every create_app() call. Each
    # app therefore owns its own Limiter, giving it independent rate-limiter
    # state and independent decorated-limit registrations. The limiter is
    # passed explicitly to initialize_extensions and register_routes (it is
    # NOT stored on app.extensions, which Flask-Limiter itself uses as a set
    # of registered limiter instances).
    limiter = Limiter(key_func=get_remote_address)

    # Initialize Flask extensions with the application instance.
    initialize_extensions(app, limiter)

    # Register application blueprints.
    register_blueprints(app, limiter)

    # Register application-level routes (e.g. health check).
    register_routes(app, limiter)

    # Register CLI commands (e.g. database seeding).
    register_cli_commands(app)

    return app


def initialize_extensions(app: Flask, limiter: Limiter) -> None:
    """
    Bind all Flask extensions to the application instance.

    Args:
        app: The Flask application instance.
        limiter: The per-app Limiter instance created by create_app().
    """
    # SQLAlchemy ORM for database access.
    db.init_app(app)

    # Alembic migrations integration.
    migrate.init_app(app, db)

    # Redis client for caching / task broker.
    redis_client.init_app(app)

    # CSRF protection for state-changing POST requests. Uses Flask-WTF's
    # CSRFProtect, which validates a token on every POST request. This is
    # enabled globally and is NOT disabled in debug or test mode.
    csrf.init_app(app)

    # Application rate limiting. Uses the per-app Limiter created in
    # create_app(), which reads its storage backend and strategy from the
    # application config. Rate limiting is enabled globally and is NOT disabled
    # in debug or test mode.
    limiter.init_app(app)

    # Celery task queue (configured but no tasks defined yet).
    celery.conf.update(app.config)


def register_blueprints(app: Flask, limiter: Limiter) -> None:
    """
    Register all application blueprints.

    Blueprints are registered here so that new modules can be added simply by
    importing and registering them in this function.

    Args:
        app: The Flask application instance.
        limiter: The per-app Limiter instance created by create_app().
    """
    # Health check blueprint is always available.
    from app.health import health_bp
    app.register_blueprint(health_bp)

    # Authentication blueprint (registration; login deferred to a later module).
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    # Apply the registration rate limit to the auth blueprint's register
    # route. The limiter is per-app (created in create_app), so the decorator
    # is applied here rather than at module definition time in the blueprint.
    # The blueprint's @route decorator defers registration, so the wrapped
    # view function must be installed into the app's view_functions AFTER the
    # blueprint is registered (otherwise the deferred route registration would
    # overwrite it). Flask-Limiter's before_request handler resolves the limit
    # from current_app.view_functions, so this replacement is sufficient.
    from app.auth import register as register_view
    app.view_functions["auth.register"] = limiter.limit(
        lambda: current_app.config["REGISTER_RATE_LIMIT"],
        methods=["POST"],
    )(register_view)

    # Files blueprint (basic authenticated upload).
    from app.files import files_bp
    app.register_blueprint(files_bp)

    # Apply the upload rate limit to the files blueprint's upload route. The
    # limiter is per-app (created in create_app), so the decorator is applied
    # here rather than at module definition time in the blueprint. The
    # blueprint's @route decorator defers registration, so the wrapped view
    # function must be installed into the app's view_functions AFTER the
    # blueprint is registered (otherwise the deferred route registration would
    # overwrite it). Flask-Limiter's before_request handler resolves the limit
    # from current_app.view_functions, so this replacement is sufficient.
    from app.files import upload as upload_view
    app.view_functions["files.upload"] = limiter.limit(
        lambda: current_app.config["UPLOAD_RATE_LIMIT"],
        methods=["POST"],
    )(upload_view)

    # Future blueprints (audit) will be registered here as they are
    # implemented. The blueprint modules exist as placeholders.


def register_routes(app: Flask, limiter: Limiter) -> None:
    """
    Register application-level routes that are not part of a blueprint.

    Args:
        app: The Flask application instance.
        limiter: The per-app Limiter instance created by create_app().
    """
    # Root route: send unauthenticated users to the login page (the
    # authentication entry point) and authenticated users to the dashboard.
    # The JSON health response previously served here is redundant; the
    # dedicated /health endpoint (app/health/__init__.py) already provides
    # the health check used by Docker Compose and monitoring tools.
    @app.route("/")
    def index():
        if get_current_user() is not None:
            return redirect("/dashboard")
        return redirect("/login")

    # Login route. The auth blueprint uses a /auth prefix for registration,
    # but the login route is exposed at the top-level /login path as required.
    # The handler is kept thin and delegates authentication to the service
    # layer in app/auth/services.py.
    from app.auth.services import authenticate_user
    from app.auth.session import (
        SESSION_SESSION_VERSION,
        SESSION_USER_ID,
        admin_required,
        get_current_user,
        login_required,
    )

    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit(
        lambda: current_app.config["LOGIN_RATE_LIMIT"],
        methods=["POST"],
    )
    def login():
        """
        Handle user login.

        GET: Render the login form.
        POST: Authenticate the user, store the user ID in the session, and
        redirect to the dashboard on success.
        """
        if request.method == "POST":
            user = authenticate_user(
                username=request.form.get("username"),
                password=request.form.get("password"),
            )

            if user is not None:
                # Harden the session against fixation: clear any pre-login
                # session data (e.g. attacker-controlled values) before
                # establishing the authenticated session. This ensures the
                # authenticated session is a fresh one, not a reused cookie.
                #
                # Preserve the CSRF token across the clear: Flask-WTF stores
                # the raw token in the session for validation, and wiping it
                # here would break CSRF protection for subsequent requests
                # (e.g. uploads) in the same session.
                csrf_token = session.get("csrf_token")
                session.clear()
                if csrf_token is not None:
                    session["csrf_token"] = csrf_token
                # Mark the session as permanent so the configured
                # PERMANENT_SESSION_LIFETIME is actually enforced.
                session.permanent = True
                # Store only the user's identifier and session-version snapshot
                # in the session. Never store the password, password hash, or
                # other sensitive data. The session_version snapshot is used
                # for multi-session revocation: if the user's version is later
                # incremented, this session becomes unauthenticated.
                session[SESSION_USER_ID] = str(user.id)
                session[SESSION_SESSION_VERSION] = user.session_version
                flash("Login successful.", "success")
                return redirect("/dashboard")

            # Generic error message; do not reveal whether the username exists.
            flash("Invalid username or password.", "error")
            # Preserve the username; never preserve the password.
            return render_template(
                "login.html",
                username=request.form.get("username", ""),
            )

        # GET request: render an empty login form.
        return render_template("login.html", username="")

    @app.route("/dashboard")
    @login_required
    def dashboard():
        """
        Render the protected dashboard for the authenticated user.

        Requires an authenticated session; unauthenticated requests are
        redirected to the login page.
        """
        user = get_current_user()
        return render_template("dashboard.html", user=user)

    @app.route("/admin")
    @admin_required
    def admin():
        """
        Render the protected admin dashboard.

        Requires an authenticated admin user. Unauthenticated users are
        redirected to the login page; authenticated non-admin users receive an
        HTTP 403 Forbidden response.
        """
        user = get_current_user()
        return render_template("admin.html", user=user)

    @app.route("/logout")
    def logout():
        """
        Log the user out by removing authentication information from the
        session, then redirect to the login page.
        """
        session.clear()
        flash("You have been logged out.", "success")
        return redirect("/login")


def register_cli_commands(app: Flask) -> None:
    """
    Register application CLI commands (e.g. ``flask seed``).

    Args:
        app: The Flask application instance.
    """
    from app.models.seed import seed_users

    @app.cli.command("seed")
    def seed_command() -> None:
        """Create default admin and demo users if they do not exist."""
        seed_users()
