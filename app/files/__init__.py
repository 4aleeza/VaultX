"""
SecureVault - Files Module
==========================

File storage feature package.

This module implements the basic authenticated file-upload flow:
    - ``GET /files/upload`` renders a minimal upload page.
    - ``POST /files/upload`` accepts a multipart upload, validates the
      filename, size, declared MIME type, and magic bytes, stores the file in
      the temporary upload area, and creates a ``File`` metadata record.

The declared MIME type is validated against a configured allowlist, and the
file's actual bytes are inspected to confirm the signature is consistent with
the declared MIME type. Magic-byte validation is stronger than trusting the
``Content-Type`` but is NOT a complete security solution. Content security
validation (ClamAV, CDR, hashing, etc.) is intentionally deferred to later
modules. Uploaded files are placed in the temporary upload area with status
``"pending"`` and are never described as "safe", "clean", or "validated".
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.auth.session import get_current_user, login_required
from app.files.services import save_uploaded_file

# Blueprint for all file routes.
files_bp = Blueprint("files", __name__, url_prefix="/files")


@files_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    """
    Handle file upload.

    GET: Render the minimal upload form.
    POST: Store the uploaded file in the temporary upload area and create its
    metadata record. The route stays thin and delegates to the service layer.
    """
    if request.method == "POST":
        # The owner is the currently authenticated user, never a client-supplied
        # value.
        user = get_current_user()
        upload_file = request.files.get("file")

        result = save_uploaded_file(upload_file, owner_id=user.id)

        if result.success:
            flash("File uploaded successfully.", "success")
        else:
            flash(result.error or "Upload failed.", "error")

        return redirect(url_for("files.upload"))

    # GET request: render the upload form.
    return render_template("upload.html")
