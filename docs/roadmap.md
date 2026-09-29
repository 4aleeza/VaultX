# SecureVault - Roadmap

This document tracks the planned development roadmap for SecureVault.

> **Status**: This is a living document and will be updated as work progresses.

---

## Phase 1 — Foundation (COMPLETE)

- [x] Flask Application Factory pattern
- [x] Modular project structure
- [x] Configuration via environment variables (python-dotenv)
- [x] SQLAlchemy, Alembic, Redis, Celery initial configuration
- [x] Docker Compose (Flask, PostgreSQL, Redis)
- [x] Health check endpoint (`GET /health`)
- [x] Storage directory structure
- [x] Audit package structure
- [x] Utils package structure
- [x] Docs and test scaffolding

---

## Phase 2 — Authentication

- [ ] User model and database migration
- [ ] Registration / login / logout
- [ ] Password hashing (`utils/hashing.py`)
- [ ] Session and token management
- [ ] Role-based access control
- [ ] Audit logging of auth events

---

## Phase 3 — File Storage

- [ ] File upload / download endpoints
- [ ] Metadata storage in PostgreSQL
- [ ] File storage on disk (UUID/hash naming, sharded layout)
- [ ] MIME / magic-byte validation
- [ ] Quarantine of suspicious files
- [ ] Audit logging of file events

---

## Phase 4 — Encryption

- [ ] Encryption at rest (`utils/encryption.py`)
- [ ] Per-file key management
- [ ] Secure key storage

---

## Phase 5 — Background Processing

- [ ] Celery tasks for encryption / scanning
- [ ] Async upload processing
- [ ] Cleanup of `storage/temp/`

---

## Phase 6 — Hardening

- [ ] Rate limiting
- [ ] Security headers
- [ ] Comprehensive security test suite
- [ ] Production configuration classes
