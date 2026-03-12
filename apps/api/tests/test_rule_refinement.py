"""Tests for rule refinement prompts, artifacts, and orchestration."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import pytest

from app.config import Settings
from app.x_to_demo.rule_refinement import (
    DemoBuildRulesLines,
    RefinementSource,
    RuleLineReplacement,
    RuleRefinementService,
    RuleUpdateSuggestions,
    apply_rule_update_suggestions,
    build_narrative_critique_developer_prompt,
    build_narrative_critique_user_prompt,
    build_narrative_improvement_developer_prompt,
    build_narrative_improvement_user_prompt,
    build_reduction_critic_developer_prompt,
    build_reduction_critic_user_prompt,
    build_reduction_editor_developer_prompt,
    build_reduction_editor_user_prompt,
    build_rule_consolidation_developer_prompt,
    build_rule_consolidation_user_prompt,
    build_rule_update_developer_prompt,
    build_rule_update_user_prompt,
    build_source_gap_analysis_developer_prompt,
    build_source_gap_analysis_user_prompt,
    extract_all_skills,
    extract_phase_models,
    extract_phase_prompts,
    extract_refinement_inputs,
    iteration_source_analysis_path,
    load_demo_build_rules_lines,
    next_rules_version,
    render_focused_diff,
    versioned_source_suggestion_path,
)
from app.x_to_demo.rule_refinement.cache import content_hash


class _FakeResponse:
    def __init__(
        self,
        *,
        output_text: str,
        usage: dict[str, int] | None = None,
        model: str = "gpt-5.2",
        status: str = "completed",
    ) -> None:
        self.output_text = output_text
        self.usage = usage or {}
        self.model = model
        self.status = status


class _FakeResponsesAPI:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = responses
        self.requests: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return self._responses.pop(0)


class _FakeClient:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.responses = _FakeResponsesAPI(responses)


class _FakeRandomizer:
    def __init__(self, shuffled_orders: list[list[str]] | None = None) -> None:
        self._shuffled_orders = shuffled_orders or []
        self.calls = 0

    def shuffle(self, values: list[RefinementSource]) -> None:
        self.calls += 1
        if not self._shuffled_orders:
            values.reverse()
            return
        desired_order = self._shuffled_orders.pop(0)
        ordered_values = {value.source_key: value for value in values}
        values[:] = [ordered_values[source_key] for source_key in desired_order]


def _build_service(
    responses: list[_FakeResponse],
    *,
    randomizer: _FakeRandomizer | None = None,
    model: str = "gpt-5.2",
) -> RuleRefinementService:
    return RuleRefinementService(
        responses_client=_FakeClient(responses),
        model=model,
        reasoning_effort="low",
        response_wait_log_interval_seconds=0.01,
        randomizer=randomizer,
    )


def _narrative_tuning_responses(
    *,
    critique: dict[str, object] | None = None,
    suggestion: dict[str, object] | None = None,
    usages: list[dict[str, int] | None] | None = None,
) -> list[_FakeResponse]:
    critique_payload = critique or {
        "critique": ["The rules could describe the procedure more clearly."],
        "suggested_improvements": ["Make the sequence of steps more explicit."],
    }
    suggestion_payload = suggestion or {"replacements": [], "appends": []}
    usage_payloads = usages or [None, None]
    return [
        _FakeResponse(output_text=json.dumps(critique_payload), usage=usage_payloads[0]),
        _FakeResponse(output_text=json.dumps(suggestion_payload), usage=usage_payloads[1]),
    ]


def _reduction_responses(
    *,
    editor_suggestions: list[dict[str, object]] | None = None,
    critic_payloads: list[dict[str, object]] | None = None,
    usages: list[dict[str, int] | None] | None = None,
) -> list[_FakeResponse]:
    editor_payloads = editor_suggestions or [{"replacements": [], "appends": []}] * 3
    critic_payload_list = critic_payloads or [{"missing_information": []}] * 3
    usage_payloads = usages or [None] * (len(editor_payloads) + len(critic_payload_list))
    responses: list[_FakeResponse] = []
    for index, editor_payload in enumerate(editor_payloads):
        responses.append(
            _FakeResponse(output_text=json.dumps(editor_payload), usage=usage_payloads[index])
        )
        critic_payload = critic_payload_list[index]
        responses.append(
            _FakeResponse(
                output_text=json.dumps(critic_payload),
                usage=usage_payloads[len(editor_payloads) + index],
            )
        )
    return responses


def _require_live_openai_smoke() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or os.getenv("RUN_LIVE_OPENAI_TESTS") != "1":
        pytest.skip(
            "Run only when OPENAI_API_KEY is set and RUN_LIVE_OPENAI_TESTS=1. "
            "Command: OPENAI_API_KEY=... RUN_LIVE_OPENAI_TESTS=1 "
            "uv run pytest -q -c apps/api/pyproject.toml apps/api/tests -k live_openai_smoke"
        )
    return api_key


def test_settings_rule_refinement_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RULE_REFINEMENT_MODEL", raising=False)
    monkeypatch.delenv("RULE_REFINEMENT_REASONING_EFFORT", raising=False)

    configured = Settings(_env_file=None)

    assert configured.rule_refinement_model == "gpt-5.2"
    assert configured.rule_refinement_reasoning_effort == "low"


def test_settings_rule_refinement_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RULE_REFINEMENT_MODEL", "gpt-5-mini")
    monkeypatch.setenv("RULE_REFINEMENT_REASONING_EFFORT", "medium")

    configured = Settings(_env_file=None)

    assert configured.rule_refinement_model == "gpt-5-mini"
    assert configured.rule_refinement_reasoning_effort == "medium"


def test_extract_refinement_inputs_aggregates_sources_in_stable_order() -> None:
    sources = extract_refinement_inputs()

    assert sources[0].source_key == "global_rules"
    assert sources[1].source_key == "feature_spec_prompts"
    assert sources[2].source_key == "feature_spec_models"
    assert any(source.source_key == "code_spec_prompts" for source in sources)
    assert any(source.source_key == "skill_demo-design-decisions" for source in sources)
    assert all(source.content for source in sources)


def test_load_demo_build_rules_lines_for_missing_file(tmp_path: Path) -> None:
    result = load_demo_build_rules_lines(tmp_path / "missing.md")

    assert isinstance(result, DemoBuildRulesLines)
    assert result.exists is False
    assert result.line_count == 0
    assert result.lines == {}


def test_load_demo_build_rules_lines_for_populated_file(tmp_path: Path) -> None:
    rules_path = tmp_path / "demo-build-rules.md"
    rules_path.write_text("# Demo Build Rules\n\nRule one\nRule two\n", encoding="utf-8")

    result = load_demo_build_rules_lines(rules_path)

    assert result.exists is True
    assert result.line_count == 4
    assert result.lines == {
        1: "# Demo Build Rules",
        2: "",
        3: "Rule one",
        4: "Rule two",
    }


def test_extract_phase_prompts_returns_descriptive_text_only() -> None:
    content = extract_phase_prompts("feature_spec")

    assert "## Phase 1: Input -> Feature Spec" in content
    assert "Objective: Transform raw input into a behavior-first feature spec" in content
    assert "### Developer Guidance" in content
    assert "### User Checklist" in content
    assert "```json" not in content
    assert "Output schema (source of truth):" not in content


def test_extract_phase_models_returns_descriptive_model_sections() -> None:
    content = extract_phase_models("feature_spec")

    assert "## Phase 1: Input -> Feature Spec" in content
    assert "### Input model" in content
    assert "### Output model" in content
    assert "#### `PipelineRunInput`" in content
    assert "#### `FeatureSpecArtifact`" in content


def test_extract_all_skills_discovers_current_skill_set() -> None:
    skills = extract_all_skills()

    assert "demo-design-decisions" in skills
    assert "generated-output-badge" in skills
    assert "## Reference" in skills["generated-output-badge"]


def test_developer_prompts_prepend_shared_objective() -> None:
    analysis_prompt = build_source_gap_analysis_developer_prompt()
    update_prompt = build_rule_update_developer_prompt()
    consolidation_prompt = build_rule_consolidation_developer_prompt()
    narrative_critique_prompt = build_narrative_critique_developer_prompt()
    narrative_improvement_prompt = build_narrative_improvement_developer_prompt()
    reduction_editor_prompt = build_reduction_editor_developer_prompt()
    reduction_critic_prompt = build_reduction_critic_developer_prompt()

    expected_prefix = (
        "Overall objective: define standard rules and procedures for the creation "
        "of demos showcasing proposed GenAI products."
    )
    assert analysis_prompt.startswith(expected_prefix)
    assert update_prompt.startswith(expected_prefix)
    assert consolidation_prompt.startswith(expected_prefix)
    assert narrative_critique_prompt.startswith(expected_prefix)
    assert narrative_improvement_prompt.startswith(expected_prefix)
    assert reduction_editor_prompt.startswith(expected_prefix)
    assert reduction_critic_prompt.startswith(expected_prefix)


def test_source_gap_analysis_user_prompt_includes_rules_and_source() -> None:
    prompt = build_source_gap_analysis_user_prompt(
        rules_text="Rule one\nRule two\n",
        source=RefinementSource(
            source_key="skill_example",
            title="Skill example",
            content="1. Keep the scope small.",
        ),
    )

    assert "Current build rules raw text" in prompt
    assert "Source key: skill_example" in prompt
    assert "Rule one" in prompt
    assert "Keep the scope small." in prompt


def test_build_rule_update_prompts_include_analysis_and_overlap_guard() -> None:
    prompt = build_rule_update_user_prompt(
        rules=DemoBuildRulesLines(
            path="demo-build-rules.md",
            exists=True,
            line_count=2,
            lines={1: "Rule one", 2: "Rule two"},
        ),
        analysis="- Missing explicit sequencing.\n- Missing default safety handling.",
        source=RefinementSource(
            source_key="global_rules",
            title="Global hard rules",
            content="ignored in this prompt",
        ),
    )

    assert '"1": "Rule one"' in prompt
    assert "Analysis of missing source aspects" in prompt
    assert "Missing explicit sequencing." in prompt
    assert "already done" in build_rule_update_developer_prompt()
    assert "descriptive natural language only" in build_rule_update_developer_prompt()
    assert "not code, schemas, field names" in build_rule_update_developer_prompt()
    assert "already done" in build_narrative_improvement_developer_prompt()
    assert "descriptive natural language only" in build_narrative_improvement_developer_prompt()


def test_build_rule_consolidation_and_narrative_prompts_include_inputs() -> None:
    consolidation_prompt = build_rule_consolidation_user_prompt(
        rules=DemoBuildRulesLines(
            path="demo-build-rules.md",
            exists=True,
            line_count=2,
            lines={1: "Rule one", 2: "Rule two"},
        )
    )
    critique_prompt = build_narrative_critique_user_prompt(
        rules_text="# Rules\n\n1. Start with context.\n2. Use clear terms."
    )
    narrative_prompt = build_narrative_improvement_user_prompt(
        rules=DemoBuildRulesLines(
            path="demo-build-rules.md",
            exists=True,
            line_count=2,
            lines={1: "Rule one", 2: "Rule two"},
        ),
        suggested_improvements=[
            "Clarify the opening procedure.",
            "Replace undefined jargon with plain language.",
        ],
    )

    assert "consolidate repetitive rules" in consolidation_prompt
    assert "Current build rules raw text" in critique_prompt
    assert "Suggested narrative improvements" in narrative_prompt


def test_build_reduction_prompts_include_notes_and_changes() -> None:
    editor_prompt = build_reduction_editor_user_prompt(
        rules=DemoBuildRulesLines(
            path="demo-build-rules.md",
            exists=True,
            line_count=3,
            lines={1: "Rule one", 2: "Rule two", 3: "Rule three"},
        ),
        notes=["Preserve setup sequencing.", "Restore any missing safety guidance."],
    )
    critic_prompt = build_reduction_critic_user_prompt(
        rules_text="Rule one\nRule two\n",
        source=RefinementSource(
            source_key="skill_example",
            title="Skill example",
            content="Keep setup explicit and safe.",
        ),
        editor_changes=RuleUpdateSuggestions(
            replacements=[RuleLineReplacement(line_number=2, new_line="")],
            appends=[],
            rationale=["Merged duplicate setup rules."],
        ),
    )

    assert "Parent notes for this reduction pass" in editor_prompt
    assert "Preserve setup sequencing." in editor_prompt
    assert '"2": "Rule two"' in editor_prompt
    assert "reduce redundancy" in build_reduction_editor_developer_prompt().lower()
    assert "Applied editor changes" in critic_prompt
    assert '"line_number": 2' in critic_prompt
    assert "updated rules" in build_reduction_critic_developer_prompt()


def test_apply_rule_update_suggestions_replaces_and_appends_lines() -> None:
    rules = DemoBuildRulesLines(
        path="demo-build-rules.md",
        exists=True,
        line_count=2,
        lines={1: "Rule one", 2: "Rule two"},
    )

    updated = apply_rule_update_suggestions(
        rules,
        RuleUpdateSuggestions(
            replacements=[RuleLineReplacement(line_number=2, new_line="Rule two updated")],
            appends=["Rule three"],
        ),
    )

    assert updated.lines == {
        1: "Rule one",
        2: "Rule two updated",
        3: "Rule three",
    }


def test_apply_rule_update_suggestions_rejects_invalid_line_numbers() -> None:
    rules = DemoBuildRulesLines(
        path="demo-build-rules.md",
        exists=True,
        line_count=2,
        lines={1: "Rule one", 2: "Rule two"},
    )

    with pytest.raises(ValueError, match="Replacement line number 3 is out of range"):
        apply_rule_update_suggestions(
            rules,
            RuleUpdateSuggestions(
                replacements=[RuleLineReplacement(line_number=3, new_line="Nope")]
            ),
        )


def test_next_rules_version_skips_existing_versions(tmp_path: Path) -> None:
    base_path = tmp_path / "demo-build-rules.md"
    base_path.write_text("base\n", encoding="utf-8")
    (tmp_path / "demo-build-rules.v001.md").write_text("v1\n", encoding="utf-8")
    (tmp_path / "demo-build-rules.v002.md").write_text("v2\n", encoding="utf-8")

    assert next_rules_version(base_path) == 3


def test_render_focused_diff_limits_context_to_changed_lines_plus_minus_five() -> None:
    previous = DemoBuildRulesLines(
        path="before.md",
        exists=True,
        line_count=12,
        lines={line_number: f"Line {line_number}" for line_number in range(1, 13)},
    )
    updated = DemoBuildRulesLines(
        path="after.md",
        exists=True,
        line_count=13,
        lines={
            **{line_number: f"Line {line_number}" for line_number in range(1, 13)},
            13: "Line 13",
        },
    )
    updated.lines[6] = "Line 6 updated"

    diff = render_focused_diff(previous, updated, context_lines=5)

    assert "## Hunk 1" in diff
    assert "-    6 | Line 6" in diff
    assert "+    6 | Line 6 updated" in diff
    assert "+   13 | Line 13" in diff


def test_source_analysis_and_suggestion_paths_include_iteration_source_and_version(
    tmp_path: Path,
) -> None:
    base_path = tmp_path / "demo-build-rules.md"
    analysis_path = iteration_source_analysis_path(base_path, 3, "skill/demo design")
    suggestion_path = versioned_source_suggestion_path(base_path, 7, "skill/demo design")

    assert analysis_path.name == "demo-build-rules.iteration-003.skill-demo-design.analysis.md"
    assert suggestion_path.name == "demo-build-rules.v007.skill-demo-design.suggestion.json"


def test_content_hash_is_stable() -> None:
    assert content_hash("foo") == content_hash("foo")
    assert content_hash("foo") != content_hash("bar")


def test_rule_refinement_service_runs_iterations_and_saves_versioned_outputs(
    tmp_path: Path,
) -> None:
    rules_path = tmp_path / "demo-build-rules.md"
    rules_path.write_text("Rule one\nRule two\n", encoding="utf-8")
    randomizer = _FakeRandomizer(
        shuffled_orders=[
            ["source_a", "source_b"],
            ["source_b", "source_a"],
        ]
    )
    service = _build_service(
        [
            _FakeResponse(output_text="Missing a clearer rule two."),
            _FakeResponse(output_text="Missing a rule four."),
            _FakeResponse(
                output_text=json.dumps(
                    {
                        "replacements": [{"line_number": 2, "new_line": "Rule two updated"}],
                        "appends": ["Rule three"],
                    }
                )
            ),
            _FakeResponse(output_text=json.dumps({"replacements": [], "appends": ["Rule four"]})),
            _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
            *_narrative_tuning_responses(),
            _FakeResponse(output_text="Missing a clearer third rule."),
            _FakeResponse(output_text="Missing a rule five."),
            _FakeResponse(
                output_text=json.dumps(
                    {
                        "replacements": [{"line_number": 3, "new_line": "Rule three refined"}],
                        "appends": [],
                    }
                )
            ),
            _FakeResponse(output_text=json.dumps({"replacements": [], "appends": ["Rule five"]})),
            _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
            *_narrative_tuning_responses(),
        ],
        randomizer=randomizer,
    )

    result = service.run(
        iterations=2,
        rules_path=rules_path,
        sources=[
            RefinementSource(source_key="source_a", title="Source A", content="Source A"),
            RefinementSource(source_key="source_b", title="Source B", content="Source B"),
        ],
        reduction_passes=0,
    )

    assert randomizer.calls == 2
    assert result.final_rules_path.endswith("demo-build-rules.v008.md")
    assert result.iteration_results[0].consolidation_artifact.rules_path.endswith("v003.md")
    assert result.iteration_results[0].narrative_tuning.output_artifact.rules_path.endswith(
        "v004.md"
    )
    assert result.iteration_results[1].consolidation_artifact.rules_path.endswith("v007.md")
    assert result.iteration_results[1].output_artifact.rules_path.endswith("v008.md")
    assert [entry.source_key for entry in result.iteration_results[0].source_results] == [
        "source_a",
        "source_b",
    ]
    assert [entry.source_key for entry in result.iteration_results[1].source_results] == [
        "source_b",
        "source_a",
    ]
    assert len(result.iteration_results[0].narrative_tuning.pass_results) == 1
    assert (tmp_path / "demo-build-rules.v001.md").read_text(encoding="utf-8").splitlines() == [
        "Rule one",
        "Rule two updated",
        "Rule three",
    ]
    assert (tmp_path / "demo-build-rules.v002.md").read_text(encoding="utf-8").splitlines() == [
        "Rule one",
        "Rule two updated",
        "Rule three",
        "Rule four",
    ]
    assert (tmp_path / "demo-build-rules.v008.md").read_text(encoding="utf-8").splitlines() == [
        "Rule one",
        "Rule two updated",
        "Rule three refined",
        "Rule four",
        "Rule five",
    ]
    assert rules_path.read_text(encoding="utf-8").splitlines() == [
        "Rule one",
        "Rule two updated",
        "Rule three refined",
        "Rule four",
        "Rule five",
    ]
    assert Path(result.iteration_results[0].source_results[0].analysis_path).exists()
    assert Path(result.iteration_results[0].source_results[0].suggestion_path).exists()
    assert Path(result.iteration_results[0].narrative_tuning.critique_path).exists()
    assert Path(
        result.iteration_results[1].narrative_tuning.pass_results[0].suggestion_path
    ).exists()
    assert result.manifest_path is not None
    manifest = Path(result.manifest_path)
    assert manifest.exists()
    assert manifest.suffix == ".md"
    assert "manifest" in manifest.stem
    manifest_content = manifest.read_text(encoding="utf-8")
    assert "# Rule Refinement Run Manifest" in manifest_content
    assert "Iteration 1" in manifest_content
    assert "Iteration 2" in manifest_content


def test_rule_refinement_service_builds_expected_payloads_and_reasoning(tmp_path: Path) -> None:
    rules_path = tmp_path / "demo-build-rules.md"
    rules_path.write_text("Rule one\n", encoding="utf-8")
    service = _build_service(
        [
            _FakeResponse(output_text="Missing an opening rule."),
            _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
            _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
            *_narrative_tuning_responses(
                critique={
                    "critique": ["The rules lack a clear opening flow."],
                    "suggested_improvements": ["Add a clearer narrative opening."],
                }
            ),
        ]
    )

    service.run(
        iterations=1,
        rules_path=rules_path,
        sources=[
            RefinementSource(
                source_key="source_a",
                title="Source A",
                content="Synthetic source",
            )
        ],
        reduction_passes=0,
    )

    requests = service.responses_client.responses.requests
    assert requests[0]["reasoning"] == {"effort": "high"}
    assert "text" not in requests[0]
    assert "Current build rules raw text" in requests[0]["input"][1]["content"]
    assert requests[1]["text"]["format"]["name"] == "rule_refinement_suggestions"
    assert "Analysis of missing source aspects" in requests[1]["input"][1]["content"]
    assert requests[2]["text"]["format"]["name"] == "rule_refinement_consolidation"
    assert requests[3]["text"]["format"]["name"] == "rule_refinement_narrative_critique"
    assert requests[3]["reasoning"] == {"effort": "xhigh"}
    assert requests[4]["text"]["format"]["name"] == "rule_refinement_narrative_suggestions"
    assert requests[4]["reasoning"] == {"effort": "medium"}


def test_rule_refinement_service_runs_end_of_run_reduction_loop_and_tracks_deltas(
    tmp_path: Path,
) -> None:
    rules_path = tmp_path / "demo-build-rules.md"
    rules_path.write_text("Rule one\nRule two\nRule three\n", encoding="utf-8")
    service = _build_service(
        [
            _FakeResponse(
                output_text="No source gaps found.",
                usage={"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
            ),
            _FakeResponse(
                output_text=json.dumps({"replacements": [], "appends": []}),
                usage={"input_tokens": 4, "output_tokens": 5, "total_tokens": 9},
            ),
            _FakeResponse(
                output_text=json.dumps({"replacements": [], "appends": []}),
                usage={"input_tokens": 6, "output_tokens": 7, "total_tokens": 13},
            ),
            *_narrative_tuning_responses(
                critique={"critique": [], "suggested_improvements": []},
                suggestion={"replacements": [], "appends": []},
                usages=[
                    {"input_tokens": 8, "output_tokens": 9, "total_tokens": 17},
                    {"input_tokens": 10, "output_tokens": 11, "total_tokens": 21},
                ],
            ),
            *_reduction_responses(
                editor_suggestions=[
                    {
                        "replacements": [
                            {"line_number": 2, "new_line": ""},
                            {"line_number": 3, "new_line": ""},
                        ],
                        "appends": [],
                    },
                    {
                        "replacements": [{"line_number": 2, "new_line": "Rule two restored"}],
                        "appends": [],
                    },
                    {
                        "replacements": [],
                        "appends": [],
                    },
                ],
                critic_payloads=[
                    {"missing_information": ["Restore setup detail.", "Restore safety detail."]},
                    {"missing_information": ["Restore safety detail."]},
                    {"missing_information": []},
                ],
                usages=[
                    {"input_tokens": 12, "output_tokens": 13, "total_tokens": 25},
                    {"input_tokens": 14, "output_tokens": 15, "total_tokens": 29},
                    {"input_tokens": 16, "output_tokens": 17, "total_tokens": 33},
                    {"input_tokens": 18, "output_tokens": 19, "total_tokens": 37},
                    {"input_tokens": 20, "output_tokens": 21, "total_tokens": 41},
                    {"input_tokens": 22, "output_tokens": 23, "total_tokens": 45},
                ],
            ),
        ]
    )

    result = service.run(
        iterations=1,
        rules_path=rules_path,
        sources=[
            RefinementSource(source_key="source_a", title="Source A", content="Synthetic source"),
        ],
    )

    requests = service.responses_client.responses.requests
    assert requests[5]["text"]["format"]["name"] == "rule_refinement_reduction_editor"
    assert requests[5]["reasoning"] == {"effort": "high"}
    assert requests[6]["text"]["format"]["name"] == "rule_refinement_reduction_critic"
    assert requests[6]["reasoning"] == {"effort": "high"}
    assert "Parent notes for this reduction pass" in requests[5]["input"][1]["content"]
    assert "Applied editor changes" in requests[6]["input"][1]["content"]

    assert result.reduction is not None
    assert result.final_rules_path.endswith("demo-build-rules.v006.md")
    assert result.reduction.final_line_count == 2
    assert result.reduction.final_missing_information_count == 0
    assert [
        pass_result.missing_information_count for pass_result in result.reduction.pass_results
    ] == [
        2,
        1,
        0,
    ]
    assert [
        pass_result.missing_information_delta for pass_result in result.reduction.pass_results
    ] == [
        None,
        -1,
        -1,
    ]
    assert [pass_result.line_count_after for pass_result in result.reduction.pass_results] == [
        2,
        2,
        2,
    ]
    assert result.reduction.pass_results[0].parent_notes
    assert result.reduction.pass_results[1].parent_notes
    assert result.reduction.pass_results[2].parent_notes == []
    assert Path(
        result.reduction.pass_results[0].editor_result.output_artifact.rules_path
    ).read_text(encoding="utf-8").splitlines() == ["Rule one", ""]
    assert Path(result.final_rules_path).read_text(encoding="utf-8").splitlines() == [
        "Rule one",
        "Rule two restored",
    ]
    assert result.usage_totals == {
        "cached_input_tokens": 0,
        "input_tokens": 131,
        "output_tokens": 142,
        "reasoning_tokens": 0,
        "total_tokens": 273,
    }

    assert result.manifest_path is not None
    manifest_text = Path(result.manifest_path).read_text(encoding="utf-8")
    assert "## Reduction" in manifest_text
    assert "Reduction Pass 1" in manifest_text
    assert "Final missing information count" in manifest_text

    metrics_filename = Path(result.manifest_path).name.replace(".manifest.md", ".json")
    metrics_payload = json.loads(
        (Path("rule_refinement_metrics") / metrics_filename).read_text(encoding="utf-8")
    )
    assert metrics_payload["reduction"]["final_line_count"] == 2
    assert metrics_payload["reduction"]["final_missing_information_count"] == 0
    assert len(metrics_payload["reduction"]["pass_metrics"]) == 3


def test_rule_refinement_service_emits_human_readable_logs(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    rules_path = tmp_path / "demo-build-rules.md"
    rules_path.write_text("Rule one\n", encoding="utf-8")
    service = _build_service(
        [
            _FakeResponse(output_text="Missing an opening rule."),
            _FakeResponse(output_text=json.dumps({"replacements": [], "appends": ["Rule two"]})),
            _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
            *_narrative_tuning_responses(),
        ]
    )

    with caplog.at_level(logging.INFO, logger="app.x_to_demo.rule_refinement.service"):
        service.run(
            iterations=1,
            rules_path=rules_path,
            sources=[
                RefinementSource(
                    source_key="source_a",
                    title="Source A",
                    content="Synthetic source",
                )
            ],
            reduction_passes=0,
        )

    log_text = caplog.text
    assert "Starting rule refinement run" in log_text
    assert "Starting rule refinement iteration 1/1" in log_text
    assert "Starting concurrent source-gap analysis" in log_text
    assert "Completed source improvement" in log_text
    assert "Suggestion summary: 0 replacements, 1 appends, 0 rationale notes" in log_text
    assert "Completed consolidation" in log_text
    assert "Completed narrative critique" in log_text
    assert "Completed narrative improvement" in log_text
    assert "Rule refinement run complete" in log_text


def test_rule_refinement_service_clamps_reasoning_for_gpt5_mini(tmp_path: Path) -> None:
    rules_path = tmp_path / "demo-build-rules.md"
    rules_path.write_text("Rule one\n", encoding="utf-8")
    service = _build_service(
        [
            _FakeResponse(output_text="Missing an opening rule."),
            _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
            _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
            *_narrative_tuning_responses(),
        ],
        model="gpt-5-mini",
    )

    service.run(
        iterations=1,
        rules_path=rules_path,
        sources=[
            RefinementSource(
                source_key="source_a",
                title="Source A",
                content="Synthetic source",
            )
        ],
        reduction_passes=0,
    )

    requests = service.responses_client.responses.requests
    assert requests[0]["reasoning"] == {"effort": "high"}
    assert requests[3]["reasoning"] == {"effort": "high"}
    assert requests[4]["reasoning"] == {"effort": "medium"}


def test_rule_refinement_service_uses_updated_rules_for_serial_improvements_and_tracks_usage(
    tmp_path: Path,
) -> None:
    rules_path = tmp_path / "demo-build-rules.md"
    rules_path.write_text("Rule one\n", encoding="utf-8")
    service = _build_service(
        [
            _FakeResponse(
                output_text="- Add a heading.",
                usage={"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
            ),
            _FakeResponse(
                output_text="- Add a first action.",
                usage={"input_tokens": 4, "output_tokens": 5, "total_tokens": 9},
            ),
            _FakeResponse(
                output_text=json.dumps(
                    {
                        "replacements": [{"line_number": 1, "new_line": "## Narrative Flow"}],
                        "appends": [],
                    }
                ),
                usage={"input_tokens": 6, "output_tokens": 7, "total_tokens": 13},
            ),
            _FakeResponse(
                output_text=json.dumps(
                    {"replacements": [], "appends": ["1. Start by stating the user's goal."]}
                ),
                usage={"input_tokens": 8, "output_tokens": 9, "total_tokens": 17},
            ),
            _FakeResponse(
                output_text=json.dumps({"replacements": [], "appends": []}),
                usage={"input_tokens": 10, "output_tokens": 11, "total_tokens": 21},
            ),
            *_narrative_tuning_responses(
                critique={
                    "critique": ["The rules read like isolated statements."],
                    "suggested_improvements": ["Keep the opening flow explicit."],
                },
                suggestion={"replacements": [], "appends": []},
                usages=[
                    {"input_tokens": 12, "output_tokens": 13, "total_tokens": 25},
                    {"input_tokens": 14, "output_tokens": 15, "total_tokens": 29},
                ],
            ),
        ]
    )

    result = service.run(
        iterations=1,
        rules_path=rules_path,
        sources=[
            RefinementSource(source_key="source_a", title="Source A", content="Synthetic A"),
            RefinementSource(source_key="source_b", title="Source B", content="Synthetic B"),
        ],
        reduction_passes=0,
    )

    requests = service.responses_client.responses.requests
    assert '"1": "## Narrative Flow"' in requests[3]["input"][1]["content"]
    assert "1. Start by stating the user's goal." in requests[4]["input"][1]["content"]
    assert result.usage_totals == {
        "cached_input_tokens": 0,
        "input_tokens": 55,
        "output_tokens": 62,
        "reasoning_tokens": 0,
        "total_tokens": 117,
    }
    assert result.iteration_results[0].narrative_tuning.critique.critique == [
        "The rules read like isolated statements."
    ]
    assert Path(result.final_rules_path).read_text(encoding="utf-8").splitlines() == [
        "## Narrative Flow",
        "1. Start by stating the user's goal.",
    ]


def test_rule_refinement_service_raises_for_invalid_source_suggestion_line_numbers(
    tmp_path: Path,
) -> None:
    rules_path = tmp_path / "demo-build-rules.md"
    rules_path.write_text("Rule one\n", encoding="utf-8")
    service = _build_service(
        [
            _FakeResponse(output_text="Bad suggestion."),
            _FakeResponse(
                output_text=json.dumps(
                    {"replacements": [{"line_number": 9, "new_line": "Bad line"}]}
                )
            ),
        ]
    )

    with pytest.raises(ValueError, match="Replacement line number 9 is out of range"):
        service.run(
            iterations=1,
            rules_path=rules_path,
            sources=[
                RefinementSource(
                    source_key="source_a",
                    title="Source A",
                    content="Synthetic source",
                )
            ],
            reduction_passes=0,
        )


def test_rule_refinement_service_raises_for_invalid_narrative_suggestion_line_numbers(
    tmp_path: Path,
) -> None:
    rules_path = tmp_path / "demo-build-rules.md"
    rules_path.write_text("Rule one\n", encoding="utf-8")
    service = _build_service(
        [
            _FakeResponse(output_text="Keep the rule."),
            _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
            _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
            *_narrative_tuning_responses(
                suggestion={
                    "replacements": [{"line_number": 9, "new_line": "Bad line"}],
                    "appends": [],
                }
            ),
        ]
    )

    with pytest.raises(ValueError, match="Replacement line number 9 is out of range"):
        service.run(
            iterations=1,
            rules_path=rules_path,
            sources=[
                RefinementSource(
                    source_key="source_a",
                    title="Source A",
                    content="Synthetic source",
                )
            ],
            reduction_passes=0,
        )


@pytest.mark.integration
def test_live_openai_smoke_rule_refinement_source_analysis() -> None:
    from openai import OpenAI

    api_key = _require_live_openai_smoke()
    service = RuleRefinementService(
        responses_client=OpenAI(api_key=api_key, timeout=1800.0),
        model="gpt-5.2",
        reasoning_effort="low",
        response_wait_log_interval_seconds=0.01,
    )

    analysis, metrics = service._analyze_sources(
        rules=DemoBuildRulesLines(
            path="demo-build-rules.md",
            exists=True,
            line_count=2,
            lines={1: "Keep the scope small.", 2: "Use clear language."},
        ),
        sources=[
            RefinementSource(
                source_key="source_a",
                title="Source A",
                content="Require explicit sequencing and defaults.",
            )
        ],
    )["source_a"]

    assert analysis
    assert metrics.status == "completed"
    assert metrics.model_used


@pytest.mark.integration
def test_live_openai_smoke_rule_refinement_source_improvement() -> None:
    from openai import OpenAI

    api_key = _require_live_openai_smoke()
    service = RuleRefinementService(
        responses_client=OpenAI(api_key=api_key, timeout=1800.0),
        model="gpt-5.2",
        reasoning_effort="low",
        response_wait_log_interval_seconds=0.01,
    )

    suggestion, metrics = service._suggest_rule_updates(
        rules=DemoBuildRulesLines(
            path="demo-build-rules.md",
            exists=True,
            line_count=2,
            lines={1: "Rule one", 2: "Rule two"},
        ),
        analysis="- Missing a clearer opening.\n- Missing sequencing.",
        source=RefinementSource(
            source_key="source_a",
            title="Source A",
            content="Synthetic source",
        ),
    )

    assert isinstance(suggestion.replacements, list)
    assert isinstance(suggestion.appends, list)
    assert metrics.status == "completed"
    assert metrics.model_used
