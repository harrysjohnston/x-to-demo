#!/usr/bin/env python3
"""Extract rule refinement sources and save each to a file for inspection."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.x_to_demo.rule_refinement import extract_refinement_inputs


def _safe_filename(key: str) -> str:
    """Convert source_key to a filesystem-safe filename."""
    return re.sub(r"[^\w\-.]", "_", key)


def main() -> None:
    output_dir = Path(__file__).resolve().parents[2] / "rule_refinement_extracted"
    output_dir.mkdir(parents=True, exist_ok=True)

    sources = extract_refinement_inputs()
    for src in sources:
        filename = f"{_safe_filename(src.source_key)}.txt"
        filepath = output_dir / filename
        header = f"# {src.title}\n# source_key: {src.source_key}\n\n"
        filepath.write_text(header + src.content, encoding="utf-8")
        print(f"Wrote {filepath}")

    print(f"\n{sources.__len__()} sources saved to {output_dir}")


if __name__ == "__main__":
    main()
