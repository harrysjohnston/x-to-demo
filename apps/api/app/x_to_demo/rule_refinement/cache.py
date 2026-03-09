"""Local disk cache for principle extraction results."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from .models import ExtractedPrinciples

logger = logging.getLogger(__name__)

_cache_dir_override: Path | None = None


def set_cache_dir_override(path: Path | None) -> None:
    """Override cache directory for tests. Pass None to reset."""
    global _cache_dir_override
    _cache_dir_override = path


def _cache_dir() -> Path:
    """Return the principles cache directory under repo root."""
    if _cache_dir_override is not None:
        return _cache_dir_override
    return Path(__file__).resolve().parents[5] / ".cache" / "rule_refinement" / "principles"


def content_hash(content: str) -> str:
    """Return SHA-256 hex digest of the content string."""
    return hashlib.sha256(content.encode()).hexdigest()


def get_cached_principles(content_hash: str) -> ExtractedPrinciples | None:
    """Load cached principles for the given content hash, or None if miss."""
    cache_path = _cache_dir() / f"{content_hash}.json"
    if not cache_path.exists():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        return ExtractedPrinciples.model_validate(data)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("Cache read failed for %s: %s", content_hash, exc)
        return None


def set_cached_principles(content_hash: str, principles: ExtractedPrinciples) -> None:
    """Persist principles to cache for the given content hash."""
    cache_path = _cache_dir() / f"{content_hash}.json"
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            principles.model_dump_json(indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning("Cache write failed for %s: %s", content_hash, exc)
