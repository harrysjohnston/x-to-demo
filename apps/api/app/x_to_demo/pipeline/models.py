"""Core models and typed phase declarations for the X-to-Demo pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

from app.x_to_demo.schemas import CodeSpecArtifact, DemoSpecArtifact, FeatureSpecArtifact

if TYPE_CHECKING:
    from datetime import datetime

PhaseKey = Literal["feature_spec", "demo_spec", "code_spec"]


class PipelineRunInput(BaseModel):
    """Canonical run input payload persisted for resume semantics."""

    x_input: str = Field(description="Raw input text")
    additional_context: str = Field(default="", description="Optional run context")
    feature_name_hint: str = Field(default="", description="Optional user-supplied feature hint")
    feature_name: str = Field(description="Resolved feature name used in artifact outputs")


@dataclass(frozen=True)
class PipelinePhaseDefinition:
    """Typed phase declaration."""

    key: PhaseKey
    title: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    objective: str


PIPELINE_PHASES: tuple[PipelinePhaseDefinition, ...] = (
    PipelinePhaseDefinition(
        key="feature_spec",
        title="Phase 1: Input -> Feature Spec",
        input_model=PipelineRunInput,
        output_model=FeatureSpecArtifact,
        objective=(
            "Transform raw input into a behavior-first feature spec with explicit intent, "
            "external behavior, and testable acceptance criteria."
        ),
    ),
    PipelinePhaseDefinition(
        key="demo_spec",
        title="Phase 2: Feature Spec -> Demo Spec",
        input_model=FeatureSpecArtifact,
        output_model=DemoSpecArtifact,
        objective=(
            "Convert the feature spec into a concise demo specification that clarifies scope, "
            "flow steps, and success signals."
        ),
    ),
    PipelinePhaseDefinition(
        key="code_spec",
        title="Phase 3: Demo Spec -> Code Spec",
        input_model=DemoSpecArtifact,
        output_model=CodeSpecArtifact,
        objective=(
            "Produce an implementation-ready code spec from the demo spec with concrete stack, "
            "component, state, and test details."
        ),
    ),
)


@dataclass(frozen=True)
class PipelineArtifact:
    """Single phase output generated during a pipeline run."""

    phase_key: PhaseKey
    title: str
    markdown: str
    saved_path: str
    json_path: str
    json_content: dict[str, Any]
    content_hash: str


@dataclass(frozen=True)
class PipelineRunResult:
    """Aggregate result for one completed or partial pipeline run."""

    run_id: str
    created_at: datetime
    model: str
    reasoning_effort: str
    stop_after_phase: PhaseKey
    next_phase_key: PhaseKey | None
    artifacts: list[PipelineArtifact]
    final_code_spec: str | None
    final_code_spec_path: str | None
    usage_totals: dict[str, int]
    cost_totals: dict[str, float] | None


@dataclass(frozen=True)
class PhaseCallMetrics:
    """Token/cost metadata collected for a single phase call."""

    phase_key: PhaseKey
    model_used: str
    usage: dict[str, int]
    cost: dict[str, float] | None
    elapsed_seconds: float
    status: str
