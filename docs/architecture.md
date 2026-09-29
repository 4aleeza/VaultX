# SecureVault - Architecture

This document describes the intended architecture of the SecureVault platform.
It is written for developers working on the codebase.

> **Status**: This is a living document. It describes the target architecture
> and will be updated as features are implemented.

---

## Overview

SecureVault is a secure file storage platform. Users upload files that are
encrypted at rest and stored on disk, while metadata is stored in PostgreSQL.
Background processing (encryption, scanning) is handled by Celery workers.

---

## High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                         Clients                              │
│                    (Web / API consumers)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────────┐
│                        Flask App                             │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐  │
│  │  auth  │ │ files  │ │ audit  │ │ health │ │   utils    │  │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────────┘  │
└───────┬──────────────────┬──────────────────┬────────────────┘
        │                  │                  │
        │ SQLAlchemy       │ Redis            │ Celery
┌───────▼───────┐  ┌───────▼───────┐  ┌───────▼───────────────┐
│  PostgreSQL   │  │    Redis      │  │   Celery Workers      │
│  (metadata)   │  │ (cache/broker)│  │  (encryption, scan)   │
└───────────────┘  └───────────────┘  └───────────┬───────────┘
                                                  │
                                          ┌───────▼───────────┐
                                          │  Storage (disk)   │
                                          │  encrypted files  │
                                          └───────────────────┘
```

---

## Feature-Owned Services

Each feature owns its business logic in a `services.py` module (or a
`services/` sub-package if the feature grows large). There is **no** shared
top-level `services` package.

```
app/
    auth/
        services.py
    files/
        services.py
    audit/
        services.py
    security/            # (future) security-specific services
```

This scales better than a single shared services layer because each feature
can evolve independently.

---

## Storage Architecture

- **Metadata** is stored in **PostgreSQL** (file name, size, MIME type, owner,
  encryption key reference, timestamps, etc.).
- **File contents** are stored **on disk** under `storage/encrypted/`.
- Files are **never** saved with their original names. They are saved using a
  UUID or content hash, sharded by a prefix:

```
storage/
    encrypted/
        2f/
            2f3a95b8.enc
        1a/
            1a7e3f91.enc
```

The sharding prefix (first two hex chars of the UUID/hash) prevents a single
directory from containing too many files.

### Storage Directories

| Directory       | Purpose                                                        |
|-----------------|----------------------------------------------------------------|
| `uploads/`      | Files being uploaded but not yet processed                     |
| `encrypted/`    | Encrypted files at rest (sharded by hash/UUID prefix)          |
| `quarantine/`   | Files flagged as suspicious/malicious, isolated from serving   |
| `temp/`         | Temporary files during processing (cleaned up after)           |

All storage directories are mounted inside Docker via volumes.

---

## Audit

A dedicated `audit` package records security-relevant events. Every feature
depends on it to log events such as logins, file access, permission changes,
and suspicious activity.

```
app/
    audit/
        models.py    # Audit log database models
        services.py  # Business logic for recording/querying events
        logger.py    # Structured logging helpers
```

---

## Utilities

Shared, single-purpose helper modules live in `app/utils/`:

```
app/
    utils/
        hashing.py      # Password/content hashing
        encryption.py   # Symmetric/asymmetric encryption
        validators.py   # Input validation
        mime.py         # MIME type detection
        magic.py        # Magic-byte / file signature detection
        tokens.py       # Token generation/verification
```

---

## Testing

Tests are split by scope:

```
tests/
    unit/          # Isolated unit tests
    integration/   # Tests exercising multiple components
    security/      # Security-focused tests
```

Security tests cover scenarios such as:
- Uploading an executable renamed to a PDF
- Using an expired download token
- Presenting an invalid signature
- Accessing another user's file
