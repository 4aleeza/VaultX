"""
SecureVault - Application Entry Point
=====================================

This module is the entry point for running the SecureVault application.

It creates the Flask application via the application factory and runs the
development server. In production, a WSGI server (e.g. Gunicorn) should be
used instead of the built-in development server.
"""

import os

from app import create_app
from config import Config


# Create the application instance using the base configuration.
app = create_app(Config)


if __name__ == "__main__":
    # Read host and port from environment variables with sensible defaults.
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", "5000"))

    # Run the development server.
    app.run(host=host, port=port, debug=app.config["DEBUG"])
