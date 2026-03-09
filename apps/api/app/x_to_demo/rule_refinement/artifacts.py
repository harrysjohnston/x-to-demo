"""Persistence helpers for versioned rule refinement outputs."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from .extractors import DemoBuildRulesLines
from .models import NarrativeCritique, RuleRefinementIterationArtifact, RuleUpdateSuggestions

if TYPE_CHECKING:
    from pathlib import Path

_VERSION_SUFFIX_PATTERN = re.compile(r"^(?P<stem>.+)\.v(?P<version>\d{3})$")


def canonical_rules_base_path(path: Path) -> Path:
    """Normalize a possibly versioned rules path back to the canonical base path."""
    match = _VERSION_SUFFIX_PATTERN.match(path.stem)
    if not match:
        return path
    return path.with_name(f"{match.group('stem')}{path.suffix}")


def versioned_rules_path(base_path: Path, version: int) -> Path:
    """Build a versioned rules markdown path for the given iteration version."""
    return base_path.with_name(f"{base_path.stem}.v{version:03d}{base_path.suffix}")


def versioned_diff_path(base_path: Path, version: int) -> Path:
    """Build the focused diff markdown path for the given iteration version."""
    return base_path.with_name(f"{base_path.stem}.v{version:03d}.diff{base_path.suffix}")


def iteration_narrative_critique_path(base_path: Path, iteration_number: int) -> Path:
    """Build the persisted critique markdown path for an iteration."""
    return base_path.with_name(
        f"{base_path.stem}.iteration-{iteration_number:03d}.narrative-critique.md"
    )


def versioned_narrative_suggestion_path(base_path: Path, version: int, pass_number: int) -> Path:
    """Build the persisted narrative improvement suggestion path for one pass."""
    return base_path.with_name(
        f"{base_path.stem}.v{version:03d}.narrative-pass-{pass_number:02d}.json"
    )


def next_rules_version(base_path: Path) -> int:
    """Resolve the next available version suffix next to the base rules file."""
    canonical_base = canonical_rules_base_path(base_path)
    pattern = re.compile(
        rf"^{re.escape(canonical_base.stem)}\.v(\d{{3}}){re.escape(canonical_base.suffix)}$"
    )
    versions: list[int] = []
    for sibling in canonical_base.parent.iterdir():
        if not sibling.is_file():
            continue
        match = pattern.match(sibling.name)
        if match:
            versions.append(int(match.group(1)))
    return max(versions, default=0) + 1


def lines_to_markdown(lines: dict[int, str]) -> str:
    """Serialize a 1-based line mapping to markdown text."""
    if not lines:
        return ""
    ordered = [value for _, value in sorted(lines.items())]
    return "\n".join(ordered) + "\n"


def apply_rule_update_suggestions(
    rules: DemoBuildRulesLines, suggestions: RuleUpdateSuggestions
) -> DemoBuildRulesLines:
    """Apply line replacements and appends to a rules line mapping."""
    updated_lines = dict(sorted(rules.lines.items()))
    for replacement in sorted(suggestions.replacements, key=lambda item: item.line_number):
        line_number = replacement.line_number
        if line_number < 1 or line_number > rules.line_count:
            raise ValueError(
                f"Replacement line number {line_number} is out of range for {rules.line_count} lines."
            )
        updated_lines[line_number] = replacement.new_line

    next_line_number = max(updated_lines, default=0)
    for appended_line in suggestions.appends:
        next_line_number += 1
        updated_lines[next_line_number] = appended_line

    return DemoBuildRulesLines(
        path=rules.path,
        exists=True,
        line_count=len(updated_lines),
        lines=updated_lines,
    )


def changed_line_numbers(previous: DemoBuildRulesLines, updated: DemoBuildRulesLines) -> list[int]:
    """Return sorted line numbers whose content changed between two rule mappings."""
    max_line = max(previous.line_count, updated.line_count)
    changed: list[int] = []
    for line_number in range(1, max_line + 1):
        if previous.lines.get(line_number) != updated.lines.get(line_number):
            changed.append(line_number)
    return changed


def render_focused_diff(
    previous: DemoBuildRulesLines,
    updated: DemoBuildRulesLines,
    *,
    context_lines: int = 5,
) -> str:
    """Render a focused markdown diff around changed lines only."""
    changed = changed_line_numbers(previous, updated)
    lines = ["# Focused Rule Diff", ""]
    if not changed:
        lines.append("No line changes.")
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            f"Previous path: `{previous.path}`",
            f"Updated path: `{updated.path}`",
            "",
        ]
    )

    windows = _merge_windows(changed, max_line=updated.line_count, context_lines=context_lines)
    for index, (window_start, window_end) in enumerate(windows, start=1):
        lines.extend([f"## Hunk {index}", ""])
        for line_number in range(window_start, window_end + 1):
            previous_line = previous.lines.get(line_number)
            updated_line = updated.lines.get(line_number)
            if previous_line == updated_line:
                if updated_line is None:
                    continue
                lines.append(f"  {line_number:>4} | {updated_line}")
                continue
            if previous_line is not None:
                lines.append(f"- {line_number:>4} | {previous_line}")
            if updated_line is not None:
                lines.append(f"+ {line_number:>4} | {updated_line}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def save_iteration_artifacts(
    *,
    previous: DemoBuildRulesLines,
    updated: DemoBuildRulesLines,
    output_path: Path,
    diff_path: Path,
    version: int,
    canonical_rules_path: Path | None = None,
) -> RuleRefinementIterationArtifact:
    """Persist versioned rules markdown and the focused diff for one iteration."""
    rendered_markdown = lines_to_markdown(updated.lines)
    output_path.write_text(rendered_markdown, encoding="utf-8")
    if canonical_rules_path is not None:
        canonical_rules_path.write_text(rendered_markdown, encoding="utf-8")
    diff_payload = render_focused_diff(
        previous,
        DemoBuildRulesLines(
            path=str(output_path),
            exists=True,
            line_count=updated.line_count,
            lines=updated.lines,
        ),
    )
    diff_path.write_text(diff_payload, encoding="utf-8")
    return RuleRefinementIterationArtifact(
        version=version,
        rules_path=str(output_path),
        diff_path=str(diff_path),
        changed_line_numbers=changed_line_numbers(previous, updated),
    )


def render_narrative_critique_markdown(critique: NarrativeCritique) -> str:
    """Render a narrative critique artifact as readable markdown."""
    lines = ["# Narrative Tuning Critique", ""]

    lines.append("## Critique")
    if critique.critique:
        lines.extend(f"- {item}" for item in critique.critique)
    else:
        lines.append("- No critique observations.")

    lines.extend(["", "## Suggested Improvements"])
    if critique.suggested_improvements:
        lines.extend(f"- {item}" for item in critique.suggested_improvements)
    else:
        lines.append("- No suggested improvements.")

    return "\n".join(lines).rstrip() + "\n"


def save_narrative_critique_artifact(*, output_path: Path, critique: NarrativeCritique) -> None:
    """Persist the narrative critique as markdown."""
    output_path.write_text(render_narrative_critique_markdown(critique), encoding="utf-8")


def save_narrative_suggestion_artifact(
    *, output_path: Path, suggestion: RuleUpdateSuggestions
) -> None:
    """Persist one narrative improvement suggestion as JSON."""
    payload = json.dumps(suggestion.model_dump(mode="json"), indent=2, sort_keys=True)
    output_path.write_text(f"{payload}\n", encoding="utf-8")


def _merge_windows(
    changed: list[int], *, max_line: int, context_lines: int
) -> list[tuple[int, int]]:
    """Merge overlapping context windows around changed lines."""
    windows: list[tuple[int, int]] = []
    for line_number in changed:
        start = max(1, line_number - context_lines)
        end = min(max_line, line_number + context_lines)
        if not windows or start > windows[-1][1] + 1:
            windows.append((start, end))
            continue
        previous_start, previous_end = windows[-1]
        windows[-1] = (previous_start, max(previous_end, end))
    return windows
