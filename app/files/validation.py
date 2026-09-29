"""
SecureVault - Files Validation
==============================

Reusable validation helpers for the file storage feature.

This module validates **metadata** (filename, size, MIME type) and **file
signatures** (magic bytes). It does NOT perform ClamAV scanning, CDR, or any
content inspection — those are deferred to later modules.

The original filename is treated as **untrusted input**. It is never used as
the physical storage filename and never concatenated into a filesystem path.

The MIME type supplied by the client/browser is also treated as **untrusted**.
``validate_mime_type`` is an **allowlist check only**: it verifies that the
declared MIME type is in the configured allowlist. It does NOT prove that the
file's actual contents match the declared MIME type.

``validate_magic_bytes`` inspects the file's **actual bytes** and compares the
detected signature with the declared MIME type. This is stronger than trusting
the ``Content-Type``, but it is NOT a complete security solution: it does NOT
detect malware and does NOT replace ClamAV or CDR.
"""

from __future__ import annotations

from dataclasses import dataclass

from flask import current_app

from app.utils.magic import SIGNATURES, read_signature


@dataclass
class ValidationResult:
    """
    Result of a validation check.

    Attributes:
        valid: Whether the value passed validation.
        error: A human-readable error message when invalid, else ``None``.
    """

    valid: bool
    error: str | None = None


def validate_original_filename(filename: str | None) -> ValidationResult:
    """
    Validate an original (user-supplied) filename.

    The filename is treated as untrusted input. It is rejected if it is empty,
    too long, or contains path separators (which could enable path traversal).
    Both Windows (``\\``) and Linux/Unix (``/``) separators are rejected.

    Args:
        filename: The original filename supplied by the user.

    Returns:
        A ``ValidationResult`` describing whether the filename is acceptable.
    """
    if filename is None or not filename.strip():
        return ValidationResult(valid=False, error="The filename cannot be empty.")

    max_length = current_app.config["MAX_FILENAME_LENGTH"]
    if len(filename) > max_length:
        return ValidationResult(
            valid=False,
            error=f"The filename is too long (maximum {max_length} characters).",
        )

    # Reject path separators on both Windows and Linux/Unix. This prevents
    # path-traversal attempts such as "../../secret.txt" or "..\\..\\secret.txt".
    if "/" in filename or "\\" in filename:
        return ValidationResult(
            valid=False,
            error="The filename must not contain path separators.",
        )

    return ValidationResult(valid=True)


def validate_file_size(size: int | None) -> ValidationResult:
    """
    Validate an uploaded file's size.

    Rejects zero-byte files and files larger than ``MAX_UPLOAD_SIZE``. The
    size is measured from the actual uploaded bytes, never trusted from the
    client.

    Args:
        size: The measured size of the uploaded file in bytes.

    Returns:
        A ``ValidationResult`` describing whether the size is acceptable.
    """
    if size is None or size <= 0:
        return ValidationResult(valid=False, error="The file is empty.")

    max_size = current_app.config["MAX_UPLOAD_SIZE"]
    if size > max_size:
        max_mb = max_size / (1024 * 1024)
        return ValidationResult(
            valid=False,
            error=f"The file exceeds the maximum upload size of {max_mb:.0f} MB.",
        )

    return ValidationResult(valid=True)


def validate_mime_type(mime_type: str | None) -> ValidationResult:
    """
    Validate a declared MIME type against the configured allowlist.

    The MIME type is treated as **untrusted input** supplied by the
    client/browser. This is an **allowlist check only**: it verifies that the
    declared MIME type is present in ``SUPPORTED_MIME_TYPES``. It does NOT
    prove that the file's actual contents match the declared MIME type —
    magic-byte validation is implemented separately (Module 3.5).

    The check is case-consistent: both the declared MIME type and the
    allowlist are normalized to lowercase before comparison, so
    ``"Application/PDF"`` and ``"application/pdf"`` are treated identically.

    Args:
        mime_type: The MIME type declared by the client/browser.

    Returns:
        A ``ValidationResult`` describing whether the MIME type is acceptable.
    """
    if mime_type is None or not mime_type.strip():
        return ValidationResult(
            valid=False,
            error="The file's MIME type is missing.",
        )

    normalized = mime_type.strip().lower()
    supported = current_app.config["SUPPORTED_MIME_TYPES"]

    if normalized not in supported:
        return ValidationResult(
            valid=False,
            error=f"The file type '{mime_type}' is not supported.",
        )

    return ValidationResult(valid=True)


def _validate_text_plain(signature: bytes) -> ValidationResult:
    """
    Conservatively validate a ``text/plain`` file.

    Plain text has **no universal magic-byte signature**, so this check cannot
    prove that a file is text. Instead, it applies a conservative heuristic:
    files whose leading bytes contain a NUL byte (``\\x00``) are rejected,
    because NUL bytes strongly indicate binary content.

    This is **NOT** proof that the file is text — it only rejects files that
    are clearly not plain text. It is intentionally conservative and does not
    claim that magic bytes prove the file is text.

    Args:
        signature: The leading bytes read from the file.

    Returns:
        A ``ValidationResult`` describing whether the file can reasonably be
        treated as plain text.
    """
    if b"\x00" in signature:
        return ValidationResult(
            valid=False,
            error="The file's contents do not match the declared type 'text/plain'.",
        )

    return ValidationResult(valid=True)


def validate_magic_bytes(file, declared_mime_type: str | None) -> ValidationResult:
    """
    Validate that a file's actual magic bytes are consistent with the declared
    MIME type.

    This inspects the file's **actual bytes** (via ``read_signature``) and
    compares the detected signature with the declared MIME type. It reads only
    the minimum number of bytes needed to identify a supported signature and
    never loads the entire file into memory. For a file-like object, the stream
    position is preserved.

    The declared MIME type and the detected signature are **compared**. If they
    disagree, the file is rejected — the MIME type is never silently "fixed" to
    whatever the signature detector discovers.

    ``text/plain`` is handled separately: it has no universal magic-byte
    signature, so a conservative heuristic is applied instead (see
    ``_validate_text_plain``).

    Magic-byte validation is **stronger** than trusting the client-supplied
    ``Content-Type``, but it is **NOT** a complete security solution. It does
    NOT detect malware and does NOT replace ClamAV or CDR.

    Args:
        file: A file-like object (e.g. ``upload.stream``) or a filesystem path.
        declared_mime_type: The MIME type declared by the client/browser.

    Returns:
        A ``ValidationResult`` describing whether the file's signature is
        consistent with the declared MIME type.
    """
    # Reject a missing declared MIME type.
    if declared_mime_type is None or not declared_mime_type.strip():
        return ValidationResult(
            valid=False,
            error="The file's MIME type is missing.",
        )

    normalized = declared_mime_type.strip().lower()

    # Reject unsupported MIME types.
    supported = current_app.config["SUPPORTED_MIME_TYPES"]
    if normalized not in supported:
        return ValidationResult(
            valid=False,
            error=f"The file type '{declared_mime_type}' is not supported.",
        )

    # Read the leading bytes of the file (minimum necessary, never the whole
    # file). The stream position is preserved by read_signature.
    signature = read_signature(file)

    # Reject an empty file.
    if not signature:
        return ValidationResult(valid=False, error="The file is empty.")

    # text/plain has no universal magic-byte signature; use a conservative
    # heuristic instead of pretending a magic signature exists.
    if normalized == "text/plain":
        return _validate_text_plain(signature)

    # Compare the detected signature with the declared MIME type. The declared
    # MIME type is never changed to match the detected signature.
    expected = SIGNATURES[normalized]
    if not signature.startswith(expected):
        return ValidationResult(
            valid=False,
            error=(
                "The file's contents do not match the declared type "
                f"'{declared_mime_type}'."
            ),
        )

    return ValidationResult(valid=True)
