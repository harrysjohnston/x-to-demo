"""Extraction helpers for rule refinement inputs."""

from __future__ import annotations

import types
from collections import OrderedDict
from pathlib import Path
from typing import get_args, get_origin

from pydantic import BaseModel, Field

from app.x_to_demo.pipeline.models import PIPELINE_PHASES, PhaseKey
from app.x_to_demo.pipeline.prompts import (
    _GLOBAL_HARD_RULES,
    _PHASE3_API_DECISION_GUIDE,
    _PHASE_PRIORITY_CHECKLIST,
    _PHASE_RULES,
)
from app.x_to_demo.rule_refinement.models import RefinementSource


class DemoBuildRulesLines(BaseModel):
    """Line-oriented view of the current demo build rules document."""

    path: str
    exists: bool
    line_count: int
    lines: dict[int, str] = Field(default_factory=dict)


def _repo_root() -> Path:
    """Resolve the repository root from the rule_refinement package."""
    return Path(__file__).resolve().parents[5]


def _default_rules_path() -> Path:
    """Return the canonical demo build rules markdown path."""
    return _repo_root() / ".agents" / "demo-build-rules.md"


def _default_skills_root() -> Path:
    """Return the canonical skills directory path."""
    return _repo_root() / ".agents" / "skills"


def _get_phase(phase_key: PhaseKey | str):
    """Look up a pipeline phase definition by key."""
    return next((phase for phase in PIPELINE_PHASES if phase.key == phase_key), None)


def _format_type(annotation: object) -> str:
    """Format a type annotation as a readable string."""
    if annotation is type(None):
        return "None"

    origin = get_origin(annotation)
    if origin in (list, tuple, set):
        args = get_args(annotation)
        inner = _format_type(args[0]) if args else "Any"
        return f"{origin.__name__}[{inner}]"
    if origin is dict:
        args = get_args(annotation)
        key_type = _format_type(args[0]) if len(args) > 0 else "Any"
        value_type = _format_type(args[1]) if len(args) > 1 else "Any"
        return f"dict[{key_type}, {value_type}]"
    if origin in (types.UnionType,):
        return " | ".join(_format_type(arg) for arg in get_args(annotation))
    if origin is not None:
        args = get_args(annotation)
        if args:
            return f"{getattr(origin, '__name__', str(origin))}[{', '.join(_format_type(arg) for arg in args)}]"
        return getattr(origin, "__name__", str(origin))
    if isinstance(annotation, type):
        return annotation.__name__
    return str(annotation)


def _annotation_model_types(annotation: object) -> list[type[BaseModel]]:
    """Extract any nested Pydantic model types from an annotation."""
    models: list[type[BaseModel]] = []
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return [annotation]

    origin = get_origin(annotation)
    if origin is None:
        return models

    for arg in get_args(annotation):
        models.extend(_annotation_model_types(arg))
    return models


def _collect_models(root_model: type[BaseModel]) -> list[type[BaseModel]]:
    """Collect nested Pydantic models reachable from a root model."""
    seen: OrderedDict[type[BaseModel], None] = OrderedDict()

    def visit(model: type[BaseModel]) -> None:
        if model in seen:
            return
        seen[model] = None
        for field in model.model_fields.values():
            for nested_model in _annotation_model_types(field.annotation):
                visit(nested_model)

    visit(root_model)
    return list(seen.keys())


def _model_to_table(model: type[BaseModel]) -> str:
    """Format a Pydantic model as a markdown table."""
    lines = ["| Field | Type | Description |", "|---|---|---|"]
    for name, field in model.model_fields.items():
        description = (field.description or "").replace("\n", " ").strip()
        lines.append(f"| {name} | {_format_type(field.annotation)} | {description} |")
    return "\n".join(lines)


def _format_model_section(model: type[BaseModel], *, heading_level: str) -> str:
    """Format one model and its fields as descriptive markdown."""
    lines = [f"{heading_level} `{model.__name__}`"]
    docstring = (model.__doc__ or "").strip()
    if docstring:
        lines.extend(["", docstring])
    lines.extend(["", _model_to_table(model)])
    return "\n".join(lines)


def load_demo_build_rules_lines(path: Path | None = None) -> DemoBuildRulesLines:
    """Load the existing demo build rules markdown as a 1-based line mapping."""
    target_path = path or _default_rules_path()
    if not target_path.exists():
        return DemoBuildRulesLines(
            path=str(target_path),
            exists=False,
            line_count=0,
            lines={},
        )

    raw_text = target_path.read_text(encoding="utf-8")
    if raw_text == "":
        return DemoBuildRulesLines(
            path=str(target_path),
            exists=True,
            line_count=0,
            lines={},
        )

    line_items = dict(enumerate(raw_text.splitlines(), start=1))
    return DemoBuildRulesLines(
        path=str(target_path),
        exists=True,
        line_count=len(line_items),
        lines=line_items,
    )


def extract_global_rules() -> str:
    """Return the global rules as a descriptive numbered list."""
    return "\n".join(f"{index}. {rule}" for index, rule in enumerate(_GLOBAL_HARD_RULES, start=1))


def extract_phase_prompts(phase_key: PhaseKey | str) -> str:
    """Return a descriptive summary of phase guidance without JSON payloads."""
    phase = _get_phase(phase_key)
    if phase is None:
        return ""

    phase_rules = _PHASE_RULES.get(phase.key, ())
    checklist = _PHASE_PRIORITY_CHECKLIST.get(phase.key, ())

    lines = [
        f"## {phase.title}",
        "",
        f"Objective: {phase.objective}",
        "",
        "### Developer Guidance",
        "",
        "Global hard rules:",
    ]
    lines.extend(f"{index}. {rule}" for index, rule in enumerate(_GLOBAL_HARD_RULES, start=1))

    if phase_rules:
        lines.extend(["", "Phase-specific rules:"])
        lines.extend(f"- {rule}" for rule in phase_rules)

    if phase.key == "code_spec":
        lines.extend(["", "API decision guide:"])
        lines.extend(f"- {rule}" for rule in _PHASE3_API_DECISION_GUIDE)

    lines.extend(["", "### User Checklist", ""])
    lines.extend(f"- {item}" for item in checklist)
    return "\n".join(lines)


def extract_skill_content(
    skill_dir_name: str,
    *,
    skills_root: Path | None = None,
    include_reference: bool = True,
) -> str:
    """Extract one skill as descriptive markdown content."""
    resolved_skills_root = skills_root or _default_skills_root()
    skill_dir = resolved_skills_root / skill_dir_name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ""

    content = skill_md.read_text(encoding="utf-8")
    if include_reference:
        reference_md = skill_dir / "reference.md"
        if reference_md.exists():
            reference_content = reference_md.read_text(encoding="utf-8")
            content = f"{content}\n\n---\n\n## Reference\n\n{reference_content}"
    return content


def extract_all_skills(
    *,
    skills_root: Path | None = None,
    include_reference: bool = True,
) -> dict[str, str]:
    """Extract all skills as a mapping from skill directory name to content."""
    resolved_skills_root = skills_root or _default_skills_root()
    if not resolved_skills_root.exists():
        return {}

    extracted: dict[str, str] = {}
    for path in sorted(resolved_skills_root.iterdir()):
        if path.is_dir() and (path / "SKILL.md").exists():
            extracted[path.name] = extract_skill_content(
                path.name,
                skills_root=resolved_skills_root,
                include_reference=include_reference,
            )
    return extracted


def extract_refinement_inputs() -> list[RefinementSource]:
    """Aggregate all extracted source strings for the rule refinement workflow."""
    inputs = [
        RefinementSource(
            source_key="global_rules",
            title="Global hard rules",
            content=extract_global_rules(),
        )
    ]

    for phase in PIPELINE_PHASES:
        prompt_content = extract_phase_prompts(phase.key)
        if prompt_content:
            inputs.append(
                RefinementSource(
                    source_key=f"{phase.key}_prompts",
                    title=f"{phase.title} prompts",
                    content=prompt_content,
                )
            )

        model_content = extract_phase_models(phase.key)
        if model_content:
            inputs.append(
                RefinementSource(
                    source_key=f"{phase.key}_models",
                    title=f"{phase.title} models",
                    content=model_content,
                )
            )

    for skill_name, content in extract_all_skills().items():
        if not content:
            continue
        inputs.append(
            RefinementSource(
                source_key=f"skill_{skill_name}",
                title=f"Skill: {skill_name}",
                content=content,
            )
        )

    return inputs


def extract_phase_models(phase_key: PhaseKey | str) -> str:
    """Return descriptive model summaries for a phase input and output."""
    phase = _get_phase(phase_key)
    if phase is None:
        return ""

    lines = [f"## {phase.title}", ""]

    for label, model in (("Input model", phase.input_model), ("Output model", phase.output_model)):
        lines.extend([f"### {label}", "", _format_model_section(model, heading_level="####"), ""])
        nested_models = [nested for nested in _collect_models(model) if nested is not model]
        if nested_models:
            lines.extend(["Nested models:", ""])
            for nested_model in nested_models:
                lines.extend([_format_model_section(nested_model, heading_level="####"), ""])

    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)
