"""Internal service for iterative rule refinement extraction runs."""

from __future__ import annotations

import asyncio
import logging
import random
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.model_capabilities import (
    default_reasoning_effort,
    supported_reasoning_efforts,
    supports_reasoning,
    validate_model_name,
    validate_reasoning_effort,
)
from app.x_to_demo.pipeline.prompts import openai_compatible_schema
from app.x_to_demo.pipeline.responses import (
    call_responses_with_progress_logs,
    extract_model,
    extract_status,
    extract_structured_payload,
    extract_usage,
)

from .artifacts import (
    apply_rule_update_suggestions,
    canonical_rules_base_path,
    iteration_narrative_critique_path,
    lines_to_markdown,
    next_rules_version,
    save_iteration_artifacts,
    save_narrative_critique_artifact,
    save_narrative_suggestion_artifact,
    versioned_diff_path,
    versioned_narrative_suggestion_path,
    versioned_rules_path,
)
from .cache import content_hash, get_cached_principles, set_cached_principles
from .extractors import DemoBuildRulesLines, extract_refinement_inputs, load_demo_build_rules_lines
from .models import (
    ExtractedPrinciples,
    NarrativeCritique,
    NarrativeTuningIterationResult,
    NarrativeTuningPassResult,
    RefinementSource,
    RuleLineReplacement,
    RuleRefinementCallMetrics,
    RuleRefinementIterationResult,
    RuleRefinementRunResult,
    RuleRefinementSourceResult,
    RuleUpdateSuggestions,
)
from .prompts import (
    build_narrative_critique_developer_prompt,
    build_narrative_critique_user_prompt,
    build_narrative_improvement_developer_prompt,
    build_narrative_improvement_user_prompt,
    build_principle_extraction_developer_prompt,
    build_principle_extraction_user_prompt,
    build_rule_consolidation_developer_prompt,
    build_rule_consolidation_user_prompt,
    build_rule_update_developer_prompt,
    build_rule_update_user_prompt_for_section,
)
from .sections import split_rules_into_sections

logger = logging.getLogger(__name__)

_REASONING_EFFORT_ORDER = ("none", "minimal", "low", "medium", "high", "xhigh")


class RuleRefinementService:
    """Runs iterative rule refinement with extraction, update, and consolidation calls."""

    def __init__(
        self,
        *,
        responses_client: object,
        model: str,
        reasoning_effort: str,
        store_responses: bool = False,
        response_wait_log_interval_seconds: float = 15.0,
        randomizer: random.Random | None = None,
    ) -> None:
        self.responses_client = responses_client
        self.model = validate_model_name(model_name=model)
        self.reasoning_effort = validate_reasoning_effort(
            model_name=self.model,
            reasoning_effort=reasoning_effort or default_reasoning_effort(model_name=self.model),
        )
        self.store_responses = store_responses
        self.response_wait_log_interval_seconds = max(response_wait_log_interval_seconds, 0.1)
        self.randomizer = randomizer or random.Random()

    def run(
        self,
        *,
        iterations: int,
        rules_path: Path | None = None,
        sources: list[RefinementSource] | None = None,
    ) -> RuleRefinementRunResult:
        """Execute the full refinement loop for the requested number of iterations."""
        if iterations < 1:
            raise ValueError("iterations must be at least 1")

        extracted_sources = sources or extract_refinement_inputs()
        if not extracted_sources:
            raise ValueError("No refinement sources were extracted")

        base_rules = load_demo_build_rules_lines(rules_path)
        current_rules_path = Path(base_rules.path)
        canonical_rules_path = canonical_rules_base_path(current_rules_path)
        current_rules = base_rules
        iteration_results: list[RuleRefinementIterationResult] = []
        usage_totals: dict[str, int] = {}

        for iteration_number in range(1, iterations + 1):
            iteration_start_rules_path = str(current_rules_path)
            source_results: list[RuleRefinementSourceResult] = []
            iteration_sources = list(extracted_sources)
            self.randomizer.shuffle(iteration_sources)
            last_artifact = None

            for source in iteration_sources:
                source_input_rules = DemoBuildRulesLines.model_validate(current_rules.model_dump())
                extracted_principles, extraction_metrics = self._extract_principles(source)
                suggestion, suggestion_metrics = self._suggest_rule_updates(
                    rules=source_input_rules,
                    principles=extracted_principles.principles,
                    source=source,
                )
                updated_rules = apply_rule_update_suggestions(source_input_rules, suggestion)
                applied_version = next_rules_version(current_rules_path)
                applied_output_path = versioned_rules_path(canonical_rules_path, applied_version)
                applied_diff_path = versioned_diff_path(canonical_rules_path, applied_version)
                applied_artifact = save_iteration_artifacts(
                    previous=source_input_rules,
                    updated=DemoBuildRulesLines(
                        path=str(applied_output_path),
                        exists=True,
                        line_count=updated_rules.line_count,
                        lines=updated_rules.lines,
                    ),
                    output_path=applied_output_path,
                    diff_path=applied_diff_path,
                    version=applied_version,
                    canonical_rules_path=canonical_rules_path,
                )
                consolidation_input_rules = self._freshly_loaded_rules(
                    load_path=canonical_rules_path,
                    display_path=applied_output_path,
                )
                consolidation_suggestion, consolidation_metrics = self._consolidate_rules(
                    rules=consolidation_input_rules
                )
                consolidated_rules = apply_rule_update_suggestions(
                    consolidation_input_rules,
                    consolidation_suggestion,
                )
                consolidated_version = next_rules_version(applied_output_path)
                consolidated_output_path = versioned_rules_path(
                    canonical_rules_path, consolidated_version
                )
                consolidated_diff_path = versioned_diff_path(
                    canonical_rules_path, consolidated_version
                )
                consolidated_artifact = save_iteration_artifacts(
                    previous=consolidation_input_rules,
                    updated=DemoBuildRulesLines(
                        path=str(consolidated_output_path),
                        exists=True,
                        line_count=consolidated_rules.line_count,
                        lines=consolidated_rules.lines,
                    ),
                    output_path=consolidated_output_path,
                    diff_path=consolidated_diff_path,
                    version=consolidated_version,
                    canonical_rules_path=canonical_rules_path,
                )
                source_results.append(
                    RuleRefinementSourceResult(
                        source_key=source.source_key,
                        title=source.title,
                        input_rules_path=str(current_rules_path),
                        principles=extracted_principles.principles,
                        suggestion=suggestion,
                        extraction_metrics=extraction_metrics,
                        suggestion_metrics=suggestion_metrics,
                        applied_artifact=applied_artifact,
                        consolidation_suggestion=consolidation_suggestion,
                        consolidation_metrics=consolidation_metrics,
                        output_artifact=consolidated_artifact,
                    )
                )
                usage_totals = _merge_usage_totals(
                    usage_totals,
                    extraction_metrics.usage,
                    suggestion_metrics.usage,
                    consolidation_metrics.usage,
                )
                current_rules_path = consolidated_output_path
                current_rules = DemoBuildRulesLines(
                    path=str(consolidated_output_path),
                    exists=True,
                    line_count=consolidated_rules.line_count,
                    lines=consolidated_rules.lines,
                )
                last_artifact = consolidated_artifact

            if last_artifact is None:
                raise RuntimeError(
                    "Rule refinement iteration completed without processing any sources"
                )
            narrative_tuning_result, narrative_rules = self._run_narrative_tuning(
                rules=current_rules,
                iteration_number=iteration_number,
                canonical_rules_path=canonical_rules_path,
            )
            usage_totals = _merge_usage_totals(
                usage_totals,
                narrative_tuning_result.critique_metrics.usage,
                *(
                    pass_result.suggestion_metrics.usage
                    for pass_result in narrative_tuning_result.pass_results
                ),
            )
            current_rules_path = Path(narrative_tuning_result.output_artifact.rules_path)
            current_rules = narrative_rules
            iteration_results.append(
                RuleRefinementIterationResult(
                    iteration_number=iteration_number,
                    input_rules_path=iteration_start_rules_path,
                    output_artifact=narrative_tuning_result.output_artifact,
                    narrative_tuning=narrative_tuning_result,
                    source_results=source_results,
                )
            )

        return RuleRefinementRunResult(
            iterations=iterations,
            initial_rules_path=base_rules.path,
            final_rules_path=str(current_rules_path),
            source_count=len(extracted_sources),
            iteration_results=iteration_results,
            usage_totals=usage_totals,
        )

    def _extract_principles(
        self, source: RefinementSource
    ) -> tuple[ExtractedPrinciples, RuleRefinementCallMetrics]:
        h = content_hash(source.content)
        cached = get_cached_principles(h)
        if cached is not None:
            return cached, RuleRefinementCallMetrics(
                model_used=self.model,
                status="cached",
                usage={},
            )
        developer_prompt = build_principle_extraction_developer_prompt()
        user_prompt = build_principle_extraction_user_prompt(source)
        principles, metrics = self._run_structured_call(
            schema_name="rule_refinement_principles",
            output_model=ExtractedPrinciples,
            developer_prompt=developer_prompt,
            user_prompt=user_prompt,
            phase_key="rule_refinement_principles",
        )
        set_cached_principles(h, principles)
        return principles, metrics

    def _suggest_rule_updates(
        self,
        *,
        rules: DemoBuildRulesLines,
        principles: list[str],
        source: RefinementSource,
    ) -> tuple[RuleUpdateSuggestions, RuleRefinementCallMetrics]:
        return asyncio.run(
            self._suggest_rule_updates_async(
                rules=rules,
                principles=principles,
                source=source,
            )
        )

    async def _suggest_rule_updates_async(
        self,
        *,
        rules: DemoBuildRulesLines,
        principles: list[str],
        source: RefinementSource,
    ) -> tuple[RuleUpdateSuggestions, RuleRefinementCallMetrics]:
        sections = split_rules_into_sections(rules)
        if not sections:
            return RuleUpdateSuggestions(), RuleRefinementCallMetrics(
                model_used=self.model,
                status="completed",
                usage={},
            )

        sem = asyncio.Semaphore(8)
        developer_prompt = build_rule_update_developer_prompt()

        async def process_section(
            section_index: int,
            start_line: int,
            end_line: int,
        ) -> tuple[int, RuleUpdateSuggestions, RuleRefinementCallMetrics]:
            section_lines = {
                ln: rules.lines[ln] for ln in range(start_line, end_line + 1) if ln in rules.lines
            }
            section_rules = DemoBuildRulesLines(
                path=rules.path,
                exists=True,
                line_count=len(section_lines),
                lines=section_lines,
            )
            section_label = f"lines {start_line}-{end_line}"
            user_prompt = build_rule_update_user_prompt_for_section(
                section_rules=section_rules,
                principles=principles,
                source=source,
                section_label=section_label,
            )
            async with sem:
                suggestion, metrics = await asyncio.to_thread(
                    self._run_structured_call,
                    schema_name="rule_refinement_suggestions",
                    output_model=RuleUpdateSuggestions,
                    developer_prompt=developer_prompt,
                    user_prompt=user_prompt,
                    phase_key="rule_refinement_suggestions",
                )
            for repl in suggestion.replacements:
                if repl.line_number < start_line or repl.line_number > end_line:
                    logger.warning(
                        "Section %s returned replacement for line %d outside range %d-%d",
                        section_label,
                        repl.line_number,
                        start_line,
                        end_line,
                    )
            return section_index, suggestion, metrics

        tasks = [process_section(i, start, end) for i, (start, end) in enumerate(sections)]
        results = await asyncio.gather(*tasks)
        results_sorted = sorted(results, key=lambda r: r[0])

        all_replacements: list[RuleLineReplacement] = []
        all_appends: list[str] = []
        all_rationale: list[str] = []
        merged_usage: dict[str, int] = {}

        for _, suggestion, metrics in results_sorted:
            all_replacements.extend(suggestion.replacements)
            all_appends.extend(suggestion.appends)
            all_rationale.extend(suggestion.rationale)
            merged_usage = _merge_usage_totals(merged_usage, metrics.usage)

        replacements_deduped = {r.line_number: r for r in all_replacements}
        merged_replacements = sorted(
            replacements_deduped.values(),
            key=lambda r: r.line_number,
        )

        return (
            RuleUpdateSuggestions(
                replacements=merged_replacements,
                appends=all_appends,
                rationale=all_rationale,
            ),
            RuleRefinementCallMetrics(
                model_used=self.model,
                status="completed",
                usage=merged_usage,
            ),
        )

    def _consolidate_rules(
        self, *, rules: DemoBuildRulesLines
    ) -> tuple[RuleUpdateSuggestions, RuleRefinementCallMetrics]:
        developer_prompt = build_rule_consolidation_developer_prompt()
        user_prompt = build_rule_consolidation_user_prompt(rules=rules)
        return self._run_structured_call(
            schema_name="rule_refinement_consolidation",
            output_model=RuleUpdateSuggestions,
            developer_prompt=developer_prompt,
            user_prompt=user_prompt,
            phase_key="rule_refinement_consolidation",
        )

    def _run_narrative_tuning(
        self,
        *,
        rules: DemoBuildRulesLines,
        iteration_number: int,
        canonical_rules_path: Path,
    ) -> tuple[NarrativeTuningIterationResult, DemoBuildRulesLines]:
        critique, critique_metrics = self._critique_narrative_structure(rules=rules)
        critique_path = iteration_narrative_critique_path(canonical_rules_path, iteration_number)
        save_narrative_critique_artifact(output_path=critique_path, critique=critique)

        current_rules = DemoBuildRulesLines.model_validate(rules.model_dump())
        pass_results: list[NarrativeTuningPassResult] = []

        for pass_number in range(1, 4):
            suggestion, suggestion_metrics = self._improve_narrative_structure(
                rules=current_rules,
                suggested_improvements=critique.suggested_improvements,
            )
            updated_rules = apply_rule_update_suggestions(current_rules, suggestion)
            output_version = next_rules_version(Path(current_rules.path))
            output_path = versioned_rules_path(canonical_rules_path, output_version)
            diff_path = versioned_diff_path(canonical_rules_path, output_version)
            suggestion_path = versioned_narrative_suggestion_path(
                canonical_rules_path,
                output_version,
                pass_number,
            )
            output_artifact = save_iteration_artifacts(
                previous=current_rules,
                updated=DemoBuildRulesLines(
                    path=str(output_path),
                    exists=True,
                    line_count=updated_rules.line_count,
                    lines=updated_rules.lines,
                ),
                output_path=output_path,
                diff_path=diff_path,
                version=output_version,
                canonical_rules_path=canonical_rules_path,
            )
            save_narrative_suggestion_artifact(output_path=suggestion_path, suggestion=suggestion)
            pass_results.append(
                NarrativeTuningPassResult(
                    pass_number=pass_number,
                    input_rules_path=current_rules.path,
                    suggestion=suggestion,
                    suggestion_metrics=suggestion_metrics,
                    suggestion_path=str(suggestion_path),
                    output_artifact=output_artifact,
                )
            )
            current_rules = DemoBuildRulesLines(
                path=str(output_path),
                exists=True,
                line_count=updated_rules.line_count,
                lines=updated_rules.lines,
            )

        if not pass_results:
            raise RuntimeError("Narrative tuning completed without any improvement passes")

        return (
            NarrativeTuningIterationResult(
                input_rules_path=rules.path,
                critique=critique,
                critique_metrics=critique_metrics,
                critique_path=str(critique_path),
                pass_results=pass_results,
                output_artifact=pass_results[-1].output_artifact,
            ),
            current_rules,
        )

    def _critique_narrative_structure(
        self, *, rules: DemoBuildRulesLines
    ) -> tuple[NarrativeCritique, RuleRefinementCallMetrics]:
        developer_prompt = build_narrative_critique_developer_prompt()
        user_prompt = build_narrative_critique_user_prompt(
            rules_text=lines_to_markdown(rules.lines)
        )
        return self._run_structured_call(
            schema_name="rule_refinement_narrative_critique",
            output_model=NarrativeCritique,
            developer_prompt=developer_prompt,
            user_prompt=user_prompt,
            phase_key="rule_refinement_narrative_critique",
            reasoning_effort="xhigh",
        )

    def _improve_narrative_structure(
        self,
        *,
        rules: DemoBuildRulesLines,
        suggested_improvements: list[str],
    ) -> tuple[RuleUpdateSuggestions, RuleRefinementCallMetrics]:
        developer_prompt = build_narrative_improvement_developer_prompt()
        user_prompt = build_narrative_improvement_user_prompt(
            rules=rules,
            suggested_improvements=suggested_improvements,
        )
        return self._run_structured_call(
            schema_name="rule_refinement_narrative_suggestions",
            output_model=RuleUpdateSuggestions,
            developer_prompt=developer_prompt,
            user_prompt=user_prompt,
            phase_key="rule_refinement_narrative_suggestions",
            reasoning_effort="medium",
        )

    def _run_structured_call(
        self,
        *,
        schema_name: str,
        output_model: type[ExtractedPrinciples | NarrativeCritique | RuleUpdateSuggestions],
        developer_prompt: str,
        user_prompt: str,
        phase_key: str,
        reasoning_effort: str | None = None,
    ) -> tuple[Any, RuleRefinementCallMetrics]:
        payload: dict[str, object] = {
            "model": self.model,
            "store": self.store_responses,
            "input": [
                {"role": "developer", "content": developer_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": openai_compatible_schema(output_model.model_json_schema()),
                    "strict": True,
                }
            },
        }
        selected_reasoning_effort = self._resolve_requested_reasoning_effort(reasoning_effort)

        if supports_reasoning(self.model):
            payload["reasoning"] = {"effort": selected_reasoning_effort}

        response = call_responses_with_progress_logs(
            create_call=self.responses_client.responses.create,
            payload=payload,
            phase_key=phase_key,  # type: ignore[arg-type]
            response_wait_log_interval_seconds=self.response_wait_log_interval_seconds,
            default_model=self.model,
            logger=logger,
        )
        parsed_payload = extract_structured_payload(response)
        validated_output = output_model.model_validate(parsed_payload)
        metrics = RuleRefinementCallMetrics(
            model_used=extract_model(response) or self.model,
            status=extract_status(response),
            usage=extract_usage(response),
        )
        return validated_output, metrics

    def _resolve_requested_reasoning_effort(self, reasoning_effort: str | None) -> str:
        """Clamp stage-specific reasoning requests to the highest effort supported by the model."""
        if reasoning_effort is None:
            return self.reasoning_effort

        try:
            return validate_reasoning_effort(
                model_name=self.model,
                reasoning_effort=reasoning_effort,
            )
        except ValueError:
            allowed = supported_reasoning_efforts(self.model)
            requested = str(reasoning_effort).strip().lower()
            if not allowed or requested not in _REASONING_EFFORT_ORDER:
                raise

            requested_index = _REASONING_EFFORT_ORDER.index(requested)
            supported_sorted = sorted(
                allowed,
                key=lambda effort: _REASONING_EFFORT_ORDER.index(effort),
            )
            fallback = next(
                (
                    effort
                    for effort in reversed(supported_sorted)
                    if _REASONING_EFFORT_ORDER.index(effort) <= requested_index
                ),
                supported_sorted[0],
            )
            logger.info(
                "Adjusted requested reasoning effort for unsupported model override",
                extra={
                    "model": self.model,
                    "requested_reasoning_effort": requested,
                    "fallback_reasoning_effort": fallback,
                },
            )
            return fallback

    @staticmethod
    def _freshly_loaded_rules(*, load_path: Path, display_path: Path) -> DemoBuildRulesLines:
        """Reload the rules from disk while preserving the relevant versioned path label."""
        loaded_rules = load_demo_build_rules_lines(load_path)
        return DemoBuildRulesLines(
            path=str(display_path),
            exists=loaded_rules.exists,
            line_count=loaded_rules.line_count,
            lines=loaded_rules.lines,
        )


def build_rule_refinement_service(
    *, responses_client: object | None = None
) -> RuleRefinementService:
    """Create a rule refinement service using configured defaults."""
    client = responses_client or _build_openai_client()
    return RuleRefinementService(
        responses_client=client,
        model=settings.rule_refinement_model,
        reasoning_effort=settings.rule_refinement_reasoning_effort,
    )


def _build_openai_client() -> object:
    """Build the OpenAI client lazily so imports remain test-friendly."""
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - covered by existing pipeline tests
        raise RuntimeError(
            "openai package is not installed. Add dependency and reinstall API environment."
        ) from exc
    return OpenAI(api_key=settings.openai_api_key, timeout=1800.0)


def _merge_usage_totals(existing: dict[str, int], *usages: dict[str, int]) -> dict[str, int]:
    """Merge usage dictionaries without dropping missing keys."""
    merged = dict(existing)
    for usage in usages:
        for key, value in usage.items():
            merged[key] = merged.get(key, 0) + int(value or 0)
    return merged
