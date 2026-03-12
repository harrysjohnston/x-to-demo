"""Internal service for iterative rule refinement extraction runs."""

from __future__ import annotations

import asyncio
import logging
import random
import re
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
from app.x_to_demo.pipeline.pricing import estimate_cost, merge_costs
from app.x_to_demo.pipeline.prompts import openai_compatible_schema
from app.x_to_demo.pipeline.responses import (
    call_responses_with_progress_logs,
    extract_model,
    extract_output_text,
    extract_status,
    extract_structured_payload,
    extract_usage,
)

from .artifacts import (
    apply_rule_update_suggestions,
    canonical_rules_base_path,
    iteration_narrative_critique_path,
    iteration_source_analysis_path,
    lines_to_markdown,
    next_rules_version,
    save_iteration_artifacts,
    save_narrative_critique_artifact,
    save_narrative_suggestion_artifact,
    save_reduction_critique_artifact,
    save_reduction_suggestion_artifact,
    save_rule_update_suggestion_artifact,
    save_source_analysis_artifact,
    versioned_diff_path,
    versioned_narrative_suggestion_path,
    versioned_reduction_critic_path,
    versioned_reduction_suggestion_path,
    versioned_rules_path,
    versioned_source_suggestion_path,
)
from .extractors import DemoBuildRulesLines, extract_refinement_inputs, load_demo_build_rules_lines
from .metrics_persistence import save_run_manifest, save_usage_metrics
from .models import (
    NarrativeCritique,
    NarrativeTuningIterationResult,
    NarrativeTuningPassResult,
    ReductionCriticResult,
    ReductionCritique,
    ReductionEditorResult,
    ReductionLoopResult,
    ReductionPassResult,
    RefinementSource,
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
)

logger = logging.getLogger(__name__)

_REASONING_EFFORT_ORDER = ("none", "minimal", "low", "medium", "high", "xhigh")


class CostLimitExceededError(Exception):
    """Raised when rule refinement accumulated cost exceeds the configured limit."""

    def __init__(self, accumulated_cost: float, limit: float) -> None:
        self.accumulated_cost = accumulated_cost
        self.limit = limit
        super().__init__(f"Cost limit ${limit:.2f} exceeded (accumulated ${accumulated_cost:.4f})")


class RuleRefinementService:
    """Runs iterative rule refinement with analysis, improvement, and consolidation calls."""

    def __init__(
        self,
        *,
        responses_client: Any,
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

    def _log_run_start(
        self,
        *,
        iterations: int,
        rules: DemoBuildRulesLines,
        sources: list[RefinementSource],
        cost_limit: float | None,
    ) -> None:
        logger.info(
            "Starting rule refinement run\n"
            "Iterations: %d\n"
            "Model: %s\n"
            "Reasoning effort: %s\n"
            "Starting rules: %s (%d lines)\n"
            "Sources: %d [%s]\n"
            "Cost limit: %s",
            iterations,
            self.model,
            self.reasoning_effort,
            rules.path,
            rules.line_count,
            len(sources),
            _format_source_list(sources),
            f"${cost_limit:.2f}" if cost_limit is not None else "none",
        )

    def _log_iteration_start(
        self,
        *,
        iteration_number: int,
        iterations: int,
        rules: DemoBuildRulesLines,
        sources: list[RefinementSource],
    ) -> None:
        logger.info(
            "Starting rule refinement iteration %d/%d\n"
            "Input rules: %s (%d lines)\n"
            "Source order: %s",
            iteration_number,
            iterations,
            rules.path,
            rules.line_count,
            _format_source_list(sources),
        )

    def _log_analysis_batch_complete(
        self,
        *,
        iteration_number: int,
        results: dict[str, tuple[str, RuleRefinementCallMetrics]],
    ) -> None:
        combined_usage: dict[str, int] = {}
        combined_cost: dict[str, float] | None = None
        analyses = []
        for source_key, (analysis, metrics) in results.items():
            combined_usage = _merge_usage_totals(combined_usage, metrics.usage)
            combined_cost = _merge_cost_totals(combined_cost, metrics.cost)
            analyses.append(f"{source_key} ({_preview_text(analysis, limit=80)})")

        logger.info(
            "Completed concurrent source-gap analysis for iteration %d\n"
            "Analyses: %d\n"
            "Analysis summaries: %s\n"
            "Analysis usage: %s\n"
            "Analysis cost: %s",
            iteration_number,
            len(results),
            "; ".join(analyses) if analyses else "none",
            _format_usage_summary(combined_usage),
            _format_cost_summary(combined_cost),
        )

    def _log_source_improvement_start(
        self,
        *,
        iteration_number: int,
        source: RefinementSource,
        rules: DemoBuildRulesLines,
    ) -> None:
        logger.info(
            "Starting source improvement\n"
            "Iteration: %d\n"
            "Source: %s (%s)\n"
            "Input rules: %s (%d lines)",
            iteration_number,
            source.source_key,
            source.title,
            rules.path,
            rules.line_count,
        )

    def _log_source_improvement_complete(
        self,
        *,
        iteration_number: int,
        source: RefinementSource,
        analysis_path: Path,
        suggestion_path: Path,
        artifact: object,
        analysis_metrics: RuleRefinementCallMetrics,
        suggestion_metrics: RuleRefinementCallMetrics,
        suggestion: RuleUpdateSuggestions,
    ) -> None:
        changed_lines = getattr(artifact, "changed_line_numbers", [])
        output_rules = getattr(artifact, "rules_path", "")
        logger.info(
            "Completed source improvement\n"
            "Iteration: %d\n"
            "Source: %s (%s)\n"
            "Analysis artifact: %s\n"
            "Suggestion artifact: %s\n"
            "Output rules: %s\n"
            "Changes: %s\n"
            "Suggestion summary: %s\n"
            "Analysis usage/cost: %s | %s\n"
            "Improvement usage/cost: %s | %s",
            iteration_number,
            source.source_key,
            source.title,
            analysis_path,
            suggestion_path,
            output_rules,
            _format_changed_lines(changed_lines),
            _format_suggestion_summary(suggestion),
            _format_usage_summary(analysis_metrics.usage),
            _format_cost_summary(analysis_metrics.cost),
            _format_usage_summary(suggestion_metrics.usage),
            _format_cost_summary(suggestion_metrics.cost),
        )

    def _log_consolidation_start(
        self,
        *,
        iteration_number: int,
        rules: DemoBuildRulesLines,
    ) -> None:
        logger.info(
            "Starting consolidation\nIteration: %d\nInput rules: %s (%d lines)",
            iteration_number,
            rules.path,
            rules.line_count,
        )

    def _log_consolidation_complete(
        self,
        *,
        iteration_number: int,
        artifact: object,
        metrics: RuleRefinementCallMetrics,
        suggestion: RuleUpdateSuggestions,
    ) -> None:
        logger.info(
            "Completed consolidation\n"
            "Iteration: %d\n"
            "Output rules: %s\n"
            "Changes: %s\n"
            "Suggestion summary: %s\n"
            "Usage/cost: %s | %s",
            iteration_number,
            getattr(artifact, "rules_path", ""),
            _format_changed_lines(getattr(artifact, "changed_line_numbers", [])),
            _format_suggestion_summary(suggestion),
            _format_usage_summary(metrics.usage),
            _format_cost_summary(metrics.cost),
        )

    def _log_narrative_critique_start(
        self,
        *,
        iteration_number: int,
        rules: DemoBuildRulesLines,
    ) -> None:
        logger.info(
            "Starting narrative critique\nIteration: %d\nInput rules: %s (%d lines)",
            iteration_number,
            rules.path,
            rules.line_count,
        )

    def _log_narrative_critique_complete(
        self,
        *,
        iteration_number: int,
        critique: NarrativeCritique,
        critique_path: Path,
        metrics: RuleRefinementCallMetrics,
    ) -> None:
        logger.info(
            "Completed narrative critique\n"
            "Iteration: %d\n"
            "Critique artifact: %s\n"
            "Critique points: %d\n"
            "Suggested improvements: %d\n"
            "Critique preview: %s\n"
            "Usage/cost: %s | %s",
            iteration_number,
            critique_path,
            len(critique.critique),
            len(critique.suggested_improvements),
            _preview_text("; ".join(critique.suggested_improvements), limit=120),
            _format_usage_summary(metrics.usage),
            _format_cost_summary(metrics.cost),
        )

    def _log_narrative_improvement_complete(
        self,
        *,
        iteration_number: int,
        pass_number: int,
        suggestion_path: Path,
        artifact: object,
        metrics: RuleRefinementCallMetrics,
        suggestion: RuleUpdateSuggestions,
    ) -> None:
        logger.info(
            "Completed narrative improvement\n"
            "Iteration: %d\n"
            "Pass: %d\n"
            "Suggestion artifact: %s\n"
            "Output rules: %s\n"
            "Changes: %s\n"
            "Suggestion summary: %s\n"
            "Usage/cost: %s | %s",
            iteration_number,
            pass_number,
            suggestion_path,
            getattr(artifact, "rules_path", ""),
            _format_changed_lines(getattr(artifact, "changed_line_numbers", [])),
            _format_suggestion_summary(suggestion),
            _format_usage_summary(metrics.usage),
            _format_cost_summary(metrics.cost),
        )

    def run(
        self,
        *,
        iterations: int,
        rules_path: Path | None = None,
        sources: list[RefinementSource] | None = None,
        cost_limit: float | None = None,
        reduction_passes: int = 3,
        reduction_notes: list[str] | None = None,
    ) -> RuleRefinementRunResult:
        """Execute the full refinement loop for the requested number of iterations."""
        if iterations < 1:
            raise ValueError("iterations must be at least 1")
        if cost_limit is not None and cost_limit <= 0:
            raise ValueError("cost_limit must be positive")
        if reduction_passes < 0:
            raise ValueError("reduction_passes must be non-negative")

        extracted_sources = sources or extract_refinement_inputs()
        if not extracted_sources:
            raise ValueError("No refinement sources were extracted")

        base_rules = load_demo_build_rules_lines(rules_path)
        current_rules_path = Path(base_rules.path)
        canonical_rules_path = canonical_rules_base_path(current_rules_path)
        current_rules = base_rules
        iteration_results: list[RuleRefinementIterationResult] = []
        usage_totals: dict[str, int] = {}
        cost_totals: dict[str, float] | None = None

        self._log_run_start(
            iterations=iterations,
            rules=base_rules,
            sources=extracted_sources,
            cost_limit=cost_limit,
        )

        for iteration_number in range(1, iterations + 1):
            iteration_start_rules_path = str(current_rules_path)
            source_results: list[RuleRefinementSourceResult] = []
            iteration_sources = list(extracted_sources)
            self.randomizer.shuffle(iteration_sources)
            self._log_iteration_start(
                iteration_number=iteration_number,
                iterations=iterations,
                rules=current_rules,
                sources=iteration_sources,
            )
            analysis_input_rules = DemoBuildRulesLines.model_validate(current_rules.model_dump())
            source_analyses = self._analyze_sources(
                rules=analysis_input_rules,
                sources=iteration_sources,
            )
            self._log_analysis_batch_complete(
                iteration_number=iteration_number,
                results=source_analyses,
            )

            for source in iteration_sources:
                source_input_rules = DemoBuildRulesLines.model_validate(current_rules.model_dump())
                self._log_source_improvement_start(
                    iteration_number=iteration_number,
                    source=source,
                    rules=source_input_rules,
                )
                analysis, analysis_metrics = source_analyses[source.source_key]
                analysis_path = iteration_source_analysis_path(
                    canonical_rules_path,
                    iteration_number,
                    source.source_key,
                )
                save_source_analysis_artifact(output_path=analysis_path, analysis=analysis)
                suggestion, suggestion_metrics = self._suggest_rule_updates(
                    rules=source_input_rules,
                    analysis=analysis,
                    source=source,
                )
                output_version = next_rules_version(current_rules_path)
                suggestion_path = versioned_source_suggestion_path(
                    canonical_rules_path,
                    output_version,
                    source.source_key,
                )
                save_rule_update_suggestion_artifact(
                    output_path=suggestion_path,
                    suggestion=suggestion,
                )
                updated_rules = apply_rule_update_suggestions(source_input_rules, suggestion)
                output_path = versioned_rules_path(canonical_rules_path, output_version)
                diff_path = versioned_diff_path(canonical_rules_path, output_version)
                source_artifact = save_iteration_artifacts(
                    previous=source_input_rules,
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
                source_results.append(
                    RuleRefinementSourceResult(
                        source_key=source.source_key,
                        title=source.title,
                        input_rules_path=str(current_rules_path),
                        analysis=analysis,
                        analysis_path=str(analysis_path),
                        suggestion=suggestion,
                        analysis_metrics=analysis_metrics,
                        suggestion_metrics=suggestion_metrics,
                        suggestion_path=str(suggestion_path),
                        output_artifact=source_artifact,
                    )
                )
                usage_totals = _merge_usage_totals(
                    usage_totals,
                    analysis_metrics.usage,
                    suggestion_metrics.usage,
                )
                cost_totals = _merge_cost_totals(
                    cost_totals,
                    analysis_metrics.cost,
                    suggestion_metrics.cost,
                )
                _check_cost_limit(cost_totals, cost_limit)
                current_rules_path = output_path
                current_rules = DemoBuildRulesLines(
                    path=str(output_path),
                    exists=True,
                    line_count=updated_rules.line_count,
                    lines=updated_rules.lines,
                )
                self._log_source_improvement_complete(
                    iteration_number=iteration_number,
                    source=source,
                    analysis_path=analysis_path,
                    suggestion_path=suggestion_path,
                    artifact=source_artifact,
                    analysis_metrics=analysis_metrics,
                    suggestion_metrics=suggestion_metrics,
                    suggestion=suggestion,
                )
            if not source_results:
                raise RuntimeError(
                    "Rule refinement iteration completed without processing any sources"
                )
            consolidation_input_rules = DemoBuildRulesLines.model_validate(
                current_rules.model_dump()
            )
            self._log_consolidation_start(
                iteration_number=iteration_number,
                rules=consolidation_input_rules,
            )
            consolidation_suggestion, consolidation_metrics = self._consolidate_rules(
                rules=consolidation_input_rules
            )
            consolidated_rules = apply_rule_update_suggestions(
                consolidation_input_rules,
                consolidation_suggestion,
            )
            consolidated_version = next_rules_version(current_rules_path)
            consolidated_output_path = versioned_rules_path(
                canonical_rules_path, consolidated_version
            )
            consolidated_diff_path = versioned_diff_path(canonical_rules_path, consolidated_version)
            consolidation_artifact = save_iteration_artifacts(
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
            usage_totals = _merge_usage_totals(usage_totals, consolidation_metrics.usage)
            cost_totals = _merge_cost_totals(cost_totals, consolidation_metrics.cost)
            _check_cost_limit(cost_totals, cost_limit)
            current_rules_path = consolidated_output_path
            current_rules = DemoBuildRulesLines(
                path=str(consolidated_output_path),
                exists=True,
                line_count=consolidated_rules.line_count,
                lines=consolidated_rules.lines,
            )
            self._log_consolidation_complete(
                iteration_number=iteration_number,
                artifact=consolidation_artifact,
                metrics=consolidation_metrics,
                suggestion=consolidation_suggestion,
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
            cost_totals = _merge_cost_totals(
                cost_totals,
                narrative_tuning_result.critique_metrics.cost,
                *(
                    pass_result.suggestion_metrics.cost
                    for pass_result in narrative_tuning_result.pass_results
                ),
            )
            total_cost = cost_totals.get("total_cost", 0.0) if cost_totals else 0.0
            _check_cost_limit(cost_totals, cost_limit)
            logger.info(
                "Rule refinement iteration %d/%d complete\n"
                "Start rules: %s\n"
                "Final iteration rules: %s\n"
                "Sources processed: %d\n"
                "Accumulated usage: %s\n"
                "Accumulated cost: %s",
                iteration_number,
                iterations,
                iteration_start_rules_path,
                narrative_tuning_result.output_artifact.rules_path,
                len(source_results),
                _format_usage_summary(usage_totals),
                _format_cost_summary(cost_totals, fallback_total=total_cost),
            )
            current_rules_path = Path(narrative_tuning_result.output_artifact.rules_path)
            current_rules = narrative_rules
            iteration_results.append(
                RuleRefinementIterationResult(
                    iteration_number=iteration_number,
                    input_rules_path=iteration_start_rules_path,
                    consolidation_suggestion=consolidation_suggestion,
                    consolidation_metrics=consolidation_metrics,
                    consolidation_artifact=consolidation_artifact,
                    output_artifact=narrative_tuning_result.output_artifact,
                    narrative_tuning=narrative_tuning_result,
                    source_results=source_results,
                )
            )

        reduction_result = None
        reduction_usage: dict[str, int] = {}
        reduction_cost: dict[str, float] | None = None
        if reduction_passes > 0 and extracted_sources:
            reduction_result, reduced_rules, reduction_usage, reduction_cost = self._run_reduction(
                rules=current_rules,
                sources=extracted_sources,
                reduction_passes=reduction_passes,
                notes=reduction_notes or [],
                canonical_rules_path=canonical_rules_path,
            )
            usage_totals = _merge_usage_totals(usage_totals, reduction_usage)
            cost_totals = _merge_cost_totals(cost_totals, reduction_cost)
            _check_cost_limit(cost_totals, cost_limit)
            current_rules = reduced_rules
            current_rules_path = Path(reduction_result.output_artifact.rules_path)

        result = RuleRefinementRunResult(
            iterations=iterations,
            initial_rules_path=base_rules.path,
            final_rules_path=str(current_rules_path),
            source_count=len(extracted_sources),
            iteration_results=iteration_results,
            usage_totals=usage_totals,
            cost_totals=cost_totals,
            reduction=reduction_result,
        )
        final_cost = cost_totals.get("total_cost", 0.0) if cost_totals else 0.0
        logger.info(
            "Rule refinement run complete\n"
            "Iterations: %d\n"
            "Sources per iteration: %d\n"
            "Final rules: %s\n"
            "Total usage: %s\n"
            "Total cost: %s",
            iterations,
            len(extracted_sources),
            current_rules_path,
            _format_usage_summary(usage_totals),
            _format_cost_summary(cost_totals, fallback_total=final_cost),
        )
        _metrics_path, run_timestamp = save_usage_metrics(result=result, rules_path=base_rules.path)
        manifest_path = save_run_manifest(
            result=result,
            rules_path=base_rules.path,
            timestamp=run_timestamp,
            model=self.model,
            reasoning_effort=self.reasoning_effort,
        )
        result.manifest_path = str(manifest_path)
        logger.info("Run manifest: %s", manifest_path)
        return result

    def _analyze_sources(
        self,
        *,
        rules: DemoBuildRulesLines,
        sources: list[RefinementSource],
    ) -> dict[str, tuple[str, RuleRefinementCallMetrics]]:
        """Run source-gap analyses concurrently against one shared rules snapshot."""
        logger.info(
            "Starting concurrent source-gap analysis\nRules snapshot: %s (%d lines)\nSources: %s",
            rules.path,
            rules.line_count,
            _format_source_list(sources),
        )
        return asyncio.run(self._analyze_sources_async(rules=rules, sources=sources))

    async def _analyze_sources_async(
        self,
        *,
        rules: DemoBuildRulesLines,
        sources: list[RefinementSource],
    ) -> dict[str, tuple[str, RuleRefinementCallMetrics]]:
        rules_text = lines_to_markdown(rules.lines)
        developer_prompt = build_source_gap_analysis_developer_prompt()
        sem = asyncio.Semaphore(8)

        async def process_source(
            source: RefinementSource,
        ) -> tuple[str, tuple[str, RuleRefinementCallMetrics]]:
            user_prompt = build_source_gap_analysis_user_prompt(
                rules_text=rules_text,
                source=source,
            )
            async with sem:
                analysis, metrics = await asyncio.to_thread(
                    self._run_text_call,
                    developer_prompt=developer_prompt,
                    user_prompt=user_prompt,
                    phase_key="rule_refinement_analysis",
                    reasoning_effort="high",
                )
            return source.source_key, (analysis, metrics)

        results = await asyncio.gather(*(process_source(source) for source in sources))
        return dict(results)

    def _suggest_rule_updates(
        self,
        *,
        rules: DemoBuildRulesLines,
        analysis: str,
        source: RefinementSource,
    ) -> tuple[RuleUpdateSuggestions, RuleRefinementCallMetrics]:
        developer_prompt = build_rule_update_developer_prompt()
        user_prompt = build_rule_update_user_prompt(
            rules=rules,
            analysis=analysis,
            source=source,
        )
        return self._run_rule_update_call(
            schema_name="rule_refinement_suggestions",
            developer_prompt=developer_prompt,
            user_prompt=user_prompt,
            phase_key="rule_refinement_suggestions",
        )

    def _consolidate_rules(
        self, *, rules: DemoBuildRulesLines
    ) -> tuple[RuleUpdateSuggestions, RuleRefinementCallMetrics]:
        developer_prompt = build_rule_consolidation_developer_prompt()
        user_prompt = build_rule_consolidation_user_prompt(rules=rules)
        return self._run_rule_update_call(
            schema_name="rule_refinement_consolidation",
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
        self._log_narrative_critique_start(
            iteration_number=iteration_number,
            rules=rules,
        )
        critique, critique_metrics = self._critique_narrative_structure(rules=rules)
        critique_path = iteration_narrative_critique_path(canonical_rules_path, iteration_number)
        save_narrative_critique_artifact(output_path=critique_path, critique=critique)
        self._log_narrative_critique_complete(
            iteration_number=iteration_number,
            critique=critique,
            critique_path=critique_path,
            metrics=critique_metrics,
        )

        current_rules = DemoBuildRulesLines.model_validate(rules.model_dump())
        pass_results: list[NarrativeTuningPassResult] = []

        for pass_number in range(1, 2):
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
            self._log_narrative_improvement_complete(
                iteration_number=iteration_number,
                pass_number=pass_number,
                suggestion_path=suggestion_path,
                artifact=output_artifact,
                metrics=suggestion_metrics,
                suggestion=suggestion,
            )
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
        return self._run_rule_update_call(
            schema_name="rule_refinement_narrative_suggestions",
            developer_prompt=developer_prompt,
            user_prompt=user_prompt,
            phase_key="rule_refinement_narrative_suggestions",
            reasoning_effort="medium",
        )

    def _run_reduction(
        self,
        *,
        rules: DemoBuildRulesLines,
        sources: list[RefinementSource],
        reduction_passes: int,
        notes: list[str],
        canonical_rules_path: Path,
    ) -> tuple[
        ReductionLoopResult,
        DemoBuildRulesLines,
        dict[str, int],
        dict[str, float] | None,
    ]:
        logger.info(
            "Starting end-of-run reduction\n"
            "Input rules: %s (%d lines)\n"
            "Reduction passes: %d\n"
            "Initial notes: %s",
            rules.path,
            rules.line_count,
            reduction_passes,
            "; ".join(notes) if notes else "none",
        )
        current_rules = DemoBuildRulesLines.model_validate(rules.model_dump())
        current_notes = list(notes)
        pass_results: list[ReductionPassResult] = []
        reduction_usage: dict[str, int] = {}
        reduction_cost: dict[str, float] | None = None
        previous_missing_count: int | None = None

        for pass_number in range(1, reduction_passes + 1):
            line_count_before = current_rules.line_count
            suggestion, suggestion_metrics = self._run_reduction_editor(
                rules=current_rules,
                notes=current_notes,
            )
            updated_rules = apply_rule_update_suggestions(current_rules, suggestion)
            normalized_rules = _normalize_blank_line_runs(updated_rules)
            output_version = next_rules_version(Path(current_rules.path))
            output_path = versioned_rules_path(canonical_rules_path, output_version)
            diff_path = versioned_diff_path(canonical_rules_path, output_version)
            suggestion_path = versioned_reduction_suggestion_path(
                canonical_rules_path,
                output_version,
                pass_number,
            )
            output_artifact = save_iteration_artifacts(
                previous=current_rules,
                updated=DemoBuildRulesLines(
                    path=str(output_path),
                    exists=True,
                    line_count=normalized_rules.line_count,
                    lines=normalized_rules.lines,
                ),
                output_path=output_path,
                diff_path=diff_path,
                version=output_version,
                canonical_rules_path=canonical_rules_path,
            )
            save_reduction_suggestion_artifact(output_path=suggestion_path, suggestion=suggestion)
            editor_result = ReductionEditorResult(
                input_rules_path=current_rules.path,
                notes=current_notes,
                suggestion=suggestion,
                suggestion_metrics=suggestion_metrics,
                suggestion_path=str(suggestion_path),
                output_artifact=output_artifact,
            )
            reduction_usage = _merge_usage_totals(reduction_usage, suggestion_metrics.usage)
            reduction_cost = _merge_cost_totals(reduction_cost, suggestion_metrics.cost)
            current_rules = DemoBuildRulesLines(
                path=str(output_path),
                exists=True,
                line_count=normalized_rules.line_count,
                lines=normalized_rules.lines,
            )
            critic_results = self._critique_reduction(
                rules=current_rules,
                sources=sources,
                editor_changes=suggestion,
                pass_number=pass_number,
                version=output_version,
                canonical_rules_path=canonical_rules_path,
            )
            for critic_result in critic_results:
                reduction_usage = _merge_usage_totals(
                    reduction_usage,
                    critic_result.critique_metrics.usage,
                )
                reduction_cost = _merge_cost_totals(
                    reduction_cost,
                    critic_result.critique_metrics.cost,
                )
            missing_information_count = sum(
                len(result.critique.missing_information) for result in critic_results
            )
            missing_information_delta = (
                None
                if previous_missing_count is None
                else missing_information_count - previous_missing_count
            )
            parent_notes = []
            if pass_number < reduction_passes:
                parent_notes = self._build_reduction_parent_notes(
                    line_count_before=line_count_before,
                    line_count_after=current_rules.line_count,
                    missing_information_count=missing_information_count,
                    missing_information_delta=missing_information_delta,
                    critic_results=critic_results,
                )
            pass_result = ReductionPassResult(
                pass_number=pass_number,
                editor_result=editor_result,
                critic_results=critic_results,
                line_count_before=line_count_before,
                line_count_after=current_rules.line_count,
                line_count_delta=current_rules.line_count - line_count_before,
                missing_information_count=missing_information_count,
                missing_information_delta=missing_information_delta,
                parent_notes=parent_notes,
            )
            pass_results.append(pass_result)
            previous_missing_count = missing_information_count
            current_notes = parent_notes
            logger.info(
                "Completed reduction pass\n"
                "Pass: %d/%d\n"
                "Output rules: %s\n"
                "Suggestion artifact: %s\n"
                "Suggestion summary: %s\n"
                "Line count: %d -> %d (%+d)\n"
                "Missing information count: %d%s",
                pass_number,
                reduction_passes,
                output_artifact.rules_path,
                suggestion_path,
                _format_suggestion_summary(suggestion),
                line_count_before,
                current_rules.line_count,
                current_rules.line_count - line_count_before,
                missing_information_count,
                ""
                if missing_information_delta is None
                else f" ({missing_information_delta:+d} vs previous)",
            )

        if not pass_results:
            raise RuntimeError("Reduction completed without any passes")

        return (
            ReductionLoopResult(
                input_rules_path=rules.path,
                pass_results=pass_results,
                output_artifact=pass_results[-1].editor_result.output_artifact,
                final_line_count=pass_results[-1].line_count_after,
                final_missing_information_count=pass_results[-1].missing_information_count,
            ),
            current_rules,
            reduction_usage,
            reduction_cost,
        )

    def _run_reduction_editor(
        self,
        *,
        rules: DemoBuildRulesLines,
        notes: list[str],
    ) -> tuple[RuleUpdateSuggestions, RuleRefinementCallMetrics]:
        developer_prompt = build_reduction_editor_developer_prompt()
        user_prompt = build_reduction_editor_user_prompt(rules=rules, notes=notes)
        return self._run_rule_update_call(
            schema_name="rule_refinement_reduction_editor",
            developer_prompt=developer_prompt,
            user_prompt=user_prompt,
            phase_key="rule_refinement_reduction_editor",
            reasoning_effort="high",
        )

    def _critique_reduction(
        self,
        *,
        rules: DemoBuildRulesLines,
        sources: list[RefinementSource],
        editor_changes: RuleUpdateSuggestions,
        pass_number: int,
        version: int,
        canonical_rules_path: Path,
    ) -> list[ReductionCriticResult]:
        logger.info(
            "Starting concurrent reduction critics\n"
            "Pass: %d\n"
            "Rules snapshot: %s (%d lines)\n"
            "Sources: %s",
            pass_number,
            rules.path,
            rules.line_count,
            _format_source_list(sources),
        )
        critic_results = asyncio.run(
            self._critique_reduction_async(
                rules=rules,
                sources=sources,
                editor_changes=editor_changes,
            )
        )
        persisted_results: list[ReductionCriticResult] = []
        for source, critique, metrics in critic_results:
            critique_path = versioned_reduction_critic_path(
                canonical_rules_path,
                version,
                pass_number,
                source.source_key,
            )
            save_reduction_critique_artifact(output_path=critique_path, critique=critique)
            persisted_results.append(
                ReductionCriticResult(
                    source_key=source.source_key,
                    title=source.title,
                    critique=critique,
                    critique_metrics=metrics,
                    critique_path=str(critique_path),
                )
            )
        return persisted_results

    async def _critique_reduction_async(
        self,
        *,
        rules: DemoBuildRulesLines,
        sources: list[RefinementSource],
        editor_changes: RuleUpdateSuggestions,
    ) -> list[tuple[RefinementSource, ReductionCritique, RuleRefinementCallMetrics]]:
        rules_text = lines_to_markdown(rules.lines)
        developer_prompt = build_reduction_critic_developer_prompt()
        sem = asyncio.Semaphore(8)

        async def process_source(
            source: RefinementSource,
        ) -> tuple[RefinementSource, ReductionCritique, RuleRefinementCallMetrics]:
            user_prompt = build_reduction_critic_user_prompt(
                rules_text=rules_text,
                source=source,
                editor_changes=editor_changes,
            )
            async with sem:
                critique, metrics = await asyncio.to_thread(
                    self._run_structured_call,
                    schema_name="rule_refinement_reduction_critic",
                    output_model=ReductionCritique,
                    developer_prompt=developer_prompt,
                    user_prompt=user_prompt,
                    phase_key="rule_refinement_reduction_critic",
                    reasoning_effort="high",
                )
            return source, critique, metrics

        return list(await asyncio.gather(*(process_source(source) for source in sources)))

    def _build_reduction_parent_notes(
        self,
        *,
        line_count_before: int,
        line_count_after: int,
        missing_information_count: int,
        missing_information_delta: int | None,
        critic_results: list[ReductionCriticResult],
    ) -> list[str]:
        notes: list[str] = []
        if line_count_after >= line_count_before:
            notes.append(
                "Reduce redundancy more aggressively; prefer empty-string replacements for lines made redundant by consolidation."
            )
        else:
            notes.append(
                "Keep reducing line count, but do not merge distinct rules into one overloaded line."
            )

        if missing_information_count == 0:
            notes.append(
                "No critic found missing information; further edits should only be made if they preserve full coverage."
            )
            return notes

        if missing_information_delta is not None and missing_information_delta > 0:
            notes.append(
                "The previous pass increased missing information; restore coverage before attempting further compression."
            )

        missing_items: list[str] = []
        for critic_result in critic_results:
            for item in critic_result.critique.missing_information:
                if item not in missing_items:
                    missing_items.append(item)
        for item in missing_items[:8]:
            notes.append(f"Ensure the reduced rules still cover: {item}")
        return notes

    def _run_rule_update_call(
        self,
        *,
        schema_name: str,
        developer_prompt: str,
        user_prompt: str,
        phase_key: str,
        reasoning_effort: str | None = None,
    ) -> tuple[RuleUpdateSuggestions, RuleRefinementCallMetrics]:
        return self._run_structured_call(
            schema_name=schema_name,
            output_model=RuleUpdateSuggestions,
            developer_prompt=developer_prompt,
            user_prompt=user_prompt,
            phase_key=phase_key,
            reasoning_effort=reasoning_effort,
        )

    def _run_text_call(
        self,
        *,
        developer_prompt: str,
        user_prompt: str,
        phase_key: str,
        reasoning_effort: str | None = None,
    ) -> tuple[str, RuleRefinementCallMetrics]:
        payload: dict[str, object] = {
            "model": self.model,
            "store": self.store_responses,
            "input": [
                {"role": "developer", "content": developer_prompt},
                {"role": "user", "content": user_prompt},
            ],
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
        output_text = extract_output_text(response)
        if not output_text:
            raise RuntimeError("Responses API returned an empty text output")
        usage = extract_usage(response)
        model_used = extract_model(response) or self.model
        cost = estimate_cost(model_name=model_used, usage=usage) if usage else None
        metrics = RuleRefinementCallMetrics(
            model_used=model_used,
            status=extract_status(response),
            usage=usage,
            cost=cost,
        )
        return output_text, metrics

    def _run_structured_call(
        self,
        *,
        schema_name: str,
        output_model: type[NarrativeCritique | ReductionCritique | RuleUpdateSuggestions],
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
        usage = extract_usage(response)
        model_used = extract_model(response) or self.model
        cost = estimate_cost(model_name=model_used, usage=usage) if usage else None
        metrics = RuleRefinementCallMetrics(
            model_used=model_used,
            status=extract_status(response),
            usage=usage,
            cost=cost,
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


def build_rule_refinement_service(*, responses_client: Any | None = None) -> RuleRefinementService:
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


def _check_cost_limit(
    cost_totals: dict[str, float] | None,
    cost_limit: float | None,
) -> None:
    """Raise CostLimitExceededError if accumulated cost exceeds limit."""
    if cost_limit is None:
        return
    total = cost_totals.get("total_cost", 0.0) if cost_totals else 0.0
    if total > cost_limit:
        raise CostLimitExceededError(accumulated_cost=total, limit=cost_limit)


def _merge_usage_totals(existing: dict[str, int], *usages: dict[str, int]) -> dict[str, int]:
    """Merge usage dictionaries without dropping missing keys."""
    merged = dict(existing)
    for usage in usages:
        for key, value in usage.items():
            merged[key] = merged.get(key, 0) + int(value or 0)
    return merged


def _merge_cost_totals(
    existing: dict[str, float] | None,
    *costs: dict[str, float] | None,
) -> dict[str, float] | None:
    """Merge cost dictionaries; returns None if no costs present."""
    merged_inputs: list[dict[str, float] | None] = [cost for cost in costs if cost is not None]
    if existing is not None:
        merged_inputs.append(existing)
    return merge_costs(merged_inputs)


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


def _format_source_list(sources: list[RefinementSource]) -> str:
    """Render sources as a concise human-readable list."""
    return ", ".join(source.source_key for source in sources) or "none"


def _format_usage_summary(usage: dict[str, int]) -> str:
    """Render token usage as a compact human-readable summary."""
    if not usage:
        return "no usage reported"
    return (
        f"input={usage.get('input_tokens', 0)}, "
        f"output={usage.get('output_tokens', 0)}, "
        f"reasoning={usage.get('reasoning_tokens', 0)}, "
        f"cached={usage.get('cached_input_tokens', 0)}, "
        f"total={usage.get('total_tokens', 0)}"
    )


def _format_cost_summary(
    cost: dict[str, float] | None,
    *,
    fallback_total: float | None = None,
) -> str:
    """Render estimated cost as a compact human-readable summary."""
    if cost and "total_cost" in cost:
        return f"${cost.get('total_cost', 0.0):.4f}"
    if fallback_total is not None:
        return f"${fallback_total:.4f}"
    return "not available"


def _preview_text(text: str, *, limit: int) -> str:
    """Return one-line preview text for logs."""
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized or "none"
    return normalized[: max(0, limit - 3)].rstrip() + "..."


def _format_changed_lines(changed_lines: list[int]) -> str:
    """Render changed line numbers for logs."""
    if not changed_lines:
        return "no line changes"
    if len(changed_lines) <= 8:
        return ", ".join(str(line) for line in changed_lines)
    head = ", ".join(str(line) for line in changed_lines[:8])
    return f"{head}, ... ({len(changed_lines)} lines changed)"


def _format_suggestion_summary(suggestion: RuleUpdateSuggestions) -> str:
    """Render replacements/appends/rationale counts for logs."""
    return (
        f"{len(suggestion.replacements)} replacements, "
        f"{len(suggestion.appends)} appends, "
        f"{len(suggestion.rationale)} rationale notes"
    )
