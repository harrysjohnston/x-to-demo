#!/usr/bin/env python3
"""Export developer_prompt and user_prompt for each pipeline phase to markdown files."""

from __future__ import annotations

import sys
from pathlib import Path

# Add apps/api to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.x_to_demo.pipeline.models import PIPELINE_PHASES, PipelineRunInput
from app.x_to_demo.pipeline.prompts import build_phase_prompts
from app.x_to_demo.schemas import DemoSpecArtifact, FeatureSpecArtifact


def minimal_phase_inputs() -> tuple[PipelineRunInput, FeatureSpecArtifact, DemoSpecArtifact]:
    """Build minimal phase inputs with field names but empty values."""
    run_input = PipelineRunInput(
        x_input="",
        additional_context="",
        feature_name_hint="",
        feature_name="",
    )
    feature_spec = FeatureSpecArtifact.model_validate(
        {
            "feature_name": "",
            "intent": {"problem": "", "objective": "", "desired_outcome": "", "target_persona": ""},
            "external_behavior": {"inputs": [], "outputs": [], "states": [], "errors": []},
            "acceptance_criteria": [],
            "invariants": [],
            "success_metrics": [],
            "versioning": {"version": "", "changelog": [], "updated_at_utc": ""},
            "source": {"x_source_type": "", "inputs": [], "notes": ""},
        }
    )
    demo_spec = DemoSpecArtifact.model_validate(
        {
            "feature_name": "",
            "demo_overview": "",
            "demo_scope": {"in_scope": [], "out_of_scope": []},
            "demo_format": "",
            "core_flow_steps": [],
            "success_signals": [],
            "example_copy": [],
            "source": {"x_source_type": "", "inputs": [], "notes": ""},
        }
    )
    return run_input, feature_spec, demo_spec


def main() -> None:
    api_root = Path(__file__).resolve().parent.parent
    run_input, feature_spec, demo_spec = minimal_phase_inputs()
    phase_inputs = [run_input, feature_spec, demo_spec]
    output_dir = api_root / "app" / "x_to_demo" / "pipeline" / "prompts"
    output_dir.mkdir(parents=True, exist_ok=True)

    for phase, phase_input in zip(PIPELINE_PHASES, phase_inputs, strict=True):
        developer_prompt, user_prompt = build_phase_prompts(phase=phase, phase_input=phase_input)

        # Use indented code block for user prompt to avoid nested ``` breaking markdown
        indented_prompt = "\n".join("    " + line for line in user_prompt.split("\n"))
        content = f"""# {phase.title}

**Phase key:** `{phase.key}`

## Developer prompt

{developer_prompt}

## User prompt

{indented_prompt}
"""

        out_path = output_dir / f"{phase.key}_prompts.md"
        out_path.write_text(content, encoding="utf-8")
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
