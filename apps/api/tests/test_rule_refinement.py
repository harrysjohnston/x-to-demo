"""Tests for rule refinement extraction, prompts, persistence, and service."""

from __future__ import annotations

import json
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
    build_principle_extraction_developer_prompt,
    build_principle_extraction_user_prompt,
    build_rule_consolidation_developer_prompt,
    build_rule_consolidation_user_prompt,
    build_rule_update_developer_prompt,
    build_rule_update_user_prompt,
    extract_all_skills,
    extract_phase_models,
    extract_phase_prompts,
    extract_refinement_inputs,
    load_demo_build_rules_lines,
    next_rules_version,
    render_focused_diff,
)
from app.x_to_demo.rule_refinement.cache import (
    content_hash,
    get_cached_principles,
    set_cache_dir_override,
    set_cached_principles,
)
from app.x_to_demo.rule_refinement.prompts import build_rule_update_user_prompt_for_section
from app.x_to_demo.rule_refinement.sections import split_rules_into_sections


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
    responses: list[_FakeResponse], *, randomizer: _FakeRandomizer | None = None
) -> RuleRefinementService:
    return RuleRefinementService(
        responses_client=_FakeClient(responses),
        model="gpt-5.2",
        reasoning_effort="low",
        response_wait_log_interval_seconds=0.01,
        randomizer=randomizer,
    )


def _narrative_tuning_responses(
    *,
    critique: dict[str, object] | None = None,
    suggestions: list[dict[str, object]] | None = None,
    usages: list[dict[str, int] | None] | None = None,
) -> list[_FakeResponse]:
    critique_payload = critique or {
        "critique": ["The rules could describe the procedure more clearly."],
        "suggested_improvements": ["Make the sequence of steps more explicit."],
    }
    suggestion_payloads = suggestions or [
        {"replacements": [], "appends": []},
        {"replacements": [], "appends": []},
        {"replacements": [], "appends": []},
    ]
    usage_payloads = usages or [None, None, None, None]
    return [
        _FakeResponse(
            output_text=json.dumps(critique_payload),
            usage=usage_payloads[0],
        ),
        *[
            _FakeResponse(
                output_text=json.dumps(payload),
                usage=usage_payloads[index + 1],
            )
            for index, payload in enumerate(suggestion_payloads)
        ],
    ]


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


def test_load_demo_build_rules_lines_for_empty_file(tmp_path: Path) -> None:
    rules_path = tmp_path / "demo-build-rules.md"
    rules_path.write_text("", encoding="utf-8")

    result = load_demo_build_rules_lines(rules_path)

    assert result.exists is True
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
    assert "Global hard rules:" in content
    assert "### User Checklist" in content
    assert "```json" not in content
    assert "Output schema (source of truth):" not in content
    assert "Input payload:" not in content
    assert "Return JSON only." not in content


def test_extract_phase_prompts_includes_code_spec_api_decision_guide() -> None:
    content = extract_phase_prompts("code_spec")

    assert "API decision guide:" in content
    assert "Responses API: choose for request/response interactions" in content
    assert "Agents SDK: choose when multi-step tool loops" in content


def test_extract_phase_models_returns_descriptive_model_sections() -> None:
    content = extract_phase_models("feature_spec")

    assert "## Phase 1: Input -> Feature Spec" in content
    assert "### Input model" in content
    assert "### Output model" in content
    assert "#### `PipelineRunInput`" in content
    assert "#### `FeatureSpecArtifact`" in content
    assert "#### `FeatureIntent`" in content
    assert "| Field | Type | Description |" in content
    assert "$defs" not in content
    assert "model_json_schema" not in content


def test_extract_all_skills_discovers_current_skill_set() -> None:
    skills = extract_all_skills()

    assert "demo-design-decisions" in skills
    assert "generated-output-badge" in skills
    assert "## Reference" in skills["generated-output-badge"]


def test_build_principle_extraction_user_prompt_includes_source_metadata() -> None:
    prompt = build_principle_extraction_user_prompt(
        RefinementSource(
            source_key="skill_example",
            title="Skill example",
            content="1. Keep the scope small.",
        )
    )

    assert "Source key: skill_example" in prompt
    assert "Source title: Skill example" in prompt
    assert "Keep the scope small." in prompt


def test_developer_prompts_prepend_shared_objective() -> None:
    principle_prompt = build_principle_extraction_developer_prompt()
    consolidation_prompt = build_rule_consolidation_developer_prompt()
    narrative_critique_prompt = build_narrative_critique_developer_prompt()
    narrative_improvement_prompt = build_narrative_improvement_developer_prompt()

    expected_prefix = (
        "Overall objective: define standard rules and procedures for the creation "
        "of demos showcasing proposed GenAI products."
    )
    assert principle_prompt.startswith(expected_prefix)
    assert consolidation_prompt.startswith(expected_prefix)
    assert narrative_critique_prompt.startswith(expected_prefix)
    assert narrative_improvement_prompt.startswith(expected_prefix)


def test_build_rule_update_developer_prompt_includes_no_updates_is_fine() -> None:
    prompt = build_rule_update_developer_prompt()
    assert "Suggesting no updates" in prompt
    assert "empty replacements and appends" in prompt


def test_build_rule_update_user_prompt_includes_line_mapping_and_principles() -> None:
    prompt = build_rule_update_user_prompt(
        rules=DemoBuildRulesLines(
            path="demo-build-rules.md",
            exists=True,
            line_count=2,
            lines={1: "Rule one", 2: "Rule two"},
        ),
        principles=["Preserve deterministic walkthroughs.", "Do not add plumbing."],
        source=RefinementSource(
            source_key="global_rules",
            title="Global hard rules",
            content="ignored in this prompt",
        ),
    )

    assert '"1": "Rule one"' in prompt
    assert "- Preserve deterministic walkthroughs." in prompt
    assert "- Do not add plumbing." in prompt


def test_build_rule_consolidation_user_prompt_includes_current_line_mapping() -> None:
    prompt = build_rule_consolidation_user_prompt(
        rules=DemoBuildRulesLines(
            path="demo-build-rules.md",
            exists=True,
            line_count=2,
            lines={1: "Rule one", 2: "Rule two"},
        )
    )

    assert '"1": "Rule one"' in prompt
    assert "consolidate repetitive rules" in prompt


def test_build_narrative_critique_user_prompt_includes_raw_rules_text() -> None:
    prompt = build_narrative_critique_user_prompt(
        rules_text="# Rules\n\n1. Start with context.\n2. Use clear terms."
    )

    assert "Current build rules raw text" in prompt
    assert "1. Start with context." in prompt
    assert "2. Use clear terms." in prompt


def test_build_narrative_improvement_user_prompt_includes_improvements_and_line_mapping() -> None:
    prompt = build_narrative_improvement_user_prompt(
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

    assert "Suggested narrative improvements" in prompt
    assert "- Clarify the opening procedure." in prompt
    assert "- Replace undefined jargon with plain language." in prompt
    assert '"1": "Rule one"' in prompt


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
    assert "    1 | Line 1" in diff
    assert "   12 | Line 12" in diff


def test_rule_refinement_service_runs_iterations_and_saves_versioned_outputs(
    tmp_path: Path,
) -> None:
    set_cache_dir_override(tmp_path / ".cache" / "rule_refinement" / "principles")
    try:
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
                _FakeResponse(output_text=json.dumps({"principles": ["Clarify rule two."]})),
                _FakeResponse(
                    output_text=json.dumps(
                        {
                            "replacements": [{"line_number": 2, "new_line": "Rule two updated"}],
                            "appends": ["Rule three"],
                        }
                    )
                ),
                _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
                _FakeResponse(output_text=json.dumps({"principles": ["Add rule four."]})),
                _FakeResponse(
                    output_text=json.dumps({"replacements": [], "appends": ["Rule four"]})
                ),
                _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
                *_narrative_tuning_responses(),
                _FakeResponse(
                    output_text=json.dumps(
                        {
                            "replacements": [{"line_number": 3, "new_line": "Rule three refined"}],
                            "appends": [],
                        }
                    )
                ),
                _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
                _FakeResponse(
                    output_text=json.dumps({"replacements": [], "appends": ["Rule five"]})
                ),
                _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
                *_narrative_tuning_responses(),
            ],
            randomizer=randomizer,
        )

        result = service.run(
            iterations=2,
            rules_path=rules_path,
            sources=[
                RefinementSource(
                    source_key="source_a",
                    title="Source A",
                    content="Source A content for extraction",
                ),
                RefinementSource(
                    source_key="source_b",
                    title="Source B",
                    content="Source B content for extraction",
                ),
            ],
        )

        assert result.final_rules_path.endswith("demo-build-rules.v014.md")
        assert result.iteration_results[0].output_artifact.rules_path.endswith("v007.md")
        assert result.iteration_results[0].narrative_tuning.output_artifact.rules_path.endswith(
            "v007.md"
        )
        assert (
            result.iteration_results[0]
            .narrative_tuning.pass_results[0]
            .output_artifact.rules_path.endswith("v005.md")
        )
        assert (
            result.iteration_results[0]
            .narrative_tuning.pass_results[1]
            .output_artifact.rules_path.endswith("v006.md")
        )
        assert (
            result.iteration_results[0]
            .narrative_tuning.pass_results[2]
            .output_artifact.rules_path.endswith("v007.md")
        )
        assert result.iteration_results[1].input_rules_path.endswith("v007.md")
        assert (
            result.iteration_results[0]
            .source_results[0]
            .applied_artifact.rules_path.endswith("v001.md")
        )
        assert (
            result.iteration_results[0]
            .source_results[0]
            .output_artifact.rules_path.endswith("v002.md")
        )
        assert (
            result.iteration_results[0]
            .source_results[1]
            .applied_artifact.rules_path.endswith("v003.md")
        )
        assert (
            result.iteration_results[0]
            .source_results[1]
            .output_artifact.rules_path.endswith("v004.md")
        )
        assert (
            result.iteration_results[1]
            .source_results[0]
            .applied_artifact.rules_path.endswith("v008.md")
        )
        assert (
            result.iteration_results[1]
            .source_results[0]
            .output_artifact.rules_path.endswith("v009.md")
        )
        assert (
            result.iteration_results[1]
            .source_results[1]
            .applied_artifact.rules_path.endswith("v010.md")
        )
        assert (
            result.iteration_results[1]
            .source_results[1]
            .output_artifact.rules_path.endswith("v011.md")
        )
        assert result.iteration_results[1].narrative_tuning.output_artifact.rules_path.endswith(
            "v014.md"
        )
        assert len(list(tmp_path.glob("demo-build-rules.v[0-9][0-9][0-9].md"))) == 14
        assert (tmp_path / "demo-build-rules.v001.md").read_text(encoding="utf-8").splitlines() == [
            "Rule one",
            "Rule two updated",
            "Rule three",
        ]
        assert (tmp_path / "demo-build-rules.v002.md").read_text(encoding="utf-8").splitlines() == [
            "Rule one",
            "Rule two updated",
            "Rule three",
        ]
        assert (tmp_path / "demo-build-rules.v003.md").read_text(encoding="utf-8").splitlines() == [
            "Rule one",
            "Rule two updated",
            "Rule three",
            "Rule four",
        ]
        assert (tmp_path / "demo-build-rules.v004.md").read_text(encoding="utf-8").splitlines() == [
            "Rule one",
            "Rule two updated",
            "Rule three",
            "Rule four",
        ]
        assert (tmp_path / "demo-build-rules.v007.md").read_text(encoding="utf-8").splitlines() == [
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
        ]
        assert (tmp_path / "demo-build-rules.v009.md").read_text(encoding="utf-8").splitlines() == [
            "Rule one",
            "Rule two updated",
            "Rule three refined",
            "Rule four",
        ]
        assert (tmp_path / "demo-build-rules.v010.md").read_text(encoding="utf-8").splitlines() == [
            "Rule one",
            "Rule two updated",
            "Rule three refined",
            "Rule four",
            "Rule five",
        ]
        assert (tmp_path / "demo-build-rules.v014.md").read_text(encoding="utf-8").splitlines() == [
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
        assert (tmp_path / "demo-build-rules.v001.diff.md").exists()
        assert (tmp_path / "demo-build-rules.v002.diff.md").exists()
        assert (tmp_path / "demo-build-rules.v003.diff.md").exists()
        assert (tmp_path / "demo-build-rules.v004.diff.md").exists()
        assert (tmp_path / "demo-build-rules.v005.diff.md").exists()
        assert (tmp_path / "demo-build-rules.v006.diff.md").exists()
        assert (tmp_path / "demo-build-rules.v007.diff.md").exists()
        assert (tmp_path / "demo-build-rules.v008.diff.md").exists()
        assert (tmp_path / "demo-build-rules.v009.diff.md").exists()
        assert (tmp_path / "demo-build-rules.v010.diff.md").exists()
        assert (tmp_path / "demo-build-rules.v011.diff.md").exists()
        assert (tmp_path / "demo-build-rules.v012.diff.md").exists()
        assert (tmp_path / "demo-build-rules.v013.diff.md").exists()
        assert (tmp_path / "demo-build-rules.v014.diff.md").exists()
        assert Path(result.iteration_results[0].narrative_tuning.critique_path).exists()
        assert Path(result.iteration_results[1].narrative_tuning.critique_path).exists()
        assert Path(
            result.iteration_results[0].narrative_tuning.pass_results[0].suggestion_path
        ).exists()
        assert Path(
            result.iteration_results[1].narrative_tuning.pass_results[2].suggestion_path
        ).exists()
    finally:
        set_cache_dir_override(None)


def test_rule_refinement_service_shuffles_source_order_each_iteration(tmp_path: Path) -> None:
    set_cache_dir_override(tmp_path / ".cache" / "rule_refinement" / "principles")
    try:
        rules_path = tmp_path / "demo-build-rules.md"
        rules_path.write_text("Rule one\n", encoding="utf-8")
        randomizer = _FakeRandomizer(
            shuffled_orders=[
                ["source_b", "source_a"],
                ["source_a", "source_b"],
            ]
        )
        service = _build_service(
            [
                _FakeResponse(output_text=json.dumps({"principles": ["B1"]})),
                _FakeResponse(
                    output_text=json.dumps({"replacements": [], "appends": ["Rule from B1"]})
                ),
                _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
                _FakeResponse(output_text=json.dumps({"principles": ["A1"]})),
                _FakeResponse(
                    output_text=json.dumps({"replacements": [], "appends": ["Rule from A1"]})
                ),
                _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
                *_narrative_tuning_responses(),
                _FakeResponse(
                    output_text=json.dumps({"replacements": [], "appends": ["Rule from A2"]})
                ),
                _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
                _FakeResponse(
                    output_text=json.dumps({"replacements": [], "appends": ["Rule from B2"]})
                ),
                _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
                *_narrative_tuning_responses(),
            ],
            randomizer=randomizer,
        )

        result = service.run(
            iterations=2,
            rules_path=rules_path,
            sources=[
                RefinementSource(source_key="source_a", title="Source A", content="A"),
                RefinementSource(source_key="source_b", title="Source B", content="B"),
            ],
        )

        assert randomizer.calls == 2
        assert [entry.source_key for entry in result.iteration_results[0].source_results] == [
            "source_b",
            "source_a",
        ]
        assert [entry.source_key for entry in result.iteration_results[1].source_results] == [
            "source_a",
            "source_b",
        ]
    finally:
        set_cache_dir_override(None)


def test_rule_refinement_service_builds_strict_responses_payloads(tmp_path: Path) -> None:
    set_cache_dir_override(tmp_path / ".cache" / "rule_refinement" / "principles")
    try:
        rules_path = tmp_path / "demo-build-rules.md"
        rules_path.write_text("Rule one\n", encoding="utf-8")
        service = _build_service(
            [
                _FakeResponse(output_text=json.dumps({"principles": ["Keep one clear rule."]})),
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
        )

        requests = service.responses_client.responses.requests
        assert requests[0]["reasoning"] == {"effort": "low"}
        assert requests[0]["text"]["format"]["strict"] is True
        assert requests[0]["text"]["format"]["name"] == "rule_refinement_principles"
        assert requests[1]["text"]["format"]["name"] == "rule_refinement_suggestions"
        assert requests[2]["text"]["format"]["name"] == "rule_refinement_consolidation"
        assert requests[3]["text"]["format"]["name"] == "rule_refinement_narrative_critique"
        assert requests[3]["reasoning"] == {"effort": "xhigh"}
        assert requests[4]["text"]["format"]["name"] == "rule_refinement_narrative_suggestions"
        assert requests[4]["reasoning"] == {"effort": "medium"}
        assert requests[5]["reasoning"] == {"effort": "medium"}
        assert requests[6]["reasoning"] == {"effort": "medium"}
        assert requests[0]["input"][0]["role"] == "developer"
        assert requests[0]["input"][1]["role"] == "user"
        assert '"1": "Rule one"' in requests[2]["input"][1]["content"]
        assert "Current build rules raw text" in requests[3]["input"][1]["content"]
        assert "Suggested narrative improvements" in requests[4]["input"][1]["content"]
    finally:
        set_cache_dir_override(None)


def test_rule_refinement_service_clamps_narrative_critique_effort_for_gpt5_mini(
    tmp_path: Path,
) -> None:
    set_cache_dir_override(tmp_path / ".cache" / "rule_refinement" / "principles")
    try:
        rules_path = tmp_path / "demo-build-rules.md"
        rules_path.write_text("Rule one\n", encoding="utf-8")
        client = _FakeClient(
            [
                _FakeResponse(output_text=json.dumps({"principles": ["Keep the rule."]})),
                _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
                _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
                *_narrative_tuning_responses(),
            ]
        )
        service = RuleRefinementService(
            responses_client=client,
            model="gpt-5-mini",
            reasoning_effort="low",
            response_wait_log_interval_seconds=0.01,
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
        )

        requests = client.responses.requests
        assert requests[3]["reasoning"] == {"effort": "high"}
        assert requests[4]["reasoning"] == {"effort": "medium"}
        assert requests[5]["reasoning"] == {"effort": "medium"}
        assert requests[6]["reasoning"] == {"effort": "medium"}
    finally:
        set_cache_dir_override(None)


def test_rule_refinement_service_narrative_tuning_uses_updated_rules_and_tracks_usage(
    tmp_path: Path,
) -> None:
    set_cache_dir_override(tmp_path / ".cache" / "rule_refinement" / "principles")
    try:
        rules_path = tmp_path / "demo-build-rules.md"
        rules_path.write_text("Rule one\n", encoding="utf-8")
        service = _build_service(
            [
                _FakeResponse(
                    output_text=json.dumps({"principles": ["Preserve the core rule."]}),
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
                    critique={
                        "critique": ["The rules read like isolated statements."],
                        "suggested_improvements": [
                            "Add a short heading that frames the procedure.",
                            "Make the first action explicit.",
                        ],
                    },
                    suggestions=[
                        {
                            "replacements": [{"line_number": 1, "new_line": "## Narrative Flow"}],
                            "appends": [],
                        },
                        {
                            "replacements": [],
                            "appends": ["1. Start by stating the user's goal."],
                        },
                        {
                            "replacements": [],
                            "appends": [],
                        },
                    ],
                    usages=[
                        {"input_tokens": 8, "output_tokens": 9, "total_tokens": 17},
                        {"input_tokens": 10, "output_tokens": 11, "total_tokens": 21},
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
                RefinementSource(source_key="source_a", title="Source A", content="Synthetic")
            ],
        )

        requests = service.responses_client.responses.requests
        assert '"1": "## Narrative Flow"' in requests[5]["input"][1]["content"]
        assert "1. Start by stating the user's goal." in requests[6]["input"][1]["content"]
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
        assert (
            result.iteration_results[0]
            .narrative_tuning.pass_results[1]
            .output_artifact.rules_path.endswith("v004.md")
        )
        assert Path(result.final_rules_path).read_text(encoding="utf-8").splitlines() == [
            "## Narrative Flow",
            "1. Start by stating the user's goal.",
        ]
    finally:
        set_cache_dir_override(None)


def test_rule_refinement_service_raises_for_invalid_suggestion_line_numbers(tmp_path: Path) -> None:
    set_cache_dir_override(tmp_path / ".cache" / "rule_refinement" / "principles")
    try:
        rules_path = tmp_path / "demo-build-rules.md"
        rules_path.write_text("Rule one\n", encoding="utf-8")
        service = _build_service(
            [
                _FakeResponse(output_text=json.dumps({"principles": ["Bad suggestion."]})),
                _FakeResponse(
                    output_text=json.dumps(
                        {"replacements": [{"line_number": 9, "new_line": "Bad line"}]}
                    )
                ),
                _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
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
            )
    finally:
        set_cache_dir_override(None)


def test_rule_refinement_service_raises_for_invalid_narrative_suggestion_line_numbers(
    tmp_path: Path,
) -> None:
    set_cache_dir_override(tmp_path / ".cache" / "rule_refinement" / "principles")
    try:
        rules_path = tmp_path / "demo-build-rules.md"
        rules_path.write_text("Rule one\n", encoding="utf-8")
        service = _build_service(
            [
                _FakeResponse(output_text=json.dumps({"principles": ["Keep the rule."]})),
                _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
                _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
                *_narrative_tuning_responses(
                    suggestions=[
                        {
                            "replacements": [{"line_number": 9, "new_line": "Bad line"}],
                            "appends": [],
                        },
                        {"replacements": [], "appends": []},
                        {"replacements": [], "appends": []},
                    ]
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
            )
    finally:
        set_cache_dir_override(None)


def test_content_hash_is_stable() -> None:
    assert content_hash("foo") == content_hash("foo")
    assert content_hash("foo") != content_hash("bar")


def test_get_cached_principles_miss_returns_none(tmp_path: Path) -> None:
    set_cache_dir_override(tmp_path / ".cache" / "rule_refinement" / "principles")
    try:
        assert get_cached_principles("nonexistent_hash") is None
    finally:
        set_cache_dir_override(None)


def test_get_cached_principles_hit_returns_cached(tmp_path: Path) -> None:
    set_cache_dir_override(tmp_path / ".cache" / "rule_refinement" / "principles")
    try:
        from app.x_to_demo.rule_refinement.models import ExtractedPrinciples

        principles = ExtractedPrinciples(principles=["P1", "P2"])
        h = content_hash("source content")
        set_cached_principles(h, principles)
        cached = get_cached_principles(h)
        assert cached is not None
        assert cached.principles == ["P1", "P2"]
    finally:
        set_cache_dir_override(None)


def test_split_rules_into_sections_no_headers() -> None:
    rules = DemoBuildRulesLines(
        path="test.md",
        exists=True,
        line_count=3,
        lines={1: "Line one", 2: "Line two", 3: "Line three"},
    )
    sections = split_rules_into_sections(rules)
    assert sections == [(1, 3)]


def test_split_rules_into_sections_with_equals_headers() -> None:
    rules = DemoBuildRulesLines(
        path="test.md",
        exists=True,
        line_count=6,
        lines={
            1: "Preamble",
            2: "=== SECTION A ===",
            3: "Content A",
            4: "=== SECTION B ===",
            5: "Content B",
            6: "More B",
        },
    )
    sections = split_rules_into_sections(rules)
    assert sections == [(1, 1), (2, 3), (4, 6)]


def test_split_rules_into_sections_with_atx_headers() -> None:
    rules = DemoBuildRulesLines(
        path="test.md",
        exists=True,
        line_count=5,
        lines={
            1: "# Title",
            2: "Intro",
            3: "## Section 1",
            4: "Body 1",
            5: "## Section 2",
        },
    )
    sections = split_rules_into_sections(rules)
    assert sections == [(1, 2), (3, 4), (5, 5)]


def test_split_rules_into_sections_empty_returns_empty() -> None:
    rules = DemoBuildRulesLines(
        path="test.md",
        exists=True,
        line_count=0,
        lines={},
    )
    sections = split_rules_into_sections(rules)
    assert sections == []


def test_build_rule_update_user_prompt_for_section_includes_section_label() -> None:
    prompt = build_rule_update_user_prompt_for_section(
        section_rules=DemoBuildRulesLines(
            path="test.md",
            exists=True,
            line_count=1,
            lines={5: "Rule line"},
        ),
        principles=["P1"],
        source=RefinementSource(source_key="sk", title="Title", content="C"),
        section_label="lines 5-5",
    )
    assert "Section: lines 5-5" in prompt
    assert '"5": "Rule line"' in prompt


def test_rule_refinement_service_batched_suggestions_reassembly(tmp_path: Path) -> None:
    """Multi-section document: verify merged replacements and ordered appends."""
    set_cache_dir_override(tmp_path / ".cache" / "rule_refinement" / "principles")
    try:
        rules_path = tmp_path / "demo-build-rules.md"
        rules_path.write_text(
            "=== SECTION A ===\nLine A1\nLine A2\n=== SECTION B ===\nLine B1\n",
            encoding="utf-8",
        )
        service = _build_service(
            [
                _FakeResponse(output_text=json.dumps({"principles": ["Update A2"]})),
                _FakeResponse(
                    output_text=json.dumps(
                        {
                            "replacements": [{"line_number": 3, "new_line": "Line A2 updated"}],
                            "appends": [],
                        }
                    )
                ),
                _FakeResponse(
                    output_text=json.dumps(
                        {
                            "replacements": [],
                            "appends": ["Appended from B"],
                        }
                    )
                ),
                _FakeResponse(output_text=json.dumps({"replacements": [], "appends": []})),
                *_narrative_tuning_responses(),
            ]
        )
        result = service.run(
            iterations=1,
            rules_path=rules_path,
            sources=[
                RefinementSource(
                    source_key="src",
                    title="Source",
                    content="Update section A line 2 and append from B",
                ),
            ],
        )
        final_path = result.iteration_results[0].output_artifact.rules_path
        final_text = (tmp_path / Path(final_path).name).read_text(encoding="utf-8")
        lines = final_text.splitlines()
        assert lines[2] == "Line A2 updated"
        assert lines[-1] == "Appended from B"
    finally:
        set_cache_dir_override(None)


@pytest.mark.integration
def test_live_openai_smoke_rule_refinement_narrative_critique() -> None:
    from openai import OpenAI

    api_key = _require_live_openai_smoke()
    service = RuleRefinementService(
        responses_client=OpenAI(api_key=api_key, timeout=1800.0),
        model="gpt-5.2",
        reasoning_effort="low",
        response_wait_log_interval_seconds=0.01,
    )

    critique, metrics = service._critique_narrative_structure(
        rules=DemoBuildRulesLines(
            path="demo-build-rules.md",
            exists=True,
            line_count=3,
            lines={
                1: "# Demo Build Rules",
                2: "Keep the scope small.",
                3: "Use clear language.",
            },
        )
    )

    assert critique.critique
    assert critique.suggested_improvements
    assert metrics.status == "completed"
    assert metrics.model_used


@pytest.mark.integration
def test_live_openai_smoke_rule_refinement_narrative_improvement() -> None:
    from openai import OpenAI

    api_key = _require_live_openai_smoke()
    service = RuleRefinementService(
        responses_client=OpenAI(api_key=api_key, timeout=1800.0),
        model="gpt-5.2",
        reasoning_effort="low",
        response_wait_log_interval_seconds=0.01,
    )

    suggestion, metrics = service._improve_narrative_structure(
        rules=DemoBuildRulesLines(
            path="demo-build-rules.md",
            exists=True,
            line_count=2,
            lines={
                1: "Rule one",
                2: "Rule two",
            },
        ),
        suggested_improvements=[
            "Add a clearer opening that frames the procedure.",
            "Use more explicit action wording.",
        ],
    )

    assert isinstance(suggestion.replacements, list)
    assert isinstance(suggestion.appends, list)
    assert metrics.status == "completed"
    assert metrics.model_used
