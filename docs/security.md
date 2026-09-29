# SecureVault - Security

This document outlines the security model and hardening plans for SecureVault.
It is written for developers.

> **Status**: This is a living document. Security features are planned but not
> yet implemented.

---

## Principles

1. **Encrypt at rest** — All stored files are encrypted before being written
   to disk.
2. **Never trust filenames** — Files are stored by UUID/hash, never by their
   original name. Original names live only in metadata.
3. **Validate content, not just extensions** — Detect file type by magic bytes,
   not by the file extension, to catch renamed executables.
4. **Isolate suspicious files** — Files that fail validation are moved to
   `storage/quarantine/` and never served.
5. **Audit everything** — Security-relevant events are recorded via the
   `audit` package.
6. **Least privilege** — Users can only access their own files.

---

## Planned Security Features

### File Validation
- MIME type detection via magic bytes (`utils/magic.py`).
- Reject executables and scripts even if renamed to look like documents.
- Quarantine suspicious files.

### Encryption
- Symmetric encryption for file contents at rest (`utils/encryption.py`).
- Per-file encryption keys, stored securely (key management TBD).

### Tokens
- Signed, expiring download tokens (`utils/tokens.py`).
- Tokens are bound to a specific file and user.

### Access Control
- Users can only access their own files.
- Sharing (if added) uses explicit, revocable grants.

### Rate Limiting
- Protect authentication and download endpoints from abuse.

### Security Headers
- Apply standard security headers (CSP, X-Frame-Options, etc.).

---

## Security Test Scenarios

The `tests/security/` suite will cover:

| Scenario | Expected behavior |
|----------|-------------------|
| Upload executable renamed to PDF | Rejected / quarantined |
| Expired download token | Request denied |
| Invalid signature | Request denied |
| Access another user's file | Request denied (403) |
