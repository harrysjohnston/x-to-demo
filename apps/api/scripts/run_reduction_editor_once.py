#!/usr/bin/env python3
"""Run the first reduction editor pass and write the result to a JSON file."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.x_to_demo.rule_refinement import (
    build_rule_refinement_service,
    load_demo_build_rules_lines,
)

service = build_rule_refinement_service()
rules = load_demo_build_rules_lines()
suggestion, metrics = service._run_reduction_editor(rules=rules, notes=[])

output = {
    "rules_path": rules.path,
    "line_count": rules.line_count,
    "suggestion": suggestion.model_dump(mode="json"),
    "metrics": metrics.model_dump(mode="json"),
}

out_path = Path("rule_refinement_metrics") / "reduction-editor-pass-1.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
print(f"Wrote {out_path}")
