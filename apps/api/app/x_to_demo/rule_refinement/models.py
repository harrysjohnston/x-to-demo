"""Typed models for rule refinement orchestration and persistence."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RefinementSource(BaseModel):
    """One extracted source string to process during rule refinement."""

    model_config = ConfigDict(extra="forbid")

    source_key: str = Field(description="Stable identifier for the extracted source content")
    title: str = Field(description="Human-readable label for the extracted source content")
    content: str = Field(
        min_length=1, description="Source rule text passed to the principle extractor"
    )


class ExtractedPrinciples(BaseModel):
    """Structured output returned by the principle extraction call."""

    model_config = ConfigDict(extra="forbid")

    principles: list[str] = Field(
        default_factory=list,
        description="Atomic principles distilled from the source rule text",
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


class RuleRefinementSourceResult(BaseModel):
    """Recorded outcome for one extracted source within an iteration."""

    model_config = ConfigDict(extra="forbid")

    source_key: str = Field(description="Stable source identifier")
    title: str = Field(description="Human-readable source label")
    input_rules_path: str = Field(description="Rules document path consumed for this source step")
    principles: list[str] = Field(
        default_factory=list,
        description="Distilled principles returned by the extraction call",
    )
    suggestion: RuleUpdateSuggestions = Field(
        description="Line replacement and append suggestions returned for this source",
    )
    extraction_metrics: RuleRefinementCallMetrics = Field(
        description="Metrics for the principle extraction call",
    )
    suggestion_metrics: RuleRefinementCallMetrics = Field(
        description="Metrics for the update suggestion call",
    )
    applied_artifact: RuleRefinementIterationArtifact = Field(
        description="Versioned rules and diff artifacts saved immediately after source updates",
    )
    consolidation_suggestion: RuleUpdateSuggestions = Field(
        description="Line updates returned by the consolidation call",
    )
    consolidation_metrics: RuleRefinementCallMetrics = Field(
        description="Metrics for the consolidation call",
    )
    output_artifact: RuleRefinementIterationArtifact = Field(
        description="Versioned rules and diff artifacts saved after consolidation",
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


class RuleRefinementIterationResult(BaseModel):
    """Full result for one iteration across all extracted rule sources."""

    model_config = ConfigDict(extra="forbid")

    iteration_number: int = Field(description="1-based iteration number")
    input_rules_path: str = Field(
        description="Rules document consumed at the start of the iteration"
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
