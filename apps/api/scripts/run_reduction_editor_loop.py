#!/usr/bin/env python3
"""Run the reduction editor up to N times, applying changes each pass; stop if changes become empty."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.x_to_demo.rule_refinement import (
    DemoBuildRulesLines,
    apply_rule_update_suggestions,
    build_rule_refinement_service,
    lines_to_markdown,
    load_demo_build_rules_lines,
)


def _normalize_blank_line_runs(rules: DemoBuildRulesLines) -> DemoBuildRulesLines:
    """Collapse repeated blank-line runs after reduction edits."""
    rendered = lines_to_markdown(rules.lines)
    normalized = re.sub(r"\n{3,}", "\n\n", rendered)
    if normalized and not normalized.endswith("\n"):
        normalized += "\n"
    line_items = dict(enumerate(normalized.splitlines(), start=1)) if normalized else {}
    return DemoBuildRulesLines(
        path=rules.path,
        exists=True,
        line_count=len(line_items),
        lines=line_items,
    )


def main() -> None:
    max_passes = 10
    rules_path = Path(".agents/demo-build-rules.md")
    rules = load_demo_build_rules_lines(rules_path)
    service = build_rule_refinement_service()

    history: list[dict] = []
    notes: list[str] = []

    for pass_num in range(1, max_passes + 1):
        suggestion, metrics = service._run_reduction_editor(rules=rules, notes=notes)
        is_empty = len(suggestion.replacements) == 0 and len(suggestion.appends) == 0

        history.append(
            {
                "pass": pass_num,
                "line_count_before": rules.line_count,
                "replacements": len(suggestion.replacements),
                "appends": len(suggestion.appends),
                "empty": is_empty,
                "metrics": metrics.model_dump(mode="json"),
            }
        )

        if is_empty:
            print(f"Pass {pass_num}: no changes proposed; stopping.")
            break

        updated = apply_rule_update_suggestions(rules, suggestion)
        normalized = _normalize_blank_line_runs(updated)
        output_text = lines_to_markdown(normalized.lines)
        rules_path.write_text(output_text, encoding="utf-8")

        rules = DemoBuildRulesLines(
            path=str(rules_path),
            exists=True,
            line_count=normalized.line_count,
            lines=normalized.lines,
        )

        print(
            f"Pass {pass_num}: {len(suggestion.replacements)} replacements, {len(suggestion.appends)} appends; "
            f"lines {history[-1]['line_count_before']} -> {rules.line_count}"
        )

        notes = [
            "Keep reducing redundancy without losing information.",
            "Prefer empty-string replacements for lines made redundant by consolidation.",
        ]

    out_path = Path("rule_refinement_metrics") / "reduction-editor-loop-history.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {"passes": len(history), "history": history, "final_line_count": rules.line_count},
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
