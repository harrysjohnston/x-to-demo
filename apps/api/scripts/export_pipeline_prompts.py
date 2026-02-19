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
            "innovation_focus": {
                "ai_headline_capabilities": [
                    {
                        "name": "capability_1",
                        "input_modalities": ["text"],
                        "user_value": "",
                        "what_is_generated_or_optimized": "",
                        "why_ai_or_innovation_is_required": "",
                        "inputs": {"modality": "text", "description": ""},
                        "outputs": {"modality": "text", "description": ""},
                        "demo_proof": "",
                    }
                ],
                "assumptions_and_constraints": {
                    "text_output_by_default": True,
                    "no_external_tools_unless_necessary": True,
                    "minimalist_ui": True,
                    "system_theme_support": True,
                    "notes": "",
                },
                "guardrails_summary": {
                    "off_topic_short_circuit": "",
                    "unsafe_or_disallowed_short_circuit": "",
                    "allowed_summary": "",
                    "refused_summary": "",
                },
                "tooling_need_assessment": {
                    "needs_tools": False,
                    "why_tools_needed": "not needed",
                },
            },
            "acceptance_criteria": [
                {
                    "capability_ref": "capability_1",
                    "given": "",
                    "when": "",
                    "then": [""],
                }
            ],
            "excluded_plumbing": ["auth"],
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
            "headline_demo_items": [
                {
                    "capability_ref": "capability_1",
                    "interaction_mode": "text_chat",
                    "user_story_in_demo": "",
                    "ai_moment": "",
                    "success_looks_like": "",
                }
            ],
            "interaction_requirements": {
                "requires_voice": False,
                "requires_tool_loop": False,
            },
            "ai_pipeline_delineation": {
                "ai_components": [""],
                "non_ai_components": [""],
                "where_innovation_lives": "",
            },
            "demo_experience": {
                "minimalist_views": [
                    {
                        "name": "",
                        "purpose": "",
                        "primary_component": "",
                        "visible_elements": [""],
                        "hidden_or_omitted_elements": [],
                    }
                ],
                "theme_support": {"system_dark_light": True},
                "device_target": {
                    "is_mobile_like": False,
                    "smartphone_frame": {
                        "enabled": False,
                        "width": None,
                        "height": None,
                        "bezel_style": None,
                    },
                },
            },
            "interactive_walkthrough": {
                "auto_start_on_launch": True,
                "retrigger_mechanism": "",
                "controls": {"next": True, "back": True, "cancel": True},
                "steps": [
                    {
                        "id": "step-1",
                        "title": "",
                        "ui_target": "",
                        "explanation": "",
                        "what_ai_does_here": "",
                        "success_criteria": "",
                    }
                ],
            },
            "synthetic_demo_inputs": {
                "seed_dataset": {"summary": "", "sample_records": [""]},
                "default_first_run_inputs": {
                    "ordered_inputs": [""],
                    "trigger_action": "",
                },
                "why_this_data": "",
                "safety_and_realism_notes": "",
                "expected_outputs": {"summary": "", "sample_records": [""]},
            },
            "consistency_trace": {
                "phase1_headline_capability_refs": ["capability_1"],
                "stable_identifier_rule": "",
                "walkthrough_alignment_summary": "",
            },
            "tooling_decision_trace": {
                "phase1_needs_tools": False,
                "phase1_why_tools_needed": "not needed",
                "must_remain_consistent": True,
                "consistency_notes": "",
            },
            "tooling_plan_if_needed": {
                "mode": "no_tools",
                "rationale": "not needed",
                "tool_definitions": [],
                "synthetic_data_source": "not used",
                "ui_visible_tool_call_log": False,
            },
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
