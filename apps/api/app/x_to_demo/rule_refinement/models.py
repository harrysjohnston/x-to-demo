"""Typed models for rule refinement orchestration and persistence."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RefinementSource(BaseModel):
    """One extracted source string to process during rule refinement."""

    model_config = ConfigDict(extra="forbid")

    source_key: str = Field(description="Stable identifier for the extracted source content")
    title: str = Field(description="Human-readable label for the extracted source content")
    content: str = Field(
        min_length=1, description="Source rule text passed to the gap analysis stage"
    )


class RuleLineReplacement(BaseModel):
    """One explicit line replacement suggestion."""

    model_config = ConfigDict(extra="forbid")

    line_number: int = Field(description="Existing 1-based line number to replace")
    new_line: str = Field(description="Replacement content for the target line")


class RuleUpdateSuggestions(BaseModel):
    """Structured output returned by the rule update suggestion call."""

    model_config = ConfigDict(extra="forbid")

    replacements: list[RuleLineReplacement] = Field(
        default_factory=list,
        description="Existing 1-based line replacements to apply in order",
    )
    appends: list[str] = Field(
        default_factory=list,
        description="New lines to append at the end of the document in order",
    )
    rationale: list[str] = Field(
        default_factory=list,
        description="Optional concise notes explaining the suggested updates",
    )


class NarrativeCritique(BaseModel):
    """Structured output returned by the narrative critique call."""

    model_config = ConfigDict(extra="forbid")

    critique: list[str] = Field(
        default_factory=list,
        description="Concrete observations about the narrative structure and clarity of the rules",
    )
    suggested_improvements: list[str] = Field(
        default_factory=list,
        description="Concrete improvements that would make the rules easier to follow",
    )


class RuleRefinementCallMetrics(BaseModel):
    """Metrics captured for one rule refinement model call."""

    model_config = ConfigDict(extra="forbid")

    model_used: str = Field(description="OpenAI model that produced the response")
    status: str = Field(description="Terminal response status")
    usage: dict[str, int] = Field(
        default_factory=dict,
        description="Token usage reported by the Responses API",
    )
    cost: dict[str, float] | None = Field(
        default=None,
        description="Estimated API cost from usage and local pricing rates",
    )


class RuleRefinementSourceResult(BaseModel):
    """Recorded outcome for one extracted source within an iteration."""

    model_config = ConfigDict(extra="forbid")

    source_key: str = Field(description="Stable source identifier")
    title: str = Field(description="Human-readable source label")
    input_rules_path: str = Field(description="Rules document path consumed for this source step")
    analysis: str = Field(
        description="Freeform analysis of missing source aspects vs current rules"
    )
    analysis_path: str = Field(description="Persisted path for the source analysis artifact")
    suggestion: RuleUpdateSuggestions = Field(
        description="Line replacement and append suggestions returned for this source",
    )
    analysis_metrics: RuleRefinementCallMetrics = Field(
        description="Metrics for the source gap analysis call",
    )
    suggestion_metrics: RuleRefinementCallMetrics = Field(
        description="Metrics for the source improvement call",
    )
    suggestion_path: str = Field(description="Persisted path for the source improvement suggestion")
    output_artifact: RuleRefinementIterationArtifact = Field(
        description="Versioned rules and diff artifacts saved after this source improvement",
    )


class RuleRefinementIterationArtifact(BaseModel):
    """Persisted output artifacts for one refinement iteration."""

    model_config = ConfigDict(extra="forbid")

    version: int = Field(description="Monotonic version suffix used for this saved iteration")
    rules_path: str = Field(description="Saved path to the versioned rules markdown")
    diff_path: str = Field(description="Saved path to the focused diff markdown")
    changed_line_numbers: list[int] = Field(
        default_factory=list,
        description="Sorted line numbers that changed in the saved output",
    )


class NarrativeTuningPassResult(BaseModel):
    """Recorded outcome for one narrative-tuning improvement pass."""

    model_config = ConfigDict(extra="forbid")

    pass_number: int = Field(description="1-based narrative-tuning pass number")
    input_rules_path: str = Field(description="Rules document path consumed by this pass")
    suggestion: RuleUpdateSuggestions = Field(
        description="Line replacement and append suggestions returned for this pass",
    )
    suggestion_metrics: RuleRefinementCallMetrics = Field(
        description="Metrics for the narrative improvement call",
    )
    suggestion_path: str = Field(
        description="Persisted path for the narrative improvement suggestion"
    )
    output_artifact: RuleRefinementIterationArtifact = Field(
        description="Versioned rules and diff artifacts saved after this pass",
    )


class NarrativeTuningIterationResult(BaseModel):
    """Recorded outcome for the iteration-end narrative tuning stage."""

    model_config = ConfigDict(extra="forbid")

    input_rules_path: str = Field(description="Rules document path consumed by narrative tuning")
    critique: NarrativeCritique = Field(description="Narrative critique of the current rules")
    critique_metrics: RuleRefinementCallMetrics = Field(
        description="Metrics for the narrative critique call",
    )
    critique_path: str = Field(description="Persisted path for the narrative critique artifact")
    pass_results: list[NarrativeTuningPassResult] = Field(
        default_factory=list,
        description="Ordered narrative improvement passes for this iteration",
    )
    output_artifact: RuleRefinementIterationArtifact = Field(
        description="Final saved artifacts produced by narrative tuning",
    )


class ReductionCritique(BaseModel):
    """Structured output returned by one reduction critic call."""

    model_config = ConfigDict(extra="forbid")

    missing_information: list[str] = Field(
        default_factory=list,
        description="Concrete pieces of source information missing from the reduced rules",
    )


class ReductionCriticResult(BaseModel):
    """Recorded outcome for one source-specific reduction critic call."""

    model_config = ConfigDict(extra="forbid")

    source_key: str = Field(description="Stable source identifier")
    title: str = Field(description="Human-readable source label")
    critique: ReductionCritique = Field(
        description="Missing-information findings for this source after reduction edits",
    )
    critique_metrics: RuleRefinementCallMetrics = Field(
        description="Metrics for the source-specific reduction critic call",
    )
    critique_path: str = Field(description="Persisted path for the reduction critic artifact")


class ReductionEditorResult(BaseModel):
    """Recorded outcome for one reduction editor pass."""

    model_config = ConfigDict(extra="forbid")

    input_rules_path: str = Field(description="Rules document path consumed by the editor")
    notes: list[str] = Field(
        default_factory=list,
        description="Parent-process notes passed into the editor for this pass",
    )
    suggestion: RuleUpdateSuggestions = Field(
        description="Line replacement and append suggestions returned by the editor",
    )
    suggestion_metrics: RuleRefinementCallMetrics = Field(
        description="Metrics for the reduction editor call",
    )
    suggestion_path: str = Field(description="Persisted path for the reduction editor suggestion")
    output_artifact: RuleRefinementIterationArtifact = Field(
        description="Saved artifacts produced after applying and normalizing the editor changes",
    )


class ReductionPassResult(BaseModel):
    """Recorded outcome for one end-of-run reduction pass."""

    model_config = ConfigDict(extra="forbid")

    pass_number: int = Field(description="1-based reduction pass number")
    editor_result: ReductionEditorResult = Field(
        description="Editor inputs, outputs, and persisted artifacts for this pass",
    )
    critic_results: list[ReductionCriticResult] = Field(
        default_factory=list,
        description="Ordered source-specific critic outcomes for this pass",
    )
    line_count_before: int = Field(description="Physical line count before editor changes")
    line_count_after: int = Field(description="Physical line count after normalization")
    line_count_delta: int = Field(description="After-minus-before line-count delta for this pass")
    missing_information_count: int = Field(
        description="Total number of missing-information findings across all critics"
    )
    missing_information_delta: int | None = Field(
        default=None,
        description="Current missing-information count minus the previous pass count",
    )
    parent_notes: list[str] = Field(
        default_factory=list,
        description="Notes generated after this pass for the next editor pass",
    )


class ReductionLoopResult(BaseModel):
    """Recorded outcome for the one-time end-of-run reduction stage."""

    model_config = ConfigDict(extra="forbid")

    input_rules_path: str = Field(description="Rules document path consumed by the reduction stage")
    pass_results: list[ReductionPassResult] = Field(
        default_factory=list,
        description="Ordered reduction passes",
    )
    output_artifact: RuleRefinementIterationArtifact = Field(
        description="Final saved artifacts produced by the reduction stage",
    )
    final_line_count: int = Field(description="Final physical line count after reduction")
    final_missing_information_count: int = Field(
        description="Final aggregated missing-information count after reduction"
    )


class RuleRefinementIterationResult(BaseModel):
    """Full result for one iteration across all extracted rule sources."""

    model_config = ConfigDict(extra="forbid")

    iteration_number: int = Field(description="1-based iteration number")
    input_rules_path: str = Field(
        description="Rules document consumed at the start of the iteration"
    )
    consolidation_suggestion: RuleUpdateSuggestions = Field(
        description="Line updates returned by the iteration-level consolidation call",
    )
    consolidation_metrics: RuleRefinementCallMetrics = Field(
        description="Metrics for the iteration-level consolidation call",
    )
    consolidation_artifact: RuleRefinementIterationArtifact = Field(
        description="Saved artifacts produced by iteration-level consolidation",
    )
    output_artifact: RuleRefinementIterationArtifact = Field(
        description="Saved artifacts produced by this iteration",
    )
    narrative_tuning: NarrativeTuningIterationResult = Field(
        description="Iteration-end narrative tuning outcomes and persisted artifacts",
    )
    source_results: list[RuleRefinementSourceResult] = Field(
        default_factory=list,
        description="Per-source extraction and suggestion outcomes",
    )


class RuleRefinementRunResult(BaseModel):
    """High-level summary for a full multi-iteration rule refinement run."""

    model_config = ConfigDict(extra="forbid")

    iterations: int = Field(description="Requested number of completed iterations")
    initial_rules_path: str = Field(description="Starting rules document path")
    final_rules_path: str = Field(description="Final saved rules document path")
    source_count: int = Field(description="Number of extracted sources processed per iteration")
    iteration_results: list[RuleRefinementIterationResult] = Field(
        default_factory=list,
        description="Ordered results for each completed iteration",
    )
    usage_totals: dict[str, int] = Field(
        default_factory=dict,
        description="Accumulated token usage across every rule refinement call",
    )
    cost_totals: dict[str, float] | None = Field(
        default=None,
        description="Accumulated estimated cost across every rule refinement call",
    )
    reduction: ReductionLoopResult | None = Field(
        default=None,
        description="One-time end-of-run reduction stage summary, if executed",
    )
    manifest_path: str | None = Field(
        default=None,
        description="Path to the persisted run manifest markdown file",
    )
