"""
SecureVault - Audit Package
===========================

Dedicated package for audit logging and security event tracking.

Every module in the application will use this package to record security-relevant
events (logins, file access, permission changes, suspicious activity, etc.).

This package will contain:
    - models.py   : Audit log database models
    - services.py : Business logic for recording and querying audit events
    - logger.py   : Structured logging helpers for audit events

No audit functionality is implemented yet; this establishes the package
structure so all features can depend on it consistently.
"""
