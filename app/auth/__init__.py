"""
SecureVault - Auth Module
=========================

Authentication feature package.

This module currently implements user registration. Login, logout, session
management, and role-based access control are deferred to later modules.
"""

from flask import Blueprint, flash, redirect, render_template, request

from app.auth.services import register_user

# Blueprint for all authentication routes.
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Handle user registration.

    GET: Render the registration form.
    POST: Validate input, create the user, and redirect to login on success.
    """
    if request.method == "POST":
        result = register_user(
            username=request.form.get("username"),
            email=request.form.get("email"),
            password=request.form.get("password"),
            confirm_password=request.form.get("confirm_password"),
        )

        if result.success:
            flash("Registration successful. Please log in.", "success")
            # The /login route does not exist yet; it is implemented in the
            # next module. Redirect to the literal URL for now.
            return redirect("/login")

        # On failure, flash each error and redisplay the form.
        for error in result.errors:
            flash(error, "error")

        # Preserve username and email; never preserve passwords.
        return render_template(
            "register.html",
            username=request.form.get("username", ""),
            email=request.form.get("email", ""),
        )

    # GET request: render an empty registration form.
    return render_template("register.html", username="", email="")

