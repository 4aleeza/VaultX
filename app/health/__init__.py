"""
SecureVault - Health Check Blueprint
====================================

Provides a simple health check endpoint used by Docker Compose and monitoring
tools to verify the application is running and responsive.
"""

from flask import Blueprint, jsonify


# Blueprint for health-related routes.
health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint.

    Returns a simple JSON payload indicating the service is healthy. This is
    used by Docker Compose healthchecks and external monitoring systems.

    Returns:
        A JSON response: {"status": "ok"}
    """
    return jsonify({"status": "ok"}), 200
