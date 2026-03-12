#!/usr/bin/env python3
"""Run the editor-critic reduction loop only, on the current demo build rules."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import colorlog

handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(
    colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s %(levelname)-8s%(reset)s %(name)s: %(message)s",
        log_colors=colorlog.default_log_colors,
    )
)
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.x_to_demo.rule_refinement import (  # noqa: E402
    build_rule_refinement_service,
    canonical_rules_base_path,
    extract_refinement_inputs,
    load_demo_build_rules_lines,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--passes",
        type=int,
        default=3,
        help="Number of editor-critic reduction passes",
    )
    parser.add_argument(
        "--note",
        action="append",
        default=[],
        help="Optional note for the first editor pass; may be repeated",
    )
    parser.add_argument(
        "--rules-path",
        type=Path,
        default=None,
        help="Path to demo build rules (default: .agents/demo-build-rules.md)",
    )
    args = parser.parse_args()

    rules_path = args.rules_path or Path(".agents/demo-build-rules.md")
    if not rules_path.is_absolute():
        rules_path = Path.cwd() / rules_path

    rules = load_demo_build_rules_lines(rules_path)
    if not rules.exists or rules.line_count == 0:
        print(f"No rules found at {rules_path}", file=sys.stderr)
        sys.exit(1)

    sources = extract_refinement_inputs()
    if not sources:
        print("No refinement sources extracted", file=sys.stderr)
        sys.exit(1)

    canonical_path = canonical_rules_base_path(rules_path)
    service = build_rule_refinement_service()

    result, _final_rules, _usage, cost = service._run_reduction(
        rules=rules,
        sources=sources,
        reduction_passes=args.passes,
        notes=args.note,
        canonical_rules_path=canonical_path,
    )

    print(f"Reduction complete: {len(result.pass_results)} passes")
    print(f"Final rules: {canonical_path}")
    print(f"Line count: {result.final_line_count}")
    print(f"Missing information count: {result.final_missing_information_count}")
    if cost and "total_cost" in cost:
        print(f"Cost: ${cost['total_cost']:.4f}")


if __name__ == "__main__":
    main()
