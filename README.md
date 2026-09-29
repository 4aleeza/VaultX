# VaultX 

VaultX is a security-focused Flask web application designed for authenticated and controlled file uploads. It combines user authentication, role-based access control, upload validation, and security protections to provide a foundation for securely managing user-submitted files.

##  Key Features

- User registration, login, and logout
- Admin-only access controls
- Secure password hashing using Argon2
- CSRF protection
- Redis-backed login attempt tracking and account lockouts
- Request rate limiting
- Authenticated file uploads
- File size and MIME-type validation
- Magic-byte/file-signature verification
- UUID-based file naming
- Database-backed file ownership and metadata tracking
- Application health-check endpoint
- Dockerized development/deployment environment

##  Tech Stack

- **Backend:** Python 3.12, Flask
- **Frontend:** Jinja2, HTML, CSS, JavaScript
- **Database:** PostgreSQL
- **ORM & Migrations:** SQLAlchemy, Flask-Migrate, Alembic
- **Caching / Rate Limiting:** Redis
- **Security:** Argon2, Flask-WTF, Flask-Limiter
- **Server:** Gunicorn
- **Containerization:** Docker & Docker Compose
- **Testing:** pytest
- **Task Queue Infrastructure:** Celery

##  Project Status

VaultX is currently under active development. The core authentication and secure upload workflow is implemented, while additional security-focused functionality such as malware scanning, encrypted file storage, secure downloads, and audit logging is planned for future development.
