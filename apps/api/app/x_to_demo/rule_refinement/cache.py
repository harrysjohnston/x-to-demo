"""Legacy cache helpers retained for hashing utilities."""

from __future__ import annotations

import hashlib


def content_hash(content: str) -> str:
    """Return SHA-256 hex digest of the content string."""
    return hashlib.sha256(content.encode()).hexdigest()
