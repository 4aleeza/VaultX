# SecureVault - Project Foundation Report

This report summarizes the initial project foundation for **SecureVault**, a
production-ready secure file storage platform. This task focused **only** on
project structure and configuration — no business logic was implemented.

---

## 1. Folder Structure Created

```
c:\dropboxpro\
├── app/
│   ├── __init__.py          # Application factory
│   ├── auth/                # Authentication feature
│   │   ├── __init__.py
│   │   └── services.py      # Auth business logic (placeholder)
│   ├── files/               # File storage feature
│   │   ├── __init__.py
│   │   └── services.py      # File business logic (placeholder)
│   ├── audit/               # Dedicated audit package
│   │   ├── __init__.py
│   │   ├── models.py        # Audit log models (placeholder)
│   │   ├── services.py      # Audit business logic (placeholder)
│   │   └── logger.py        # Structured audit logging (placeholder)
│   ├── utils/               # Shared helper utilities
│   │   ├── __init__.py
│   │   ├── hashing.py       # Password/content hashing (placeholder)
│   │   ├── encryption.py    # Encryption helpers (placeholder)
│   │   ├── validators.py    # Input validation (placeholder)
│   │   ├── mime.py          # MIME type detection (placeholder)
│   │   ├── magic.py         # Magic-byte detection (placeholder)
│   │   └── tokens.py        # Token generation (placeholder)
│   ├── models/              # Database models (placeholder)
│   ├── tasks/               # Celery background tasks (placeholder)
│   ├── health/              # Health check blueprint
│   ├── templates/           # Jinja2 templates
│   │   └── index.html
│   └── static/              # Static assets
│       ├── css/style.css
│       └── js/main.js
├── storage/                 # File storage (mounted in Docker)
│   ├── uploads/             # Incoming uploads
│   ├── encrypted/           # Encrypted files at rest (sharded)
│   ├── quarantine/          # Suspicious files (isolated)
│   └── temp/                # Temporary processing files
├── tests/                   # Test suite (split by scope)
│   ├── unit/                # Isolated unit tests
│   ├── integration/         # Multi-component tests
│   ├── security/            # Security-focused tests
│   └── conftest.py          # Shared test fixtures
├── docs/                    # Developer documentation
│   ├── architecture.md
│   ├── security.md
│   └── roadmap.md
├── migrations/              # Alembic migration environment
│   ├── env.py
│   └── script.py.mako
├── config.py                # Application configuration
├── extensions.py            # Flask extension instances
├── run.py                   # Application entry point
├── alembic.ini              # Alembic configuration
├── requirements.txt         # Python dependencies
├── .env.example             # Documented environment variables
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── REPORT.md
```

---

## 2. Files Created

| File | Purpose |
|------|---------|
| `app/__init__.py` | Flask Application Factory (`create_app`) |
| `config.py` | Central configuration class reading from environment variables |
| `extensions.py` | Centralized instantiation of `db`, `migrate`, `redis_client`, `celery` |
| `run.py` | Development server entry point |
| `app/health/__init__.py` | Health check blueprint (`GET /health`) |
| `app/auth/__init__.py` | Auth feature package |
| `app/auth/services.py` | Auth business logic (placeholder) |
| `app/files/__init__.py` | Files feature package |
| `app/files/services.py` | File business logic (placeholder) |
| `app/audit/__init__.py` | Audit package |
| `app/audit/models.py` | Audit log models (placeholder) |
| `app/audit/services.py` | Audit business logic (placeholder) |
| `app/audit/logger.py` | Structured audit logging (placeholder) |
| `app/utils/__init__.py` | Utils package |
| `app/utils/hashing.py` | Hashing helpers (placeholder) |
| `app/utils/encryption.py` | Encryption helpers (placeholder) |
| `app/utils/validators.py` | Validation helpers (placeholder) |
| `app/utils/mime.py` | MIME type helpers (placeholder) |
| `app/utils/magic.py` | Magic-byte detection (placeholder) |
| `app/utils/tokens.py` | Token helpers (placeholder) |
| `app/models/__init__.py` | Models package placeholder |
| `app/tasks/__init__.py` | Tasks package placeholder |
| `app/templates/index.html` | Basic landing template |
| `app/static/css/style.css` | Stylesheet placeholder |
| `app/static/js/main.js` | JavaScript placeholder |
| `storage/{uploads,encrypted,quarantine,temp}/.gitkeep` | Storage directory placeholders |
| `tests/unit/__init__.py` | Unit test package |
| `tests/integration/__init__.py` | Integration test package |
| `tests/security/__init__.py` | Security test package |
| `tests/conftest.py` | Shared test fixtures (placeholder) |
| `docs/architecture.md` | Developer architecture documentation |
| `docs/security.md` | Security model documentation |
| `docs/roadmap.md` | Development roadmap |
| `migrations/env.py` | Alembic migration environment |
| `migrations/script.py.mako` | Alembic migration script template |
| `alembic.ini` | Alembic configuration |
| `requirements.txt` | Python dependencies |
| `.env.example` | Documented environment variables |
| `.gitignore` | Git ignore rules |
| `Dockerfile` | Production image definition |
| `docker-compose.yml` | Multi-service orchestration |
| `REPORT.md` | This report |

---

## 3. Configuration Completed

- **Flask**: Application factory pattern with `create_app()`, config loaded via
  `app.config.from_object(config_class)`.
- **SQLAlchemy**: `db` instance initialized in `extensions.py` and bound in the
  factory. `SQLALCHEMY_TRACK_MODIFICATIONS` disabled for production.
- **Alembic (Flask-Migrate)**: `migrate` instance bound to `db`. Initial
  `alembic.ini` and `migrations/` environment created. No migration scripts
  exist yet (no models).
- **Redis**: `redis_client` (Flask-Redis) initialized and bound.
- **Celery**: `celery` instance created and configured from app config
  (broker/result backend point to Redis). No tasks defined.
- **python-dotenv**: Environment variables are read via `os.environ.get()` in
  `config.py`. The `.env` file is loaded by Flask's dotenv support.

---

## 4. Environment Variables Added

Defined in `.env.example`:

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `dev-secret-key-change-me` | Session/crypto secret key |
| `FLASK_DEBUG` | `true` | Enable/disable debug mode |
| `FLASK_HOST` | `0.0.0.0` | Dev server host |
| `FLASK_PORT` | `5000` | Dev server port |
| `DATABASE_URL` | `postgresql://securevault:securevault@db:5432/securevault` | PostgreSQL connection string |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Celery broker URL |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/0` | Celery result backend |
| `CELERY_TIMEZONE` | `UTC` | Celery timezone |
| `SESSION_LIFETIME_DAYS` | `1` | Session lifetime in days |
| `MAX_CONTENT_LENGTH` | `104857600` (100 MB) | Max upload size (future) |

---

## 5. Docker Services Configured

`docker-compose.yml` defines three services:

| Service | Image | Purpose |
|---------|-------|---------|
| `web` | Built from `Dockerfile` | Flask app via Gunicorn on port `5000` |
| `db` | `postgres:16-alpine` | PostgreSQL database on port `5432` |
| `redis` | `redis:7-alpine` | Redis cache/broker on port `6379` |

- The `web` service depends on healthy `db` and `redis` services.
- Health checks are configured for all three services.
- PostgreSQL data persists via the `postgres_data` named volume.
- The `storage/` directory is bind-mounted into the `web` container so
  encrypted files persist on the host.
- The `Dockerfile` uses a slim Python 3.12 base, installs `psycopg2` system
  dependencies, and runs the app with Gunicorn.

---

## 6. Intentionally Left for Future Tasks

The following were **explicitly NOT implemented** per the task requirements:

- ❌ User model / any database tables
- ❌ Authentication (registration, login, sessions, tokens)
- ❌ File uploads / storage
- ❌ Celery background tasks
- ❌ Business logic in feature `services.py` modules
- ❌ Production-specific config classes (`TestingConfig`, `ProductionConfig`)
- ❌ Security features (encryption, rate limiting, audit logging)

The `auth`, `files`, `audit`, `utils`, `models`, and `tasks` packages exist as
documented placeholders to establish the modular structure. The `storage/`,
`tests/`, and `docs/` directories are scaffolding for future work.

---

## 7. Assumptions Made

1. **Database credentials**: Default PostgreSQL credentials
   (`securevault`/`securevault`) are used for local development and match the
   `docker-compose.yml` defaults. These must be changed in production.
2. **Redis as Celery broker**: Redis is used for both the Celery broker and
   result backend, which is a common lightweight setup. A dedicated broker
   (e.g. RabbitMQ) can be swapped in later.
3. **Gunicorn for production**: The Dockerfile runs the app with Gunicorn
   (3 workers). Worker count can be tuned based on deployment resources.
4. **Health check via curl**: The `web` service healthcheck uses `curl`, which
   is available in the `python:3.12-slim` image. If this changes, the
   healthcheck command must be updated.
5. **Alembic initial config**: The `migrations/` environment was created
   manually to match Flask-Migrate's generated structure. Running
   `flask db init` would regenerate it identically.
6. **`MAX_CONTENT_LENGTH`**: Included as a security foundation setting even
   though file uploads are not yet implemented.
7. **No `.env` committed**: Only `.env.example` is committed. Users must copy
   it to `.env` before running.
8. **Storage architecture**: Metadata will live in PostgreSQL while file
   contents live on disk under `storage/encrypted/`, saved by UUID/hash (never
   original filenames) and sharded by a two-character prefix. See
   `docs/architecture.md`.
9. **`security/` replaced by `audit/`**: The former `security` placeholder
   package was replaced with a dedicated `audit` package. Security-specific
   services can be reintroduced under a `security` feature later if needed.

---

## How to Run

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Start all services with Docker Compose
docker compose up --build

# 3. Verify the health check
curl http://localhost:5000/health
# => {"status": "ok"}
```

---

# Module 2.1 — User Model

This module implements the **User model** and its supporting components. It
does **not** implement authentication (registration, login, sessions, routes,
or templates) — those are deferred to later modules.

---

## 1. Files Created

| File | Purpose |
|------|---------|
| `app/models/user.py` | SQLAlchemy `User` model with Argon2 password hashing |
| `app/models/seed.py` | Idempotent seed script for default admin/demo users |
| `tests/unit/test_user_model.py` | Unit tests for the `User` model |
| `migrations/versions/1d9a8ab68988_create_users_table.py` | Initial Alembic migration creating the `users` table |

## 2. Files Modified

| File | Change |
|------|--------|
| `app/models/__init__.py` | Import `User` so Alembic can autogenerate against it |
| `app/__init__.py` | Registered a `flask seed` CLI command |
| `tests/conftest.py` | Added `app`, `client`, and `db_session` fixtures using an in-memory SQLite database |
| `requirements.txt` | Added `argon2-cffi==23.1.0` and `pytest==8.2.2`; bumped `psycopg2-binary` to `2.9.12` for Python 3.13 support |
| `.env.example` | Documented new seed-user environment variables |
| `alembic.ini` → `migrations/alembic.ini` | Moved into the `migrations/` directory to match the standard Flask-Migrate layout; updated `script_location` to `.` |

## 3. Database Schema Added

The `users` table:

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | Primary key, default `uuid4` |
| `username` | `String(150)` | Unique, indexed, NOT NULL |
| `email` | `String(255)` | Unique, indexed, NOT NULL |
| `password_hash` | `String(255)` | NOT NULL (Argon2 hash, never plaintext) |
| `is_active` | `Boolean` | NOT NULL, default `True` |
| `is_admin` | `Boolean` | NOT NULL, default `False` |
| `created_at` | `DateTime(timezone=True)` | NOT NULL, default UTC now |
| `updated_at` | `DateTime(timezone=True)` | NOT NULL, default UTC now, auto-updated |

## 4. Seed Users Created

Running `flask seed` (idempotent) creates:

| Username | Email | Admin |
|----------|-------|-------|
| `admin` | `admin@vaultx.local` | Yes |
| `demo` | `demo@vaultx.local` | No |

Passwords are hashed with Argon2. Existing users are left untouched on
re-runs.

## 5. Environment Variables Introduced

| Variable | Default | Description |
|----------|---------|-------------|
| `SEED_ADMIN_USERNAME` | `admin` | Admin seed username |
| `SEED_ADMIN_EMAIL` | `admin@vaultx.local` | Admin seed email |
| `SEED_ADMIN_PASSWORD` | `admin-dev-password` | Admin seed password (dev only) |
| `SEED_DEMO_USERNAME` | `demo` | Demo seed username |
| `SEED_DEMO_EMAIL` | `demo@vaultx.local` | Demo seed email |
| `SEED_DEMO_PASSWORD` | `demo-dev-password` | Demo seed password (dev only) |

## 6. Tests Added

`tests/unit/test_user_model.py` (6 tests):

- `test_user_creation` — user persists with correct defaults
- `test_password_is_hashed_not_plaintext` — stored hash is Argon2, not plaintext
- `test_verify_password_correct` — returns `True` for the correct password
- `test_verify_password_incorrect` — returns `False` for an incorrect password
- `test_username_uniqueness` — duplicate usernames raise `IntegrityError`
- `test_email_uniqueness` — duplicate emails raise `IntegrityError`

All tests pass against an in-memory SQLite database.

## 7. Assumptions Made

1. **UUID primary key**: Used `db.Uuid` (PostgreSQL-native `UUID`) as the
   primary key, matching the "UUID preferred" requirement.
2. **Argon2 via `argon2-cffi`**: A single shared `PasswordHasher` instance is
   reused for performance; Argon2 is intentionally CPU/memory-intensive.
3. **`flask seed` requires migrations first**: The seed script assumes the
   schema exists (run `flask db upgrade` before `flask seed`). It does not
   create tables itself.
4. **`alembic.ini` relocated**: Moved into `migrations/` because Flask-Migrate
   expects `migrations/alembic.ini` (standard layout). The root-level file was
   incompatible with `flask db` commands.
5. **`psycopg2-binary` bumped to `2.9.12`**: The pinned `2.9.9` has no wheel
   for Python 3.13 and fails to build from source without `pg_config`.
6. **Seed credentials are development defaults**: They must be overridden via
   environment variables in production.

## 8. Intentionally Deferred to the Next Module

- ❌ Registration, login, logout, and session management
- ❌ Authentication routes, blueprints, and templates
- ❌ Password reset / change flows
- ❌ Email verification
- ❌ Role/permission system beyond the `is_admin` flag
- ❌ User profile fields (name, avatar, etc.)
- ❌ Audit logging tied to user actions
- ❌ Production config classes (`TestingConfig` is defined in `tests/conftest.py` only)

---

# Module 2.2 — User Registration

This module implements **user registration only**. Login, logout, sessions,
Flask-Login, email verification, password reset, CAPTCHA, rate limiting, and
file uploads are **not** implemented.

---

## 1. Files Created

| File | Purpose |
|------|---------|
| `app/templates/register.html` | Registration form template (username, email, password, confirm password, register button) |
| `tests/unit/test_auth_register.py` | Unit tests for the registration flow |

## 2. Files Modified

| File | Change |
|------|--------|
| `app/auth/__init__.py` | Created the `auth` Blueprint with the `/register` route |
| `app/auth/services.py` | Added `register_user()` service with validation and user creation logic |
| `app/__init__.py` | Registered the `auth` Blueprint in the application factory |

## 3. Routes Added

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/auth/register` | Renders the registration form |
| `POST` | `/auth/register` | Validates input, creates the user, redirects to `/login` on success |

## 4. Validation Rules Implemented

- All fields (username, email, password, confirm password) are required.
- Empty or whitespace-only values are rejected.
- Leading/trailing whitespace is trimmed from username and email.
- Username must be unique.
- Email must be unique.
- Password and confirm password must match.
- On failure, error messages are flashed and the form is redisplayed with
  username/email preserved; passwords are never preserved.

## 5. Tests Added

`tests/unit/test_auth_register.py` (9 tests):

- `test_successful_registration` — valid input creates a user and redirects to `/login`
- `test_duplicate_username` — existing username is rejected
- `test_duplicate_email` — existing email is rejected
- `test_password_mismatch` — mismatched passwords are rejected
- `test_empty_required_fields` — missing fields are rejected
- `test_whitespace_only_values_rejected` — whitespace-only values are rejected
- `test_password_stored_as_hash` — password is stored as an Argon2 hash, not plaintext
- `test_username_and_email_are_trimmed` — whitespace is trimmed from username/email
- `test_passwords_not_preserved_on_failure` — passwords are not echoed back on failure

All 15 tests pass (9 new + 6 existing from Module 2.1).

## 6. Assumptions Made

1. **Redirect to literal `/login`**: Since the `/login` route does not exist
   yet, the success redirect uses the literal URL `/login` rather than
   `url_for("auth.login")` (which would raise a `BuildError`). This will be
   switched to `url_for` once the login route is implemented in Module 2.3.
2. **Blueprint URL prefix**: The `auth` Blueprint uses a `/auth` URL prefix,
   so the register route is at `/auth/register`.
3. **Service-layer validation**: Validation and user creation live in
   `app/auth/services.py` (`register_user`), keeping the route handler thin.
4. **No CSRF protection**: CSRF protection is not implemented in this module
   (deferred). The test config sets `WTF_CSRF_ENABLED = False`.

## 7. Intentionally Deferred to Module 2.3 (Login)

- ❌ Login route and template
- ❌ Logout
- ❌ Session management
- ❌ Flask-Login integration
- ❌ Email verification
- ❌ Password reset / change flows
- ❌ CAPTCHA
- ❌ Rate limiting
- ❌ CSRF protection
- ❌ File upload functionality

---

# Module 2.3 — User Login

This module implements **user login only**. Registration, logout, session
management, protected routes, Flask-Login, MFA, OAuth, password reset, email
verification, account lockout, rate limiting, file uploads, authorization, and
audit logging are **not** implemented.

---

## 1. Files Created

| File | Purpose |
|------|---------|
| `app/templates/login.html` | Login form template (username, password, login button) |
| `tests/unit/test_auth_login.py` | Unit tests for the login flow |

## 2. Files Modified

| File | Change |
|------|--------|
| `app/auth/services.py` | Added `authenticate_user()` service for login authentication |
| `app/__init__.py` | Added the `/login` route (GET/POST) and required Flask imports |

## 3. Routes Added

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/login` | Renders the login form |
| `POST` | `/login` | Authenticates the user and redirects to `/dashboard` on success |

## 4. Authentication Logic Implemented

`authenticate_user(username, password)` in `app/auth/services.py`:

- Finds the user by username.
- Rejects inactive accounts (`is_active == False`).
- Verifies the supplied password using `User.verify_password()` (Argon2).
- Returns the authenticated `User` on success, or `None` on failure.

## 5. Validation Implemented

- Username is required (empty or whitespace-only values are rejected).
- Password is required (empty or whitespace-only values are rejected).
- Leading/trailing whitespace is stripped from the username.
- The password value is **not** modified before verification.

## 6. Tests Added

`tests/unit/test_auth_login.py` (10 tests):

- `test_successful_login` — correct credentials redirect to `/dashboard`
- `test_login_fails_with_incorrect_password` — wrong password is rejected
- `test_login_fails_with_nonexistent_username` — unknown username is rejected
- `test_login_fails_for_inactive_user` — inactive account is rejected
- `test_missing_username` — missing username is rejected
- `test_missing_password` — missing password is rejected
- `test_generic_error_message_for_invalid_credentials` — identical generic message for wrong password vs. nonexistent username
- `test_password_not_preserved_on_failure` — password is not echoed back on failure
- `test_password_not_stored_in_plaintext` — stored password is an Argon2 hash
- `test_username_is_trimmed` — whitespace is stripped from the username

All 25 tests pass (10 new + 9 from Module 2.2 + 6 from Module 2.1).

## 7. Security Decisions

1. **Generic error message**: Failed logins always display
   `"Invalid username or password."` regardless of whether the username exists,
   so the response does not reveal valid usernames.
2. **No session created**: Successful login only flashes a success message and
   redirects to `/dashboard`. No authentication session is created in this
   module (deferred to a later module).
3. **Passwords never logged or stored in plaintext**: The password is only
   passed to `User.verify_password()` (Argon2). It is never logged, stored, or
   echoed back to the form on failure.
4. **Existing Argon2 verification reused**: No new password hashing
   implementation was introduced; the existing `User.verify_password()` method
   from Module 2.1 is used.
5. **Redirect to literal `/dashboard`**: Since the `/dashboard` route does not
   exist yet, the success redirect uses the literal URL `/dashboard` rather
   than `url_for(...)` (which would raise a `BuildError`). This will be
   switched once the dashboard route is implemented in Module 2.4.
6. **Login route at top-level `/login`**: The auth blueprint uses a `/auth`
   URL prefix for registration (`/auth/register`), but the login route is
   registered at the application level so it is exposed at `/login` as
   required. The handler remains thin and delegates to
   `app/auth/services.py`.

## 8. Intentionally Deferred to Module 2.4

- ❌ Dashboard route and template
- ❌ Logout
- ❌ Session management
- ❌ Protected routes
- ❌ Flask-Login integration
- ❌ MFA
- ❌ OAuth / Authlib
- ❌ Password reset / change flows
- ❌ Email verification
- ❌ Account lockout
- ❌ Rate limiting
- ❌ CSRF protection
- ❌ File upload functionality
- ❌ Authorization / admin permissions
- ❌ Audit logging

---

# Module 2.4 — Session Management & Protected Dashboard

This module implements **secure session management** after the existing login
flow, a protected dashboard, and logout. Registration, login authentication
logic, password reset, email verification, MFA, OAuth, role-based
authorization, admin functionality, file uploads, file permissions, audit
logging, rate limiting, and account lockout are **not** implemented.

---

## 1. Files Created

| File | Purpose |
|------|---------|
| `app/auth/session.py` | Reusable session helpers: `SESSION_USER_ID`, `get_current_user()`, `login_required` |
| `app/templates/dashboard.html` | Simple dashboard template (VaultX, username, email, logout link) |
| `tests/unit/test_auth_session.py` | Unit tests for session management, dashboard, and logout |

## 2. Files Modified

| File | Change |
|------|--------|
| `app/__init__.py` | Integrated session into `/login`, added `/dashboard` and `/logout` routes |
| `config.py` | Added secure session cookie configuration (`SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE`, `SESSION_COOKIE_SECURE`) |

## 3. Session Design

- After a successful login, the session stores **only** the user's identifier
  under the `user_id` key (`SESSION_USER_ID`).
- The password, password hash, email, full `User` object, and other sensitive
  data are **never** stored in the session.
- The user ID is stored as a string (Flask sessions serialize to JSON) and
  converted back to a `UUID` for database lookups.
- Flask's built-in session mechanism is used; Flask-Login is **not** introduced.

## 4. Current-User Implementation

`get_current_user()` in `app/auth/session.py`:

- Reads the user ID from the session.
- Converts it to a `UUID` (a malformed ID is treated as unauthenticated).
- Looks up the `User` from the database.
- Returns the `User` if the session is valid.
- Returns `None` if there is no authenticated session or the user no longer
  exists (deleted).

## 5. Protected Routes

- `GET /dashboard` is protected by the reusable `login_required` decorator.
- Unauthenticated requests to `/dashboard` are redirected to `/login`.
- The dashboard displays the current user's username and email; it never
  displays the password or password hash.

## 6. Logout Behavior

- `GET /logout` clears the session (`session.clear()`), removing all
  authentication information.
- Redirects to `/login`.
- After logout, the previous authenticated session can no longer access
  `/dashboard` (verified by tests).

## 7. Cookie Security Configuration

Added to `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `SESSION_COOKIE_HTTPONLY` | `True` | Cookie is not readable from JavaScript (mitigates XSS) |
| `SESSION_COOKIE_SAMESITE` | `Lax` | Restricts when the cookie is sent (mitigates CSRF) |
| `SESSION_COOKIE_SECURE` | `False` (configurable) | Cookie sent only over HTTPS; defaults to `False` so local HTTP development works, set to `True` in production |

`SESSION_COOKIE_SECURE` is read from the `SESSION_COOKIE_SECURE` environment
variable, so production can require HTTPS without hard-coding secrets.

## 8. Tests Added

`tests/unit/test_auth_session.py` (11 tests):

- `test_unauthenticated_dashboard_redirects_to_login` — `/dashboard` redirects to `/login` when unauthenticated
- `test_successful_login_creates_authenticated_session` — login stores the user ID in the session
- `test_authenticated_user_can_access_dashboard` — authenticated user can access `/dashboard`
- `test_dashboard_displays_user_information` — dashboard shows the correct username and email
- `test_logout_removes_authentication` — logout removes the user ID from the session
- `test_dashboard_inaccessible_after_logout` — `/dashboard` is inaccessible after logout
- `test_session_contains_only_user_identifier` — session contains only the user ID (plus Flask's internal flash storage)
- `test_password_and_hash_never_stored_in_session` — password and hash are never in the session
- `test_dashboard_does_not_display_password_or_hash` — dashboard never shows password or hash
- `test_invalid_user_id_in_session_is_unauthenticated` — a nonexistent user ID is treated as unauthenticated
- `test_get_current_user_returns_none_for_invalid_session` — `get_current_user` returns `None` for a deleted user

All 36 tests pass (11 new + 10 from Module 2.3 + 9 from Module 2.2 + 6 from
Module 2.1).

## 9. Security Considerations

1. **Minimal session data**: Only the user's identifier is stored in the
   session. No password, hash, email, or full user object is ever stored.
2. **Safe user resolution**: `get_current_user()` handles malformed and
   nonexistent user IDs gracefully, treating them as unauthenticated.
3. **Secure cookie flags**: `HttpOnly`, `SameSite=Lax`, and configurable
   `Secure` flags are set to mitigate XSS and CSRF.
4. **Logout clears the session**: `session.clear()` removes all authentication
   information, preventing reuse of the previous session.
5. **No secrets hard-coded**: `SESSION_COOKIE_SECURE` is configurable via
   environment variable; the existing `SECRET_KEY` is used for session signing.
6. **No Flask-Login**: Flask's built-in session mechanism is used for this
   module, as required.

## 10. Intentionally Deferred to the Next Module

- ❌ Flask-Login integration
- ❌ Role-based authorization / admin permissions
- ❌ MFA
- ❌ OAuth / Authlib
- ❌ Password reset / change flows
- ❌ Email verification
- ❌ Account lockout
- ❌ Rate limiting
- ❌ CSRF protection
- ❌ File upload functionality
- ❌ File permissions
- ❌ Audit logging

---

# Module 2.5 — Basic Authorization & Admin Protection

This module implements the **basic authorization foundation** for SecureVault:
a reusable `admin_required` decorator and a protected `/admin` route. It builds
directly on the existing session management from Module 2.4 and the `User`
model's `is_admin` field. This task **only** implements the authorization
foundation — no file storage or other features were added.

## 1. Files Created

| File | Purpose |
|------|---------|
| `app/templates/admin.html` | Simple admin dashboard template (VaultX, Admin Dashboard, current admin username, logout link) |
| `tests/unit/test_auth_admin.py` | Unit tests for the `admin_required` decorator and the protected `/admin` route |

## 2. Files Modified

| File | Change |
|------|--------|
| `app/auth/session.py` | Added the reusable `admin_required` decorator |
| `app/__init__.py` | Added the protected `GET /admin` route |

## 3. Authorization Behavior

The `admin_required` decorator in `app/auth/session.py`:

- **Requires an authenticated user** — reuses the existing `get_current_user()`
  helper (no duplicated session lookup logic).
- **Redirects unauthenticated users** to `/login`.
- **Returns HTTP 403** for authenticated non-admin users.
- **Allows authenticated admin users** to continue to the protected view.
- **Reads `User.is_admin` from the database** — never trusts an `is_admin`
  value stored in the session.

## 4. `admin_required` Implementation

```python
def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return redirect(url_for("login"))
        if not user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped
```

- Reuses `get_current_user()` from Module 2.4 — no session lookup logic is
  duplicated.
- `abort(403)` raises a `Forbidden` exception that Flask converts to an HTTP
  403 response during request dispatch.
- The decorator is applied with `@wraps(view)` so the wrapped view preserves
  its metadata.

## 5. `/admin` Route

`GET /admin` in `app/__init__.py`:

- Protected by `@admin_required`.
- Requires an authenticated user.
- Requires that the user is an admin.
- Renders `admin.html` with the current admin user.
- Displays the current admin user's username.

## 6. Security Decisions

1. **No `is_admin` in the session**: Only the user's identifier is stored in
   the session (from Module 2.4). Authorization flags are never stored in the
   session.
2. **Database is the source of truth**: `User.is_admin` is read from the
   database on every request via `get_current_user()`, so a stale or forged
   session cannot grant admin access.
3. **Reuse over duplication**: `admin_required` builds on `get_current_user()`
   and `login_required`; no session lookup logic is duplicated.
4. **No sensitive data exposed**: The admin page displays only the admin
   user's username. It never displays the password, password hash, email, or
   other sensitive information.
5. **Clear separation of concerns**: Unauthenticated users are redirected to
   `/login`; authenticated non-admin users receive HTTP 403. This distinguishes
   "not logged in" from "logged in but not authorized."

## 7. Tests Added

`tests/unit/test_auth_admin.py` (8 tests):

- `test_unauthenticated_admin_redirects_to_login` — unauthenticated `/admin` redirects to `/login`
- `test_normal_user_admin_returns_403` — authenticated non-admin user receives HTTP 403 on `/admin`
- `test_admin_user_can_access_admin` — authenticated admin user can access `/admin`
- `test_admin_dashboard_displays_admin_username` — admin dashboard shows the correct admin username
- `test_admin_required_does_not_grant_access_to_normal_user` — `admin_required` denies a normal user (raises `Forbidden`)
- `test_admin_required_allows_admin_user` — `admin_required` allows an admin user through
- `test_admin_required_redirects_unauthenticated` — `admin_required` redirects unauthenticated users to `/login`
- `test_admin_page_does_not_expose_sensitive_info` — admin page never shows password or hash

All 44 tests pass (8 new + 11 from Module 2.4 + 10 from Module 2.3 + 9 from
Module 2.2 + 6 from Module 2.1).

## 8. Intentionally Deferred to the Next Module

- ❌ File upload functionality
- ❌ File permissions / per-file access control
- ❌ Role-based authorization beyond the single `is_admin` flag
- ❌ Audit logging
- ❌ CSRF protection
- ❌ Rate limiting
- ❌ MFA
- ❌ OAuth / Authlib
- ❌ Password reset / change flows
- ❌ Email verification
- ❌ Account lockout

---

# Module 3.1 — File Model

This module implements the **database model for stored files**. It creates the
SQLAlchemy `File` model (metadata only), the `User ↔ File` relationship, and an
Alembic migration for the `files` table. This task **only** creates the model —
no uploads, downloads, encryption, scanning, or file routes were implemented.

## 1. Files Created

| File | Purpose |
|------|---------|
| `app/models/file.py` | SQLAlchemy `File` model (metadata only) |
| `migrations/versions/a1b2c3d4e5f6_create_files_table.py` | Alembic migration creating the `files` table |
| `tests/unit/test_file_model.py` | Unit tests for the `File` model and `User ↔ File` relationship |

## 2. Files Modified

| File | Change |
|------|--------|
| `app/models/user.py` | Added the `files` relationship (`user.files`) with `back_populates="owner"` and `cascade="all, delete-orphan"` |
| `app/models/__init__.py` | Imported and exported `File` so Alembic autogenerate sees the new table |

## 3. Database Schema

The `files` table stores **metadata only** — file contents are never persisted
in PostgreSQL.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | Primary key, default `uuid.uuid4` |
| `owner_id` | `UUID` | Foreign key → `users.id`, `ON DELETE CASCADE`, indexed, required |
| `original_filename` | `String(255)` | Required — filename supplied by the user |
| `stored_filename` | `String(255)` | Required — internal filename for storage |
| `storage_path` | `String(1024)` | Required — eventual storage location |
| `file_size` | `BigInteger` | Required — must never be negative |
| `mime_type` | `String(255)` | Required |
| `file_hash` | `String(128)` | Nullable — cryptographic hash (computed later) |
| `status` | `String(32)` | Required, default `"pending"` |
| `created_at` | `DateTime(timezone=True)` | Required, default UTC now |
| `updated_at` | `DateTime(timezone=True)` | Required, default UTC now, `onupdate` |

## 4. User/File Relationship

- `user.files` — a `User` can access their files via a one-to-many
  relationship (`back_populates="owner"`).
- `file.owner` — a `File` can access its owner via `back_populates="files"`.
- Deleting a user cascades to their files (`cascade="all, delete-orphan"` on
  the ORM side, matching the `ON DELETE CASCADE` foreign key).
- The relationship is defined on the existing `User` model; no unrelated User
  functionality was modified.

## 5. Constraints

- `owner_id` is required and indexed; it references `users.id` with
  `ON DELETE CASCADE`.
- `file_size` must never be negative — enforced by a `CheckConstraint`
  (`ck_files_file_size_non_negative`, `file_size >= 0`).
- All required fields (`original_filename`, `stored_filename`, `storage_path`,
  `file_size`, `mime_type`) are `nullable=False`.
- `file_hash` is nullable (the hash is computed later during processing).

## 6. Migration Details

`migrations/versions/a1b2c3d4e5f6_create_files_table.py`:

- `down_revision = '1d9a8ab68988'` (chains onto the existing users migration).
- `upgrade()` creates the `files` table, the foreign key to `users.id`, the
  `file_size >= 0` check constraint, and the `ix_files_owner_id` index.
- `downgrade()` drops the index and the `files` table cleanly.
- The existing users migration was **not** modified.
- Verified against a temporary SQLite database: `upgrade` to `head` creates
  both tables, and `downgrade` to `1d9a8ab68988` drops the `files` table.

## 7. Tests Added

`tests/unit/test_file_model.py` (13 tests):

- `test_file_creation` — a file can be created and persisted with default status
- `test_file_belongs_to_user` — `file.owner` resolves to the owning user
- `test_user_can_access_files_through_relationship` — `user.files` returns the user's files
- `test_owner_id_required` — a file without an owner is rejected
- `test_original_filename_required` — missing `original_filename` is rejected
- `test_stored_filename_required` — missing `stored_filename` is rejected
- `test_storage_path_required` — missing `storage_path` is rejected
- `test_file_size_required` — missing `file_size` is rejected
- `test_mime_type_required` — missing `mime_type` is rejected
- `test_negative_file_size_rejected` — negative `file_size` is rejected by the check constraint
- `test_default_status_is_pending` — default status is `"pending"`
- `test_file_hash_can_be_null` — `file_hash` is nullable
- `test_uuid_primary_key_generated` — UUID primary key is generated and unique

All 57 tests pass (13 new + 44 from Modules 2.1–2.5).

## 8. Security Considerations

1. **Metadata only**: The `File` model stores metadata only. File contents are
   never stored in PostgreSQL.
2. **`original_filename` is not a path**: It is treated as an opaque user
   string and must never be trusted as a filesystem path. The internal
   `stored_filename` and `storage_path` are separate fields.
3. **No physical files created**: This module creates no files on disk.
4. **No status-transition logic**: The `status` field defaults to `"pending"`
   but no transition logic is implemented yet.
5. **`file_hash` deferred**: The cryptographic hash is nullable and will be
   computed during later processing.

## 9. Intentionally Deferred to the Next Module

- ❌ File uploads
- ❌ File downloads
- ❌ File encryption
- ❌ ClamAV scanning
- ❌ CDR (Content Disarm & Reconstruction)
- ❌ MIME validation
- ❌ Magic-byte validation
- ❌ Signed URLs
- ❌ File sharing
- ❌ File permissions
- ❌ Celery tasks
- ❌ Redis functionality
- ❌ Audit logging
- ❌ File routes
- ❌ File templates
- ❌ Status-transition logic

---

# Module 3.2 — Basic File Upload

This module implements the **basic authenticated file-upload mechanism**. It
creates a `files` Blueprint with a minimal upload page and a `POST /files/upload`
route that stores an uploaded file in the temporary upload area and creates a
`File` metadata record. This task **only** implements the upload mechanism — no
security validation, encryption, scanning, or downloads were added.

## 1. Files Created

| File | Purpose |
|------|---------|
| `app/templates/upload.html` | Minimal upload page (file input, upload button, flash messages) |
| `tests/unit/test_upload.py` | Unit tests for the upload flow |

## 2. Files Modified

| File | Change |
|------|--------|
| `app/files/__init__.py` | Replaced the placeholder with the `files_bp` Blueprint and the `GET`/`POST /files/upload` routes |
| `app/files/services.py` | Implemented `save_uploaded_file(...)` business logic |
| `app/__init__.py` | Registered the `files_bp` Blueprint |
| `config.py` | Added the `UPLOAD_FOLDER` configuration setting |

## 3. Upload Route

- `GET /files/upload` — renders the minimal upload page.
- `POST /files/upload` — accepts a `multipart/form-data` upload, delegates to
  the service layer, flashes a success/error message, and redirects back to the
  upload page.
- Both routes are protected by the existing `@login_required` decorator.
  Unauthenticated requests are redirected to `/login`.
- The route stays **thin**: it handles HTTP/form concerns and delegates all
  business logic to `save_uploaded_file(...)` in `app/files/services.py`.

## 4. Storage Behavior

- Uploaded files are written to `storage/uploads/` (the `UPLOAD_FOLDER` config
  setting, resolved relative to the project root).
- The physical filename is a **cryptographically random UUID** generated via
  `uuid.uuid4()` — never the user-supplied filename.
- The `storage_path` stored on the `File` record is the relative path
  `storage/uploads/<uuid>`.
- No file is stored directly under the application source directory.

## 5. Filename Handling

- The user-supplied filename is treated as **untrusted input**.
- It is **never** concatenated into a filesystem path and **never** used as the
  physical filename.
- Path-traversal attempts (e.g. `../../secret.txt`, `..\..\secret.txt`) cannot
  determine the physical storage location because the physical filename is a
  generated UUID.
- The original filename is preserved **only** as database metadata
  (`original_filename`).

## 6. Database Behavior

After a successful physical write, a `File` record is created with:

| Field | Value |
|-------|-------|
| `owner_id` | Current authenticated user's ID (from `get_current_user()`, never client-supplied) |
| `original_filename` | Uploaded filename |
| `stored_filename` | Generated internal UUID filename |
| `storage_path` | Relative path `storage/uploads/<uuid>` |
| `file_size` | Uploaded file size (from the written file) |
| `mime_type` | Value supplied by Flask/Werkzeug |
| `file_hash` | `NULL` (not computed yet) |
| `status` | `"pending"` |

## 7. Error / Rollback Behavior

- If the database commit fails, the transaction is **rolled back** and the
  newly created physical upload file is **removed**, so no orphaned file is
  left behind.
- An appropriate error message is returned to the user.
- Empty filename and missing-file cases are rejected before any file is written.

## 8. Tests Added

`tests/unit/test_upload.py` (11 tests):

- `test_unauthenticated_upload_redirects_to_login` — unauthenticated upload redirects to `/login`
- `test_authenticated_user_can_upload` — an authenticated user can upload a file
- `test_file_record_is_created` — a `File` record is created after upload
- `test_file_belongs_to_authenticated_user` — the record belongs to the authenticated user
- `test_original_filename_stored_as_metadata` — the original filename is preserved as metadata
- `test_physical_filename_is_not_original` — the physical filename is a generated UUID, not the original
- `test_physical_file_exists_in_uploads` — the physical file exists in `storage/uploads/`
- `test_empty_filename_rejected` — an empty filename is rejected (no record created)
- `test_no_file_supplied_rejected` — a missing file is rejected
- `test_path_traversal_filename_does_not_escape` — a path-traversal filename cannot escape `storage/uploads/`
- `test_database_failure_removes_orphaned_file` — a DB failure rolls back and removes the physical file

All tests use a **temporary upload directory** (`tmp_path`) so the real project
storage directories are never written to. Verified: `storage/uploads/`,
`storage/encrypted/`, `storage/quarantine/`, and `storage/temp/` all remain
empty (only `.gitkeep`) after the test run.

All 68 tests pass (11 new + 57 from Modules 2.1–3.1).

## 9. Security Limitations

This module intentionally does **not** trust the uploaded file. The file is
only placed into the temporary upload area. It is **not** described as "safe",
"clean", or "validated". The `status` is set to `"pending"` because security
validation will be implemented in later modules.

## 10. Intentionally Deferred to Later File-Security Modules

- ❌ MIME validation
- ❌ Magic-byte validation
- ❌ ClamAV scanning
- ❌ CDR (Content Disarm & Reconstruction)
- ❌ File encryption
- ❌ File hashing
- ❌ Signed URLs
- ❌ File sharing
- ❌ File downloads
- ❌ File access-control rules beyond ownership
- ❌ Celery tasks
- ❌ Redis processing
- ❌ Audit logging
- ❌ Virus scanning
- ❌ File previews
- ❌ Image processing
- ❌ File conversion

---

# Module 3.3 — Upload Metadata & File-Size Validation

This module adds **upload metadata and file-size validation** to the file
upload flow. It introduces reusable validation helpers for the original
filename and the uploaded file size, and integrates them into
`save_uploaded_file(...)` so that invalid uploads are rejected **before** any
physical file is written or any database record is created. This task **only**
adds metadata and size validation — no MIME, magic-byte, or content security
validation was added.

## 1. Files Created

| File | Purpose |
|------|---------|
| `app/files/validation.py` | Reusable validation helpers (`validate_original_filename`, `validate_file_size`) |
| `tests/unit/test_upload_validation.py` | Unit tests for the validation helpers and their integration into the upload flow |

## 2. Files Modified

| File | Change |
|------|--------|
| `app/files/services.py` | Integrated filename and size validation into `save_uploaded_file(...)`; added `_measure_stream_size(...)` to measure the actual uploaded bytes |
| `config.py` | Added `MAX_UPLOAD_SIZE` and `MAX_FILENAME_LENGTH` configuration settings |
| `.env.example` | Documented `MAX_UPLOAD_SIZE` and `MAX_FILENAME_LENGTH` |
| `tests/unit/test_upload.py` | Updated `test_path_traversal_filename_does_not_escape` to reflect the new rejection behavior |

## 3. Validation Rules

### Filename (`validate_original_filename`)

The original filename is treated as **untrusted input** and rejected when:

- It is `None`, empty, or whitespace-only → `"The filename cannot be empty."`
- It exceeds `MAX_FILENAME_LENGTH` characters → `"The filename is too long (maximum {n} characters)."`
- It contains a path separator (`/` or `\`) → `"The filename must not contain path separators."`

Rejecting path separators on both Windows (`\`) and Linux/Unix (`/`) prevents
path-traversal attempts such as `../../secret.txt` or `..\..\secret.txt`.

### Size (`validate_file_size`)

The uploaded file size is rejected when:

- It is `None`, zero, or negative → `"The file is empty."`
- It exceeds `MAX_UPLOAD_SIZE` bytes → `"The file exceeds the maximum upload size of {n} MB."`

The size is **measured from the actual uploaded bytes** (via
`_measure_stream_size`, which seeks to the end of the stream and restores the
position) — it is **never trusted from the client**.

## 4. Configuration Values

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_UPLOAD_SIZE` | `10 * 1024 * 1024` (10 MB) | Maximum size of a single uploaded file, in bytes |
| `MAX_FILENAME_LENGTH` | `255` | Maximum length of an original filename, in characters |

Both are overridable via environment variables (`MAX_UPLOAD_SIZE`,
`MAX_FILENAME_LENGTH`) and documented in `.env.example`.

## 5. Upload-Flow Changes

The upload flow in `save_uploaded_file(...)` is now:

```
Receive upload
    ↓
Validate filename
    ↓
Validate size
    ↓
Save temporary upload
    ↓
Create File metadata
```

- Filename validation happens **first** (cheap, no I/O).
- Size validation happens **before** the file is written, so an oversized or
  zero-byte file is rejected without touching the filesystem.
- If validation fails, **no database record is created** and **no physical
  file is left behind**.
- The `file_size` recorded on the `File` record is the measured actual byte
  count, not a client-supplied value.
- The UUID-based physical storage filename remains independent of the original
  filename.

## 6. Tests Added

`tests/unit/test_upload_validation.py` (21 tests):

**`validate_original_filename` (8 tests):**
- `test_normal_filename_accepted` — a normal filename passes
- `test_empty_filename_rejected` — an empty filename is rejected
- `test_whitespace_filename_rejected` — a whitespace-only filename is rejected
- `test_none_filename_rejected` — a `None` filename is rejected
- `test_path_traversal_filename_rejected` — `../../secret.txt` is rejected
- `test_windows_style_path_traversal_rejected` — `..\..\secret.txt` is rejected
- `test_filename_exceeding_max_length_rejected` — a filename over the limit is rejected
- `test_filename_at_max_length_accepted` — a filename exactly at the limit is accepted

**`validate_file_size` (5 tests):**
- `test_zero_byte_file_rejected` — a zero-byte file is rejected
- `test_none_size_rejected` — a `None` size is rejected
- `test_negative_size_rejected` — a negative size is rejected
- `test_file_exactly_at_max_upload_size_accepted` — a file exactly at the limit is accepted
- `test_file_larger_than_max_upload_size_rejected` — a file over the limit is rejected

**Integration into the upload flow (8 tests):**
- `test_upload_with_invalid_filename_rejected` — a path-traversal filename is rejected
- `test_rejected_invalid_filename_creates_no_file_record` — no `File` record is created
- `test_upload_with_oversized_file_rejected` — an oversized upload is rejected
- `test_rejected_oversized_file_leaves_no_physical_file` — no physical file remains
- `test_upload_with_zero_byte_file_rejected` — a zero-byte upload is rejected
- `test_upload_at_max_size_accepted` — an upload exactly at the limit is accepted
- `test_stored_filename_independent_of_original` — the UUID storage filename is independent of the original
- `test_file_size_recorded_from_actual_bytes` — the recorded size reflects the actual bytes

All tests use a **temporary upload directory** (`tmp_path`) so the real project
storage directories are never written to.

All 89 tests pass (21 new + 68 from Modules 2.1–3.2).

## 7. Security Considerations

- The original filename is validated (empty, length, path separators) but is
  **never** used as the physical filename and **never** concatenated into a
  filesystem path.
- Path separators are rejected on both Windows and Linux/Unix, closing the
  path-traversal vector at the validation layer.
- The file size is measured from the actual uploaded bytes, not trusted from
  the client, so a client cannot bypass the size limit by lying about the
  content length.
- Rejected uploads leave **no physical file** and **no database record**,
  preventing orphaned files and metadata pollution.
- The file is still only placed into the temporary upload area with
  `status="pending"`; it is **not** described as "safe", "clean", or
  "validated".

## 8. Intentionally Deferred to Later File-Security Modules

- ❌ MIME validation
- ❌ Magic-byte validation
- ❌ ClamAV scanning
- ❌ CDR (Content Disarm & Reconstruction)
- ❌ File encryption
- ❌ File hashing
- ❌ Signed URLs
- ❌ File sharing
- ❌ File downloads
- ❌ File access-control rules beyond ownership
- ❌ Celery tasks
- ❌ Redis processing
- ❌ Audit logging
- ❌ Virus scanning
- ❌ File previews
- ❌ Image processing
- ❌ File conversion

---

# Module 3.4 — MIME Type Validation

This module adds **MIME type validation** to the file upload flow. It
introduces a configurable allowlist of supported MIME types and a reusable
`validate_mime_type` helper, and integrates it into `save_uploaded_file(...)`
so that uploads declaring an unsupported MIME type are rejected **before** any
physical file is written or any database record is created. This task **only**
implements MIME allowlist validation — no magic-byte detection, ClamAV, CDR,
encryption, hashing, or content inspection was added.

## 1. Files Created

| File | Purpose |
|------|---------|
| `tests/unit/test_mime_validation.py` | Unit tests for `validate_mime_type` and its integration into the upload flow |

## 2. Files Modified

| File | Change |
|------|--------|
| `app/files/validation.py` | Added the reusable `validate_mime_type` helper |
| `app/files/services.py` | Integrated MIME validation into `save_uploaded_file(...)`; stored the validated MIME type on the `File` record |
| `app/files/__init__.py` | Updated the module docstring to reflect that MIME validation is now implemented (magic bytes still deferred) |
| `config.py` | Added the `SUPPORTED_MIME_TYPES` configuration setting |
| `.env.example` | Documented `SUPPORTED_MIME_TYPES` |

## 3. Supported MIME Types

The allowlist is centralized in `config.py` as `SUPPORTED_MIME_TYPES` and is
overridable via the `SUPPORTED_MIME_TYPES` environment variable. The initial
allowlist supports exactly four types:

| MIME Type | Description |
|-----------|-------------|
| `application/pdf` | PDF documents |
| `image/jpeg` | JPEG images |
| `image/png` | PNG images |
| `text/plain` | Plain text files |

Arbitrary MIME types are **not** accepted. The allowlist is normalized to
lowercase at load time so validation is case-consistent.

## 4. Validation Behavior

`validate_mime_type(mime_type)` in `app/files/validation.py`:

- **Rejects a missing (`None`) MIME type** → `"The file's MIME type is missing."`
- **Rejects an empty or whitespace-only MIME type** → `"The file's MIME type is missing."`
- **Rejects a MIME type not in the allowlist** → `"The file type '{mime}' is not supported."`
- **Accepts a MIME type in the allowlist** → returns a valid result.
- **Is case-consistent**: both the declared MIME type and the allowlist are
  normalized to lowercase before comparison, so `"Application/PDF"` and
  `"application/pdf"` are treated identically.
- **Trims surrounding whitespace** from the declared MIME type.

It returns a `ValidationResult` dataclass (`.valid`, `.error`), matching the
existing validation helpers.

## 5. Upload-Flow Changes

The upload flow in `save_uploaded_file(...)` is now:

```
Receive upload
    ↓
Validate filename
    ↓
Validate size
    ↓
Validate MIME type
    ↓
Save temporary upload
    ↓
Create File metadata
```

- MIME validation happens **after** filename and size validation but **before**
  the file is written, so an upload declaring an unsupported MIME type is
  rejected without touching the filesystem.
- If MIME validation fails, **no database record is created** and **no
  physical file is left behind**.
- For accepted uploads, the **validated MIME type** is stored in
  `File.mime_type`.
- The **UUID-based physical filename is unchanged** (still independent of the
  original filename).
- `File.status` remains `"pending"`.

## 6. Tests Added

`tests/unit/test_mime_validation.py` (18 tests):

**`validate_mime_type` (10 tests):**
- `test_application_pdf_accepted` — `application/pdf` is accepted
- `test_image_jpeg_accepted` — `image/jpeg` is accepted
- `test_image_png_accepted` — `image/png` is accepted
- `test_text_plain_accepted` — `text/plain` is accepted
- `test_missing_mime_type_rejected` — a `None` MIME type is rejected
- `test_empty_mime_type_rejected` — an empty MIME type is rejected
- `test_whitespace_mime_type_rejected` — a whitespace-only MIME type is rejected
- `test_unsupported_mime_type_rejected` — a MIME type not in the allowlist is rejected
- `test_mime_validation_is_case_consistent` — uppercase is treated as lowercase
- `test_mime_validation_trims_whitespace` — surrounding whitespace is trimmed

**Integration into the upload flow (8 tests):**
- `test_upload_with_supported_mime_accepted` — a supported MIME type is accepted
- `test_upload_with_unsupported_mime_rejected` — an unsupported MIME type is rejected
- `test_rejected_mime_creates_no_file_record` — no `File` record is created
- `test_rejected_mime_leaves_no_physical_file` — no physical file remains
- `test_accepted_mime_stored_in_file_record` — the validated MIME type is stored in `File.mime_type`
- `test_upload_with_missing_mime_rejected` — a missing MIME type is rejected
- `test_upload_with_case_variant_mime_accepted` — a case-variant MIME type is accepted
- `test_existing_filename_and_size_validation_still_works` — filename and size validation still reject invalid uploads

All tests use a **temporary upload directory** (`tmp_path`) so the real project
storage directories are never written to.

All 107 tests pass (18 new + 89 from Modules 2.1–3.3).

## 7. Security Limitations

**MIME type validation is an allowlist check only.** It verifies that the MIME
type declared by the client/browser is present in the configured allowlist. It
does **NOT** prove that the file's actual contents match the declared MIME
type. A malicious client can trivially declare `application/pdf` while
uploading arbitrary bytes.

## 8. Why MIME Validation Alone Is Insufficient

The MIME type is supplied by the client/browser and is therefore **untrusted**.
An attacker can:

- Declare a benign MIME type (e.g. `image/png`) while uploading a malicious
  executable or script.
- Rename a malicious file to a benign extension so the browser/HTTP layer
  reports a benign MIME type.

---

# Phase A.1 — Production-Safe Configuration

This phase makes VaultX configuration **safer by default**. It removes the
insecure hardcoded `SECRET_KEY` fallback, defaults `DEBUG` to `False`, and
defaults `SESSION_COOKIE_SECURE` to `True`. No business logic, models,
migrations, routes, or UI were changed.

## 1. What Was Changed

| File | Change |
|------|--------|
| `config.py` | `SECRET_KEY` now required from the environment (no insecure fallback); `DEBUG` defaults to `False`; `SESSION_COOKIE_SECURE` defaults to `True` |
| `tests/conftest.py` | Sets a deterministic test-only `SECRET_KEY` so the suite does not depend on the developer's environment |
| `.env.example` | Documents `SECRET_KEY=` (required, no default), `DEBUG=false`, and `SESSION_COOKIE_SECURE=true` with explanatory comments |
| `tests/unit/test_config.py` | **New** — focused tests for the configuration behavior |

## 2. SECRET_KEY Behavior

- `SECRET_KEY` is read **only** from the `SECRET_KEY` environment variable.
- The hardcoded `"dev-secret-key-change-me"` fallback was **removed**.
- If `SECRET_KEY` is missing, the application **fails clearly** at import time
  with a `RuntimeError` and a helpful message (including a command to generate
  a strong random value).
- A random key is **not** generated at runtime, because that would invalidate
  sessions on every restart.

## 3. DEBUG Behavior

- `DEBUG` now defaults to **`False`** (production-safe).
- It can be explicitly enabled for local development via `DEBUG=true`.
- The value is parsed strictly: only `1`, `true`, or `yes` (case-insensitive)
  enable debug mode; any other value (including an empty string) disables it.

## 4. Session Cookie Behavior

- `SESSION_COOKIE_HTTPONLY` remains **`True`**.
- `SESSION_COOKIE_SAMESITE` remains **`Lax`**.
- `SESSION_COOKIE_SECURE` now defaults to **`True`** (cookie sent only over
  HTTPS).
- It can be explicitly disabled (`SESSION_COOKIE_SECURE=false`) for local
  development over plain HTTP.

## 5. Environment Variables Added/Changed

| Variable | Default | Notes |
|----------|---------|-------|
| `SECRET_KEY` | **required** (no default) | Must be a strong random secret; no insecure fallback |
| `DEBUG` | `false` | Keep `false` outside local development |
| `SESSION_COOKIE_SECURE` | `true` | Set `false` only for local HTTP development |

## 6. Tests Added

`tests/unit/test_config.py` covers:

1. `SECRET_KEY` is loaded from the environment.
2. Missing `SECRET_KEY` fails clearly (raises `RuntimeError`).
3. `DEBUG` defaults to `False`.
4. `DEBUG=true` enables debug mode.
5. `DEBUG=false` disables debug mode.
6. `SESSION_COOKIE_HTTPONLY` remains `True`.
7. `SESSION_COOKIE_SAMESITE` remains `Lax`.
8. `SESSION_COOKIE_SECURE` defaults to `True`.
9. `SESSION_COOKIE_SECURE=false` disables the Secure flag for local HTTP.

## 7. Test Results

```
137 passed in 19.88s
```

All 128 pre-existing tests still pass, plus 9 new configuration tests.

## 8. Verification

- Application imports successfully with `SECRET_KEY` set:
  `DEBUG=False`, `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE=Lax`,
  `SESSION_COOKIE_SECURE=True`.
- Application fails clearly with a `RuntimeError` when `SECRET_KEY` is missing.

## 9. Development Considerations

- **You must now set `SECRET_KEY`** in your local `.env` (copy `.env.example`
  and fill in a real value) before the app will start. This is intentional.
- The existing dev server (started without a `SECRET_KEY`) now stops with a
  clear error until a `SECRET_KEY` is provided.
- `docker-compose.yml` forwards `SECRET_KEY` and `DEBUG` from the
  environment.

## 10. Intentionally Deferred (NOT part of this phase)

- ❌ Removing default admin credentials (Phase A.2)
- ❌ CSRF protection
- ❌ Flask-Limiter (rate limiting)
- ❌ Flask-Talisman (security headers)
- ❌ Any other security feature
- Bypass the allowlist entirely by crafting a raw HTTP request with a forged
  `Content-Type` header.

Because the declared MIME type is not tied to the actual file bytes, an
allowlist check alone provides **no** protection against malicious content. It
only filters out obviously-declared unsupported types.

## 9. What Is Intentionally Deferred to Module 3.5

- ❌ **Magic-byte detection** — inspecting the file's actual bytes to verify
  they match the declared MIME type. This is the next security layer and is
  implemented separately in Module 3.5.
- ❌ File signature detection
- ❌ ClamAV scanning
- ❌ CDR (Content Disarm & Reconstruction)
- ❌ File encryption
- ❌ File hashing
- ❌ Signed URLs
- ❌ File downloads
- ❌ File sharing
- ❌ File access-control rules beyond ownership
- ❌ Celery tasks
- ❌ Redis processing
- ❌ Audit logging
- ❌ Content inspection
- ❌ Image/document processing

---

# Phase A.2 — Remove Unsafe Default Admin Credentials

This phase removes the unsafe hardcoded default admin credentials from the
seed process. Admin credentials must now come from environment variables, and
the seed command fails clearly if they are missing instead of silently creating
an admin with an insecure default password. No models, migrations, auth logic,
routes, or UI were changed.

## 1. Previous Insecure Behavior

- `app/models/seed.py` read admin credentials with hardcoded development
  fallbacks:
  - `SEED_ADMIN_USERNAME` → `"admin"`
  - `SEED_ADMIN_EMAIL` → `"admin@vaultx.local"`
  - `SEED_ADMIN_PASSWORD` → `"admin-dev-password"`
- The demo user had similar hardcoded fallbacks (`demo` / `demo-dev-password`).
- If the environment variables were unset, `flask seed` would silently create
  an admin with the well-known password `admin-dev-password`.

## 2. New Credential Behavior

- **Admin credentials are REQUIRED** from the environment. There are no
  defaults.
- If any of `SEED_ADMIN_USERNAME`, `SEED_ADMIN_EMAIL`, or
  `SEED_ADMIN_PASSWORD` is missing, `seed_users()` raises a
  `SeedConfigurationError` (a `RuntimeError` subclass) with a clear message
  naming the missing variable(s).
- The old password `admin-dev-password` is **never** used as a fallback.
- No predictable password is generated.
- Passwords are never printed, logged, or stored in plaintext. They continue to
  be hashed with Argon2 via the existing `User.set_password()`.

## 3. Environment Variables

| Variable | Required | Notes |
|----------|----------|-------|
| `SEED_ADMIN_USERNAME` | **required** | Admin username |
| `SEED_ADMIN_EMAIL` | **required** | Admin email |
| `SEED_ADMIN_PASSWORD` | **required** | Admin password (Argon2-hashed) |
| `SEED_DEMO_USERNAME` | optional | Demo username |
| `SEED_DEMO_EMAIL` | optional | Demo email |
| `SEED_DEMO_PASSWORD` | optional | Demo password (Argon2-hashed) |

`.env.example` now documents these with empty values (no real secrets).

## 4. Seed Behavior

- `seed_users()` validates admin credentials first; if missing, it raises
  `SeedConfigurationError` **before** touching the database.
- The demo user is **optional**: it is created only if all three demo
  credentials are provided. If demo credentials are absent, the demo user is
  skipped (no insecure fallback).
- The admin is created with `is_admin=True`; the demo user with `is_admin=False`.

## 5. Idempotency

- Running `flask seed` multiple times does **not** create duplicate users.
- Existing users are left untouched and their passwords are **never**
  overwritten by a subsequent seed run.

## 6. Tests Added

`tests/unit/test_seed.py` (11 tests) covers:

1. Admin credentials are loaded from environment variables.
2. Missing admin password fails clearly.
3. Missing admin username fails clearly.
4. Missing admin config does not create an admin.
5. The old password `admin-dev-password` is never used as a fallback.
6. Admin password is stored only as an Argon2 hash.
7. Running the seed twice is idempotent.
8. Existing users' passwords are not overwritten.
9. Password values are not included in error messages.
10. Demo user is created when configured.
11. Demo user is skipped when not configured.

## 7. Test Results

```
148 passed in 21.58s
```

All 137 pre-existing tests still pass, plus 11 new seed tests.

## 8. Verification

- With valid env credentials, `seed_users()` creates the admin (and demo) user
  correctly; running it twice does not duplicate users.
- Admin password is stored as an Argon2 hash (`$argon2...`), never plaintext.
- With missing admin credentials, `flask seed` fails safely with a clear
  `SeedConfigurationError` and creates no admin user.
- The error message names the missing variable(s) but never includes any
  password value.

## 9. Security Improvements

- Removed the hardcoded `admin` / `admin-dev-password` fallback.
- Admin credentials are now required from the environment; missing config fails
  fast with a clear error.
- No predictable password generation; passwords remain Argon2-hashed.
- Passwords are never printed, logged, or included in error messages.

## 10. Intentionally Deferred (NOT part of this phase)

- ❌ CSRF protection
- ❌ Flask-Limiter (rate limiting)
- ❌ Flask-Talisman (security headers)
- ❌ Authentication changes
- ❌ Authorization changes
- ❌ File security features
- ❌ ClamAV
- ❌ CDR
- ❌ Encryption
- ❌ Any other security feature

---

# Module 3.5 — Magic Byte / File Signature Validation

This module adds **magic-byte / file-signature validation** to the file upload
flow. It introduces a reusable `validate_magic_bytes` helper that inspects the
file's actual leading bytes and verifies they match the declared MIME type's
signature, and integrates it into `save_uploaded_file(...)` so that uploads
whose contents do not match their declared type are rejected **before** any
physical file is written or any database record is created. This task **only**
implements magic-byte validation — no ClamAV, CDR, encryption, hashing, or
full content inspection was added.

## 1. Files Created

| File | Purpose |
|------|---------|
| `app/utils/magic.py` | Magic-byte / file-signature detection utility (`read_signature`, `SIGNATURES`) |
| `tests/unit/test_magic_validation.py` | Unit tests for `validate_magic_bytes` and its integration into the upload flow |

## 2. Files Modified

| File | Change |
|------|--------|
| `app/files/validation.py` | Added the reusable `validate_magic_bytes` helper and the `_validate_text_plain` helper |
| `app/files/services.py` | Integrated magic-byte validation into `save_uploaded_file(...)` after MIME validation, before saving |
| `app/files/__init__.py` | Updated the module docstring to reflect that magic-byte validation is now implemented (ClamAV/CDR/hashing still deferred) |
| `tests/unit/test_upload.py` | Updated upload content to valid magic-byte signatures so existing tests pass |
| `tests/unit/test_upload_validation.py` | Updated upload content to valid magic-byte signatures so existing tests pass |
| `tests/unit/test_mime_validation.py` | Updated upload content to valid magic-byte signatures so existing tests pass |

## 3. Supported Signatures

`app/utils/magic.py` defines `SIGNATURES`, a mapping of MIME type to its
expected leading bytes. Only the minimum bytes needed to identify each type are
read (at most `MAX_SIGNATURE_LENGTH = 8` bytes):

| MIME Type | Signature (hex) | Signature (text) |
|-----------|-----------------|------------------|
| `application/pdf` | `25 50 44 46` | `%PDF` |
| `image/png` | `89 50 4E 47 0D 0A 1A 0A` | `\x89PNG\r\n\x1a\n` |
| `image/jpeg` | `FF D8 FF` | `\xff\xd8\xff` |
| `text/plain` | *(none — conservative check)* | *(no magic signature)* |

`text/plain` has **no** magic signature. Instead, it is validated
conservatively: the file is rejected if its leading bytes contain a NUL byte
(`\x00`), which is a strong indicator of binary content. This is a heuristic,
not a proof of text content.

## 4. Validation Behavior

`validate_magic_bytes(file, declared_mime_type)` in `app/files/validation.py`:

- **Rejects a missing (`None`) or empty MIME type** → `"The file's MIME type is missing."`
- **Rejects a MIME type not in the allowlist** → `"The file type '{mime}' is not supported."`
- **Rejects an empty file** → `"The file is empty."`
- **For `text/plain`**: rejects content containing a NUL byte → `"The file's contents do not match the declared type 'text/plain'."`
- **For binary types**: rejects content whose leading bytes do not start with the expected signature → `"The file's contents do not match the declared type '{mime}'."`
- **Accepts** content whose leading bytes match the declared type's signature.

It returns a `ValidationResult` dataclass (`.valid`, `.error`), matching the
existing validation helpers.

`read_signature(source)` reads at most `MAX_SIGNATURE_LENGTH` bytes and
**preserves the stream position**: it records the current position, seeks to 0,
reads the signature, then restores the original position. This is safe because
`FileStorage.save()` rewinds the stream to position 0 before writing.

## 5. Upload-Flow Changes

The upload flow in `save_uploaded_file(...)` is now:

```
Receive upload
    ↓
Validate filename
    ↓
Validate size
    ↓
Validate MIME type (allowlist)
    ↓
Inspect magic bytes
    ↓
Save temporary upload
    ↓
Create File metadata
```

- Magic-byte validation happens **after** MIME allowlist validation but
  **before** the file is written, so an upload whose contents do not match its
  declared type is rejected without touching the filesystem.
- If magic-byte validation fails, **no database record is created** and **no
  physical file is left behind**.
- `File.mime_type` is **unchanged** — it still stores the **declared** (client
  supplied) MIME type, not a detected type. Magic-byte validation is a
  verification step, not a re-classification step.
- The **UUID-based physical filename is unchanged**.
- `File.status` remains `"pending"`.

## 6. Tests Added

`tests/unit/test_magic_validation.py` (21 tests):

**`validate_magic_bytes` (13 tests):**
- `test_valid_pdf_signature_accepted` — a valid PDF signature is accepted
- `test_valid_png_signature_accepted` — a valid PNG signature is accepted
- `test_valid_jpeg_signature_accepted` — a valid JPEG signature is accepted
- `test_valid_text_file_accepted` — a text file (no NUL bytes) is accepted
- `test_pdf_content_declared_as_png_rejected` — PDF content declared as `image/png` is rejected
- `test_png_content_declared_as_pdf_rejected` — PNG content declared as `application/pdf` is rejected
- `test_jpeg_content_declared_as_pdf_rejected` — JPEG content declared as `application/pdf` is rejected
- `test_random_binary_rejected_for_binary_mime` — random binary content is rejected for binary MIME types
- `test_empty_file_rejected` — an empty file is rejected
- `test_missing_mime_type_rejected` — a missing MIME type is rejected
- `test_unsupported_mime_type_rejected` — an unsupported MIME type is rejected
- `test_text_file_with_nul_byte_rejected` — a text file containing a NUL byte is rejected

**Integration into the upload flow (9 tests):**
- `test_valid_pdf_upload_accepted` — a valid PDF upload is accepted end-to-end
- `test_valid_png_upload_accepted` — a valid PNG upload is accepted end-to-end
- `test_valid_text_upload_accepted` — a valid text upload is accepted end-to-end
- `test_mismatched_content_rejected` — content that does not match the declared MIME type is rejected
- `test_rejected_magic_creates_no_file_record` — no `File` record is created
- `test_rejected_magic_leaves_no_physical_file` — no physical file remains
- `test_existing_filename_validation_still_works` — filename validation still rejects invalid filenames
- `test_existing_size_validation_still_works` — size validation still rejects oversized files
- `test_existing_mime_allowlist_still_works` — the MIME allowlist still rejects unsupported types

All tests use a **temporary upload directory** (`tmp_path`) so the real project
storage directories are never written to.

All 128 tests pass (21 new + 107 from Modules 2.1–3.4).

## 7. Security Considerations

- **The client-supplied MIME type is treated as untrusted.** Magic-byte
  validation verifies the file's actual leading bytes against the declared
  type, so a client cannot simply declare `application/pdf` while uploading
  arbitrary bytes.
- **Only the minimum bytes are read** (`MAX_SIGNATURE_LENGTH = 8`), keeping the
  check fast and avoiding loading the whole file into memory.
- **The stream position is preserved**, so the check does not interfere with
  subsequent file handling.
- **`text/plain` is handled conservatively** — a NUL byte is treated as binary
  and rejected, even though a valid text file has no magic signature.

## 8. Limitations

- **Magic-byte validation is not a full content scan.** It only inspects the
  first few bytes. A file can pass magic-byte validation while still containing
  malicious content later in the file (e.g. a polyglot file, or a PDF with an
  embedded malicious payload).
- **Signatures are not unique.** For example, `FF D8 FF` identifies a JPEG, but
  other formats could theoretically begin with the same bytes.
- **`text/plain` validation is a heuristic.** The NUL-byte check reduces false
  positives but does not prove the file is genuinely text.
- **Magic-byte validation does not detect malware.** It only verifies the file
  type matches its declared type.

## 9. Why ClamAV and CDR Are Still Required

Magic-byte validation confirms the file's **type**, not its **safety**. A file
can have a perfectly valid PDF/PNG/JPEG signature while containing a virus,
exploit, or malicious macro. ClamAV is required to scan the file's full
contents for known malware signatures, and CDR (Content Disarm &
Reconstruction) is required to strip active content (scripts, macros, embedded
objects) from otherwise-valid documents. Neither is replaced by magic-byte
validation.

## 10. What Is Intentionally Deferred to Module 3.6

- ❌ ClamAV scanning
- ❌ CDR (Content Disarm & Reconstruction)
- ❌ File encryption
- ❌ File hashing
- ❌ Signed URLs
- ❌ File downloads
- ❌ File sharing
- ❌ File access-control rules beyond ownership
- ❌ Celery tasks
- ❌ Redis processing
- ❌ Audit logging
- ❌ Content inspection
- ❌ Image/document processing

---

# Module UI-1 — Match the Provided Dashboard Design

This module recreates the visual structure and aesthetic of the provided
reference image for a professional enterprise cybersecurity/SaaS product. It
introduces a centralized design system (`app.css`), a reusable application
layout (`base.html`), and rebuilds the dashboard, upload, admin, login, and
register pages on top of that layout. This task is **UI only** — no backend
functionality was changed.

## 1. Files Created

| File | Purpose |
|------|---------|
| `app/static/css/app.css` | Centralized design-system stylesheet (design tokens, layout, components, responsive + accessibility rules) |
| `app/templates/base.html` | Reusable application layout: sidebar, top header, page content, flash messages |

## 2. Files Modified

| File | Change |
|------|--------|
| `app/templates/dashboard.html` | Rebuilt to extend `base.html` with stats cards, recent-files table, upload panel, and security pipeline |
| `app/templates/upload.html` | Rebuilt to extend `base.html` with the upload form (behavior unchanged) |
| `app/templates/admin.html` | Rebuilt to extend `base.html` (behavior unchanged) |
| `app/templates/login.html` | Rebuilt to extend `base.html` using the auth layout (behavior unchanged) |
| `app/templates/register.html` | Rebuilt to extend `base.html` using the auth layout (behavior unchanged) |

## 3. Design System

`app.css` defines a dark, enterprise cybersecurity aesthetic using CSS custom
properties (design tokens):

- **Backgrounds**: `--bg: #0a0a0c`, `--bg-card: #141419`, `--bg-sidebar: #0d0d11`
- **Borders**: `--border: #26262e`
- **Primary (brand red)**: `--primary: #e11d2e`, `--primary-bright: #ff2b3d`, `--primary-dark: #8f0f1c`, `--primary-glow: rgba(225,29,46,0.35)`
- **Text**: `--text: #e8e8ec`, `--text-muted: #9a9aa6`, `--text-faint: #6b6b76`
- **Status colors**: `--success`, `--warning`, `--danger`
- **Layout**: `--sidebar-width: 280px`, `--header-height: 72px`
- **Glow effects**: `--glow-red`, `--glow-red-soft`

## 4. Layout Structure

`base.html` provides the application shell:

```
app-shell
├── sidebar (brand, nav sections: Main / Security / System, storage meter)
└── app-main
    ├── top-header (page title/subtitle, search box, notifications, avatar)
    └── page-content (flash messages + block content)
```

- The sidebar is overridden to be empty on auth pages (login/register).
- The header is overridden to be empty on auth pages.
- `body.auth-page` removes the sidebar margin so the auth card centers correctly.

## 5. Components Created

- **Sidebar**: brand logo, nav sections, active-state highlighting, storage meter with `role="progressbar"`.
- **Top header**: page title/subtitle, search box, notification button, user avatar.
- **Stats grid**: three stat cards (Total Files, Storage Used, Security Status).
- **Data table**: recent-files table with file-type icons, status badges, and action buttons.
- **Upload panel**: drop-zone with icon, "Choose File" label, hidden file input, submit button.
- **Security pipeline**: 9-step vertical pipeline (Upload → Filename Validation → Size Validation → MIME Check → Magic Bytes → Malware Scan (ClamAV) → CDR → Encryption → Secure Storage), with implemented/planned states.
- **Auth card**: centered login/register card with brand, heading, and form.

## 6. Responsive Behavior

- **≤ 1100px**: dashboard grid and stats grid collapse to a single column.
- **≤ 900px**: sidebar becomes off-canvas (slides out), main content takes full width.
- **≤ 600px**: header subtitle and search box hide; stats grid stays single column.

## 7. Accessibility

- `:focus-visible` outlines on interactive elements.
- `.sr-only` class for screen-reader-only labels.
- `role="progressbar"` with `aria-valuenow/min/max` on the storage meter.
- Inline SVG icons use `aria-hidden="true"`; interactive icon buttons carry `aria-label`s.
- Semantic HTML: `<nav>`, `<main>`, `<header>`, `<aside>`, `<table>` with `<th scope>`.

## 8. Placeholder Data Used

The dashboard uses **presentation/demo values only** — no database queries were
added:

- Total Files: 12 (+2 this week)
- Storage Used: 2.4 GB of 10 GB
- Security Status: CLEAN
- Recent files table: 3 placeholder rows (report.pdf CLEAN, image.png SCANNING, document.pdf QUARANTINED)
- Storage meter: 2.4 GB / 10 GB, 24% used

## 9. Backend Functionality Intentionally Not Changed

Per the module scope, the following were **not** modified:

- ❌ SQLAlchemy models
- ❌ Alembic migrations
- ❌ Authentication logic
- ❌ Session logic
- ❌ Authorization logic
- ❌ File upload security
- ❌ Filename validation
- ❌ File-size validation
- ❌ MIME validation
- ❌ Magic-byte validation
- ❌ Database schema
- ❌ Security functionality

No React/Vue/Bootstrap/Tailwind/npm/frontend build systems were introduced. The
existing Flask + Jinja + CSS architecture is preserved.

## 10. Tests Performed

- Ran the full test suite: **128 tests passed**.
- Verified login, registration, dashboard access, admin protection, and upload
  flows still render correctly with the new templates.
- Confirmed the dashboard still displays the authenticated user's username and
  email (asserted by `test_auth_session.py`).
- Confirmed the admin dashboard still displays "Admin Dashboard" and the admin
  username (asserted by `test_auth_admin.py`).
- Confirmed upload success/error flash messages still render (asserted by the
  upload, MIME, and magic-byte validation tests).

---

# Phase A.3 — CSRF Protection

This phase adds **Cross-Site Request Forgery (CSRF) protection** to VaultX.
State-changing POST requests (registration, login, and file upload) now require
a valid CSRF token. The protection is enabled globally via Flask-WTF's
`CSRFProtect` and is **not** disabled in debug or test mode. No models,
migrations, auth logic, routes, or UI behavior were changed beyond adding the
hidden CSRF token fields to the three forms.

## 1. Library Chosen

- **Flask-WTF 1.2.1** (`flask_wtf.csrf.CSRFProtect`) was added to
  `requirements.txt`.
- **Why Flask-WTF**: it is the de-facto standard, well-maintained CSRF
  implementation for Flask. It uses `itsdangerous` signed tokens with a
  timestamp and a per-session random hash, and it validates tokens on every
  POST request automatically. No custom crypto was written.

## 2. Files Created

| File | Purpose |
|------|---------|
| `tests/unit/test_csrf.py` | Focused CSRF tests (9 tests) covering registration, login, and upload with valid / missing / invalid tokens |

## 3. Files Modified

| File | Change |
|------|--------|
| `requirements.txt` | Added `Flask-WTF==1.2.1` |
| `extensions.py` | Added `csrf = CSRFProtect()` |
| `app/__init__.py` | `csrf.init_app(app)` in `initialize_extensions()` |
| `config.py` | Added CSRF configuration settings |
| `app/templates/login.html` | Added hidden `csrf_token` input |
| `app/templates/register.html` | Added hidden `csrf_token` input |
| `app/templates/upload.html` | Added hidden `csrf_token` input |
| `tests/conftest.py` | Added `csrf_token` fixture; removed `WTF_CSRF_ENABLED = False` from `TestConfig` |
| 8 existing test files | Updated POST helpers to supply valid CSRF tokens |

## 4. Configuration Added

`config.py` now defines:

| Setting | Value | Notes |
|---------|-------|-------|
| `WTF_CSRF_ENABLED` | `True` | CSRF protection is always on |
| `WTF_CSRF_TIME_LIMIT` | `3600` (env-overridable via `WTF_CSRF_TIME_LIMIT`) | Token validity window in seconds |
| `WTF_CSRF_SSL_STRICT` | `True` | Referrer check enforced over HTTPS |
| `WTF_CSRF_FIELD_NAME` | `"csrf_token"` | Form field name |

## 5. Forms Protected

- **Registration** (`/register`) — `app/templates/register.html`
- **Login** (`/login`) — `app/templates/login.html`
- **File upload** (`/files/upload`) — `app/templates/upload.html`

Each form now includes:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

## 6. Failure Behavior

- A POST **without** a CSRF token → **HTTP 400** (Bad Request).
- A POST **with an invalid** CSRF token → **HTTP 400** (Bad Request).
- A POST **with an expired** token → **HTTP 400** (Bad Request).
- No database record is created and no physical file is written when a request
  is rejected (verified by tests).

## 7. Test Strategy

CSRF protection is **intentionally left enabled** during tests. Rather than
disabling it, the test suite supplies valid tokens via a `csrf_token` fixture.
This exercises the real-world behavior.

The `csrf_token` fixture works as follows:

- `generate_csrf()` stores a **raw** random hash in the session and returns a
  **signed** token (raw hash + timestamp + signature).
- `CSRFProtect.validate_csrf()` deserializes the submitted signed token and
  compares it to the raw hash stored in the session.
- The fixture captures both values: it returns the signed token for use in POST
  data, and persists the raw hash into the test client's session cookie so
  validation passes.

## 8. Tests Added

`tests/unit/test_csrf.py` (9 tests):

1. `test_register_with_valid_csrf_token_succeeds`
2. `test_register_without_csrf_token_rejected`
3. `test_register_with_invalid_csrf_token_rejected`
4. `test_login_with_valid_csrf_token_succeeds`
5. `test_login_without_csrf_token_rejected`
6. `test_login_with_invalid_csrf_token_rejected`
7. `test_upload_with_valid_csrf_token_succeeds`
8. `test_upload_without_csrf_token_rejected`
9. `test_upload_with_invalid_csrf_token_rejected`

The rejection tests also assert that **no** `File` record is created and **no**
physical file is written when a request is rejected.

## 9. Existing Tests Updated

8 existing test files were updated so their POST helpers supply a valid CSRF
token (via the `csrf_token` fixture):

- `tests/unit/test_auth_login.py`
- `tests/unit/test_auth_register.py`
- `tests/unit/test_auth_session.py`
- `tests/unit/test_auth_admin.py`
- `tests/unit/test_upload.py`
- `tests/unit/test_magic_validation.py`
- `tests/unit/test_mime_validation.py`
- `tests/unit/test_upload_validation.py`

One existing assertion in `test_auth_session.py`
(`test_session_contains_only_user_identifier`) was updated to allow the
`csrf_token` key in the session, since Flask-WTF now stores the raw token there
for validation. This is expected and not sensitive user data.

## 10. Test Results

```
157 passed in 49.98s
```

All 148 pre-existing tests still pass, plus 9 new CSRF tests.

## 11. Security Considerations

- CSRF protection is **enabled globally** and is **not** disabled in debug or
  test mode.
- Tokens are signed with `itsdangerous` (timestamped) and bound to the user's
  session, so they cannot be forged without the `SECRET_KEY`.
- `WTF_CSRF_SSL_STRICT = True` enforces the referrer check over HTTPS.
- The token is stored in the session (not a cookie), so it is not exposed to
  JavaScript and is resistant to cookie-based CSRF attacks.

## 12. Intentionally Deferred (NOT part of this phase)

- ❌ Flask-Limiter (rate limiting)
- ❌ Flask-Talisman (security headers / CSP)
- ❌ SameSite cookie hardening beyond existing session config
- ❌ Authentication changes
- ❌ Authorization changes
- ❌ File security features
- ❌ ClamAV
- ❌ CDR
- ❌ Encryption
- ❌ Any other security feature
