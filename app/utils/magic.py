"""
SecureVault - Magic Byte Utilities
==================================

Magic-byte / file signature detection helpers.

This module inspects the **actual bytes** of a file to determine whether its
signature is consistent with a declared MIME type. It reads only the minimum
number of bytes needed to identify the supported signatures and never loads the
entire file into memory.

Magic-byte detection is **stronger** than trusting the client-supplied
``Content-Type``, but it is **NOT** a complete security solution:

- It does **NOT** detect malware.
- It does **NOT** replace ClamAV.
- It does **NOT** replace CDR (Content Disarm & Reconstruction).

The declared MIME type and the detected file signature are **compared**. If
they disagree, the file is rejected — the MIME type is never silently "fixed"
to whatever the signature detector discovers.
"""

from __future__ import annotations

from pathlib import Path

# Maximum number of bytes needed to identify any supported signature.
#   PDF:  4 bytes ("%PDF")
#   PNG:  8 bytes (89 50 4E 47 0D 0A 1A 0A)
#   JPEG: 3 bytes (FF D8 FF)
MAX_SIGNATURE_LENGTH = 8

# Supported file signatures (magic bytes), keyed by MIME type.
# A file is considered to match a signature if its leading bytes start with
# the signature prefix.
SIGNATURES: dict[str, bytes] = {
    "application/pdf": b"%PDF",
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
}

# text/plain has NO universal magic-byte signature. It is intentionally absent
# from SIGNATURES and is handled separately with a conservative heuristic (see
# validate_magic_bytes in app/files/validation.py). Plain text cannot be proven
# by magic bytes.


def read_signature(source) -> bytes:
    """
    Read the minimum number of bytes needed to identify a supported signature.

    Works with a file-like object (a stream with ``read``/``seek``/``tell``) or
    a filesystem path. Only the leading ``MAX_SIGNATURE_LENGTH`` bytes are
    read; the entire file is never loaded into memory.

    For a file-like object, the stream position is **preserved** so later
    processing is not unexpectedly affected.

    Args:
        source: A file-like object (e.g. ``upload.stream``) or a path.

    Returns:
        The leading bytes of the file (up to ``MAX_SIGNATURE_LENGTH`` bytes).
    """
    if isinstance(source, (str, Path)):
        with open(source, "rb") as f:
            return f.read(MAX_SIGNATURE_LENGTH)

    # File-like object: preserve the current stream position.
    current = source.tell()
    source.seek(0)
    data = source.read(MAX_SIGNATURE_LENGTH)
    source.seek(current)
    return data
