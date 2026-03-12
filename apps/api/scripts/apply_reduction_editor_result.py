#!/usr/bin/env python3
"""Apply a reduction editor result JSON to the demo build rules."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.x_to_demo.rule_refinement import (
    DemoBuildRulesLines,
    RuleLineReplacement,
    RuleUpdateSuggestions,
    apply_rule_update_suggestions,
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
    json_path = Path("rule_refinement_metrics/reduction-editor-pass-1.json")
    if not json_path.exists():
        print(f"Not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(json_path.read_text(encoding="utf-8"))
    rules_path = data["rules_path"]
    suggestion_data = data["suggestion"]

    rules = load_demo_build_rules_lines(Path(rules_path))
    suggestion = RuleUpdateSuggestions(
        replacements=[
            RuleLineReplacement(line_number=r["line_number"], new_line=r["new_line"])
            for r in suggestion_data["replacements"]
        ],
        appends=suggestion_data.get("appends", []),
        rationale=suggestion_data.get("rationale", []),
    )

    updated = apply_rule_update_suggestions(rules, suggestion)
    normalized = _normalize_blank_line_runs(updated)
    output_text = lines_to_markdown(normalized.lines)

    out_path = Path(rules_path)
    out_path.write_text(output_text, encoding="utf-8")
    print(f"Applied {len(suggestion.replacements)} replacements, {len(suggestion.appends)} appends")
    print(
        f"Lines: {rules.line_count} -> {updated.line_count} -> {normalized.line_count} (after blank-line normalization)"
    )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
