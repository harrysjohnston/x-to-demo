"""Persist usage and cost metrics and run manifests for rule refinement."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from app.x_to_demo.pipeline.pricing import merge_costs

if TYPE_CHECKING:
    from .models import RuleRefinementRunResult


def _run_timestamp() -> str:
    """Return a stable timestamp string for the current run."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")


def _repo_root() -> Path:
    """Resolve the repository root from the rule_refinement package."""
    return Path(__file__).resolve().parents[5]


def _metrics_dir() -> Path:
    """Return the gitignored directory for rule refinement usage metrics."""
    return _repo_root() / "rule_refinement_metrics"


def save_usage_metrics(
    *,
    result: RuleRefinementRunResult,
    rules_path: str,
) -> tuple[Path, str]:
    """Persist usage and cost metrics for a rule refinement run.

    Writes a JSON file to rule_refinement_metrics/<stem>.run-<timestamp>.json
    with per-iteration and run-total usage and cost. The directory is gitignored.
    """
    metrics_dir = _metrics_dir()
    metrics_dir.mkdir(parents=True, exist_ok=True)

    base_path = Path(rules_path)
    stem = base_path.stem
    timestamp = _run_timestamp()
    output_path = metrics_dir / f"{stem}.run-{timestamp}.json"

    iteration_metrics = []
    for ir in result.iteration_results:
        usage: dict[str, int] = {}
        costs: list[dict[str, float] | None] = []

        for sr in ir.source_results:
            for m in (sr.analysis_metrics, sr.suggestion_metrics):
                for k, v in m.usage.items():
                    usage[k] = usage.get(k, 0) + int(v or 0)
                costs.append(m.cost)

        for k, v in ir.consolidation_metrics.usage.items():
            usage[k] = usage.get(k, 0) + int(v or 0)
        costs.append(ir.consolidation_metrics.cost)

        nt = ir.narrative_tuning
        for k, v in nt.critique_metrics.usage.items():
            usage[k] = usage.get(k, 0) + int(v or 0)
        costs.append(nt.critique_metrics.cost)
        for pr in nt.pass_results:
            for k, v in pr.suggestion_metrics.usage.items():
                usage[k] = usage.get(k, 0) + int(v or 0)
            costs.append(pr.suggestion_metrics.cost)

        cost_totals = merge_costs(costs)
        iteration_metrics.append(
            {
                "iteration_number": ir.iteration_number,
                "usage": usage,
                "cost": cost_totals,
            }
        )

    payload = {
        "rules_path": rules_path,
        "started_at": datetime.now(UTC).isoformat(),
        "iterations": result.iterations,
        "source_count": result.source_count,
        "iteration_metrics": iteration_metrics,
        "reduction": None,
        "usage_totals": result.usage_totals,
        "cost_totals": result.cost_totals,
    }
    if result.reduction is not None:
        reduction_usage: dict[str, int] = {}
        reduction_costs: list[dict[str, float] | None] = []
        pass_metrics = []
        for reduction_pass in result.reduction.pass_results:
            pass_usage: dict[str, int] = {}
            for key, value in reduction_pass.editor_result.suggestion_metrics.usage.items():
                pass_usage[key] = pass_usage.get(key, 0) + int(value or 0)
                reduction_usage[key] = reduction_usage.get(key, 0) + int(value or 0)
            reduction_costs.append(reduction_pass.editor_result.suggestion_metrics.cost)
            for critic_result in reduction_pass.critic_results:
                for key, value in critic_result.critique_metrics.usage.items():
                    pass_usage[key] = pass_usage.get(key, 0) + int(value or 0)
                    reduction_usage[key] = reduction_usage.get(key, 0) + int(value or 0)
                reduction_costs.append(critic_result.critique_metrics.cost)
            pass_metrics.append(
                {
                    "pass_number": reduction_pass.pass_number,
                    "line_count_before": reduction_pass.line_count_before,
                    "line_count_after": reduction_pass.line_count_after,
                    "line_count_delta": reduction_pass.line_count_delta,
                    "missing_information_count": reduction_pass.missing_information_count,
                    "missing_information_delta": reduction_pass.missing_information_delta,
                    "usage": pass_usage,
                    "cost": merge_costs(
                        [reduction_pass.editor_result.suggestion_metrics.cost]
                        + [critic.critique_metrics.cost for critic in reduction_pass.critic_results]
                    ),
                }
            )
        payload["reduction"] = {
            "input_rules_path": result.reduction.input_rules_path,
            "output_rules_path": result.reduction.output_artifact.rules_path,
            "final_line_count": result.reduction.final_line_count,
            "final_missing_information_count": result.reduction.final_missing_information_count,
            "pass_metrics": pass_metrics,
            "usage": reduction_usage,
            "cost": merge_costs(reduction_costs),
        }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path, timestamp


def save_run_manifest(
    *,
    result: RuleRefinementRunResult,
    rules_path: str,
    timestamp: str,
    model: str | None = None,
    reasoning_effort: str | None = None,
) -> Path:
    """Persist an informative, readable manifest for a rule refinement run.

    Writes a markdown file next to the rules document (e.g.
    .agents/demo-build-rules.run-<timestamp>.manifest.md) summarizing the run,
    key artifacts, and cost/usage.
    """
    base_path = Path(rules_path)
    rules_dir = base_path.parent
    stem = base_path.stem
    manifest_path = rules_dir / f"{stem}.run-{timestamp}.manifest.md"

    lines: list[str] = [
        "# Rule Refinement Run Manifest",
        "",
        f"**Run:** `{timestamp}`",
        f"**Rules:** `{base_path.name}`",
        "",
        "## Summary",
        "",
        f"- **Iterations:** {result.iterations}",
        f"- **Sources per iteration:** {result.source_count}",
        f"- **Initial rules:** `{result.initial_rules_path}`",
        f"- **Final rules:** `{result.final_rules_path}`",
        "",
    ]

    if model:
        lines.extend([f"- **Model:** {model}", ""])
    if reasoning_effort:
        lines.extend([f"- **Reasoning effort:** {reasoning_effort}", ""])

    if result.cost_totals:
        total = result.cost_totals.get("total_cost")
        if total is not None:
            lines.extend(["## Cost", "", f"**Total:** ${total:.4f}", ""])
    if result.usage_totals:
        lines.extend(
            [
                "## Usage",
                "",
                "| Token type | Count |",
                "|------------|------:|",
            ]
        )
        for k, v in sorted(result.usage_totals.items()):
            lines.append(f"| {k} | {v:,} |")
        lines.append("")

    lines.extend(["## Artifacts by Iteration", ""])

    for ir in result.iteration_results:
        lines.extend(
            [
                f"### Iteration {ir.iteration_number}",
                "",
                f"- **Input rules:** `{Path(ir.input_rules_path).name}`",
                f"- **Consolidation:** `{Path(ir.consolidation_artifact.rules_path).name}`",
                f"  - Diff: `{Path(ir.consolidation_artifact.diff_path).name}`",
                f"- **Narrative critique:** `{Path(ir.narrative_tuning.critique_path).name}`",
                f"- **Final output:** `{Path(ir.narrative_tuning.output_artifact.rules_path).name}`",
                f"  - Diff: `{Path(ir.narrative_tuning.output_artifact.diff_path).name}`",
                "",
            ]
        )
        if ir.source_results:
            lines.append("#### Source improvements")
            lines.append("")
            for sr in ir.source_results:
                lines.extend(
                    [
                        f"- **{sr.title}** (`{sr.source_key}`)",
                        f"  - Analysis: `{Path(sr.analysis_path).name}`",
                        f"  - Suggestion: `{Path(sr.suggestion_path).name}`",
                        f"  - Output: `{Path(sr.output_artifact.rules_path).name}`",
                        "",
                    ]
                )
        if ir.narrative_tuning.pass_results:
            lines.append("#### Narrative passes")
            lines.append("")
            for pr in ir.narrative_tuning.pass_results:
                lines.append(f"- Pass {pr.pass_number}: `{Path(pr.suggestion_path).name}`")
            lines.append("")

    if result.reduction is not None:
        lines.extend(["## Reduction", ""])
        lines.extend(
            [
                f"- **Input rules:** `{Path(result.reduction.input_rules_path).name}`",
                f"- **Final output:** `{Path(result.reduction.output_artifact.rules_path).name}`",
                f"  - Diff: `{Path(result.reduction.output_artifact.diff_path).name}`",
                f"- **Final line count:** {result.reduction.final_line_count}",
                f"- **Final missing information count:** {result.reduction.final_missing_information_count}",
                "",
            ]
        )
        for reduction_pass in result.reduction.pass_results:
            lines.extend(
                [
                    f"### Reduction Pass {reduction_pass.pass_number}",
                    "",
                    f"- **Suggestion:** `{Path(reduction_pass.editor_result.suggestion_path).name}`",
                    f"- **Output:** `{Path(reduction_pass.editor_result.output_artifact.rules_path).name}`",
                    f"- **Line count:** {reduction_pass.line_count_before} -> {reduction_pass.line_count_after} ({reduction_pass.line_count_delta:+d})",
                    f"- **Missing information count:** {reduction_pass.missing_information_count}",
                    "",
                ]
            )
            if reduction_pass.parent_notes:
                lines.append("#### Parent notes")
                lines.append("")
                lines.extend(f"- {note}" for note in reduction_pass.parent_notes)
                lines.append("")
            if reduction_pass.critic_results:
                lines.append("#### Reduction critics")
                lines.append("")
                for critic_result in reduction_pass.critic_results:
                    lines.extend(
                        [
                            f"- **{critic_result.title}** (`{critic_result.source_key}`)",
                            f"  - Critique: `{Path(critic_result.critique_path).name}`",
                            f"  - Missing items: {len(critic_result.critique.missing_information)}",
                            "",
                        ]
                    )

    manifest_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return manifest_path
