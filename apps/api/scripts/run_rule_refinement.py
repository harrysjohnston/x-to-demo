#!/usr/bin/env python3
"""Run rule refinement for a given number of iterations with optional cost limit."""

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
    CostLimitExceededError,
    build_rule_refinement_service,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=2, help="Number of refinement iterations")
    parser.add_argument(
        "--cost-limit",
        type=float,
        default=10.0,
        help="Stop the run if estimated cost exceeds this amount",
    )
    parser.add_argument(
        "--reduction-passes",
        type=int,
        default=3,
        help="Number of end-of-run reduction passes (use 0 to disable)",
    )
    parser.add_argument(
        "--reduction-note",
        action="append",
        default=[],
        help="Optional note passed into the first reduction editor pass; may be repeated",
    )
    args = parser.parse_args()

    service = build_rule_refinement_service()
    try:
        result = service.run(
            iterations=args.iterations,
            cost_limit=args.cost_limit,
            reduction_passes=args.reduction_passes,
            reduction_notes=args.reduction_note,
        )
        print(f"Completed {result.iterations} iterations")
        print(f"Final rules: {result.final_rules_path}")
        if result.reduction is not None:
            print(
                "Reduction: "
                f"{len(result.reduction.pass_results)} passes, "
                f"{result.reduction.final_line_count} final lines, "
                f"{result.reduction.final_missing_information_count} missing items"
            )
        if result.manifest_path:
            print(f"Manifest: {result.manifest_path}")
        if result.cost_totals:
            print(f"Total cost: ${result.cost_totals.get('total_cost', 0):.4f}")
    except CostLimitExceededError as e:
        print(f"Stopped: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
