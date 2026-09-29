"""
SecureVault - Files Services
============================

Business logic for the file storage feature.

This module implements the basic authenticated file-upload flow with upload
metadata, file-size, MIME-type, and magic-byte validation. The uploaded file is
placed into the temporary upload area **without** any content security
validation (ClamAV, CDR, hashing, etc.) — those are deferred to later modules.
The file is therefore never described as "safe", "clean", or "validated"; its
database status is set to ``"pending"``.

The user-supplied filename is treated as **untrusted input**. It is validated
(empty, length, path separators) but never used as the physical storage
filename and never concatenated into a filesystem path. A cryptographically
random internal filename (UUID) is generated instead, and the original filename
is preserved only as database metadata.

The MIME type supplied by the client/browser is also treated as **untrusted**.
It is checked against the configured allowlist (``validate_mime_type``) and its
actual bytes are inspected (``validate_magic_bytes``). Magic-byte validation is
stronger than trusting the ``Content-Type`` but is NOT a complete security
solution — it does NOT detect malware and does NOT replace ClamAV or CDR.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from flask import current_app
from werkzeug.datastructures import FileStorage

from app.files.validation import (
    validate_file_size,
    validate_magic_bytes,
    validate_mime_type,
    validate_original_filename,
)
from app.models.file import File
from extensions import db


@dataclass
class UploadResult:
    """
    Result of a file-upload attempt.

    Attributes:
        success: Whether the upload succeeded.
        file: The created ``File`` record on success, else ``None``.
        error: A human-readable error message on failure, else ``None``.
    """

    success: bool
    file: File | None = None
    error: str | None = None


def _measure_stream_size(upload: FileStorage) -> int:
    """
    Measure the actual size of an uploaded file's stream.

    Seeks to the end of the stream to determine its length, then restores the
    position to the start so the stream can be saved. The size is measured from
    the actual bytes, never trusted from the client.

    Args:
        upload: The uploaded file.

    Returns:
        The size of the stream in bytes.
    """
    stream = upload.stream
    current = stream.tell()
    stream.seek(0, 2)  # Seek to end.
    size = stream.tell()
    stream.seek(current)  # Restore original position.
    return size


def save_uploaded_file(
    upload: FileStorage,
    owner_id: uuid.UUID,
) -> UploadResult:
    """
    Persist an uploaded file to the temporary upload area and create its
    metadata record.

    The upload flow is:

        Receive upload
            ↓
        Validate filename
            ↓
        Validate size
            ↓
        Validate declared MIME type
            ↓
        Inspect magic bytes
            ↓
        Save temporary upload
            ↓
        Create File metadata

    The uploaded bytes are written to ``UPLOAD_FOLDER`` under a
    cryptographically random internal filename. The user-supplied filename is
    stored only as metadata on the ``File`` record. The MIME type declared by
    the client is validated against the configured allowlist, and the file's
    actual bytes are inspected to confirm the signature is consistent with the
    declared MIME type. Magic-byte validation is stronger than trusting the
    ``Content-Type`` but is NOT a complete security solution (ClamAV/CDR are
    deferred to later modules). The record's status is set to ``"pending"``.

    If validation fails, no database record is created and no physical file is
    left behind. If the database commit fails, the transaction is rolled back
    and the physical upload file is removed so no orphaned file is left behind.

    Args:
        upload: The uploaded file (from ``request.files``).
        owner_id: The authenticated user's ID (never taken from the client).

    Returns:
        An ``UploadResult`` describing the outcome.
    """
    # Verify a file was actually supplied.
    if upload is None or not upload.filename:
        return UploadResult(success=False, error="No file was supplied.")

    original_filename = upload.filename

    # Validate the original filename (empty, length, path separators).
    filename_result = validate_original_filename(original_filename)
    if not filename_result.valid:
        return UploadResult(success=False, error=filename_result.error)

    # Measure the actual uploaded size and validate it (zero-byte and
    # MAX_UPLOAD_SIZE). The size is measured from the stream, never trusted
    # from the client.
    file_size = _measure_stream_size(upload)
    size_result = validate_file_size(file_size)
    if not size_result.valid:
        return UploadResult(success=False, error=size_result.error)

    # Validate the MIME type declared by the client/browser against the
    # configured allowlist. The declared MIME type is UNTRUSTED: this is an
    # allowlist check only and does NOT prove the file's actual contents.
    mime_type = upload.mimetype
    mime_result = validate_mime_type(mime_type)
    if not mime_result.valid:
        return UploadResult(success=False, error=mime_result.error)

    # Inspect the file's actual bytes (magic bytes) and verify the detected
    # signature is consistent with the declared MIME type. This happens BEFORE
    # the file is accepted into the upload storage area. The declared MIME type
    # is never changed to match the detected signature — a mismatch is rejected.
    magic_result = validate_magic_bytes(upload.stream, mime_type)
    if not magic_result.valid:
        return UploadResult(success=False, error=magic_result.error)

    # Generate a cryptographically random internal filename. The user-supplied
    # filename is never used as the physical filename, so path-traversal
    # attempts (e.g. "../../secret.txt") cannot determine the storage location.
    stored_filename = str(uuid.uuid4())

    # Resolve the upload directory and ensure it exists.
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)

    # The storage path is the relative path from the project root to the file.
    # It is derived from the generated internal filename, never from the
    # user-supplied filename.
    storage_path = str(Path("storage") / "uploads" / stored_filename)

    # Write the uploaded bytes to the temporary upload area.
    physical_path = upload_dir / stored_filename
    upload.save(physical_path)

    # Create the File metadata record. The validated MIME type is stored; the
    # UUID-based physical filename is unchanged and the status stays "pending".
    file_record = File(
        owner_id=owner_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        storage_path=storage_path,
        file_size=file_size,
        mime_type=mime_type,
        file_hash=None,
        status="pending",
    )

    try:
        db.session.add(file_record)
        db.session.commit()
    except Exception:
        # Roll back the transaction and remove the physical file so no
        # orphaned upload is left behind.
        db.session.rollback()
        try:
            physical_path.unlink(missing_ok=True)
        except OSError:
            pass
        return UploadResult(
            success=False,
            error="The file could not be stored. Please try again.",
        )

    return UploadResult(success=True, file=file_record)
