"""Markdown section splitting for batched rule update suggestions."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .extractors import DemoBuildRulesLines

_SECTION_HEADER = re.compile(r"^(===|#{1,6}\s)")


def _is_section_header(line: str) -> bool:
    """True if the line starts a markdown section (=== or ATX header)."""
    return bool(_SECTION_HEADER.match(line.strip()))


def split_rules_into_sections(rules: DemoBuildRulesLines) -> list[tuple[int, int]]:
    """
    Split rules into sections by markdown headers.

    Returns [(start_line, end_line), ...] for each section (1-based, inclusive).
    Section headers: lines matching ^=== or ^#{1,6}\\s.
    - Preamble: lines before the first header (if any)
    - Each section: from one header line (inclusive) to the next header (exclusive)
    - Documents with no headers: single section = entire document
    """
    if not rules.lines:
        return []

    sorted_lines = sorted(rules.lines.items())
    header_indices: list[int] = []
    for line_number, content in sorted_lines:
        if _is_section_header(content):
            header_indices.append(line_number)

    if not header_indices:
        first = sorted_lines[0][0]
        last = sorted_lines[-1][0]
        return [(first, last)]

    sections: list[tuple[int, int]] = []
    line_numbers = [ln for ln, _ in sorted_lines]

    if line_numbers[0] < header_indices[0]:
        sections.append((line_numbers[0], header_indices[0] - 1))

    for i, start in enumerate(header_indices):
        end = header_indices[i + 1] - 1 if i + 1 < len(header_indices) else line_numbers[-1]
        if start <= end:
            sections.append((start, end))

    return sections
