"""Prompt builders for rule refinement model calls."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .extractors import DemoBuildRulesLines
    from .models import RefinementSource, RuleUpdateSuggestions

_OBJECTIVE_PREFIX = (
    "Overall objective: define standard rules and procedures for the creation "
    "of demos showcasing proposed GenAI products.\n\n"
    "Guidelines:\n"
    "- Format textual outputs as markdown where appropriate (e.g. lists, bullets, code blocks, headers).\n"
    "- Do not include line number references (e.g. 'line 57', 'see 16, 19') in rule content; "
    "use section names or topic anchors instead.\n"
    "- The rules and procedures being refined are general and abstract; they must not reproduce or "
    "redefine the schemas (e.g. code specs, demo specs, feature specs) used elsewhere in the system.\n"
    "- Return JSON only.\n\n"
)

_ABSTRACT_NATURAL_LANGUAGE_GUIDANCE = (
    "The build rules under refinement must remain general and abstract: descriptive natural language "
    "only, not code, schemas, field names, or implementation-shaped notation.\n"
    "Defining or referring to common terms is acceptable, but do so in natural language, with "
    "capitalization only where needed for the term itself.\n"
)

_LINE_MAPPED_UPDATE_FORMAT_GUIDANCE = (
    "Use replacements for edits to existing lines and appends for new lines at the end.\n"
    "Use appends only when absolutely necessary—when information is completely missing from the rules; "
    "prefer replacements when the rules can be improved by editing existing lines.\n"
    "Each replacement must be an object with line_number and new_line.\n"
    "Do not delete, reorder, or renumber lines.\n"
)


def _with_objective_prefix(instructions: str) -> str:
    """Prepend the shared rule refinement objective to developer prompts."""
    return f"{_OBJECTIVE_PREFIX}{instructions}"


def _with_line_mapped_update_format(instructions: str) -> str:
    """Append the common structured update format requirements."""
    return f"{instructions}{_LINE_MAPPED_UPDATE_FORMAT_GUIDANCE}"


def build_source_gap_analysis_developer_prompt() -> str:
    """Build the instruction prompt for one source-gap analysis call."""
    return _with_objective_prefix(
        "You analyze the gap between one source string and the current build rules.\n"
        "Read the current rules and the source carefully, then explain what aspects of the source are "
        "missing, under-specified, or insufficiently explicit in the current build rules.\n"
        "Focus on substantive omissions, constraints, defaults, prohibitions, sequencing, and coverage "
        "gaps that the build rules should better capture.\n"
        "Do not propose exact line edits or output JSON.\n"
        "Return concise markdown only."
    )


def build_source_gap_analysis_user_prompt(*, rules_text: str, source: RefinementSource) -> str:
    """Build the user prompt for one source-gap analysis call."""
    return (
        "Current build rules raw text:\n"
        f"```text\n{rules_text}\n```\n\n"
        f"Source key: {source.source_key}\n"
        f"Source title: {source.title}\n\n"
        "Analyze what this source requires that is not yet fully captured in the current build rules.\n\n"
        "Source content:\n"
        f"```text\n{source.content}\n```\n"
    )


def build_rule_update_developer_prompt() -> str:
    """Build the instruction prompt for line-based rule update suggestions."""
    return _with_objective_prefix(
        _with_line_mapped_update_format(
            "You update a line-mapped build rules document using a prior analysis of missing source aspects.\n"
            "Use the analysis to improve the current rules so they better capture the source's intent.\n"
            f"{_ABSTRACT_NATURAL_LANGUAGE_GUIDANCE}"
            "Suggest only necessary changes; if a needed improvement is already reflected in the current rules, "
            "do not duplicate it and treat it as already done.\n"
            "Avoid duplicate semantics and preserve existing meaning unless a clearer rule is needed.\n"
            "Prefer minimal edits when the current rules already cover the analysis findings.\n"
            "Append new lines only when information is completely missing; otherwise use replacements.\n"
            "Suggesting no updates (empty replacements and appends) is fine when the current rules "
            "already satisfy the analysis."
        )
    )


def build_rule_consolidation_developer_prompt() -> str:
    """Build the instruction prompt for consolidating the current rule set."""
    return _with_objective_prefix(
        _with_line_mapped_update_format(
            "You consolidate a line-mapped build rules document after source-specific updates.\n"
            "Suggest line updates that combine similar or repetitive rules into fewer rules, impose clear "
            "categories or sections, and resolve conflicting rules where possible.\n"
            "You may replace a redundant rule line with an empty string when consolidation removes it.\n"
            "Use appends only when information is completely missing; prefer replacements and consolidation.\n"
            "Prefer a cleaner, more structured final document with less duplication."
        )
    )


def build_narrative_critique_developer_prompt() -> str:
    """Build the instruction prompt for narrative-structure critique."""
    return _with_objective_prefix(
        "You critique build rules for narrative structure and clarity.\n"
        "Assess whether the document is easy to follow, has a clear flow or procedure, avoids jargon "
        "or undefined terms, and can be understood without insider context.\n"
        "Call out concrete structural or wording problems only when they are supported by the text.\n"
        "Suggest improvements that would make the document easier to read and execute.\n"
        "Do not propose line edits here; return critique observations and suggested improvements only."
    )


def build_narrative_improvement_developer_prompt() -> str:
    """Build the instruction prompt for narrative-structure improvement updates."""
    return _with_objective_prefix(
        _with_line_mapped_update_format(
            "You update a line-mapped build rules document to apply narrative-structure improvements.\n"
            "Use the suggested improvements to make the rules easier to follow, clearer, and more procedural "
            "without changing their substantive intent.\n"
            f"{_ABSTRACT_NATURAL_LANGUAGE_GUIDANCE}"
            "Suggest only necessary changes; if an improvement is already reflected in the current rules, do "
            "not duplicate it and treat it as already done.\n"
            "Append new lines only when information is completely missing; prefer replacements.\n"
        )
    )


def build_reduction_editor_developer_prompt() -> str:
    """Build the instruction prompt for one reduction editor pass."""
    return _with_objective_prefix(
        _with_line_mapped_update_format(
            "You are the editor in an end-of-run reduction loop for demo build rules.\n"
            "Reduce redundancy and compress the rules into fewer lines where possible, while preserving the "
            "important information already captured.\n"
            "Do not cause genuine loss of information: every substantive requirement, constraint, procedure, "
            "or definition in the current rules must remain represented in the reduced output, either by "
            "consolidation into a surviving line or by explicit retention.\n"
            "Keep separate rules on separate lines; do not merge distinct obligations into one bloated line.\n"
            "When multiple lines restate the same idea, consolidate them into the clearest single rule and "
            "replace the redundant lines with empty strings.\n"
            "If parent notes explicitly identify missing information that should be restored or added, you may "
            "append or revise lines to include it.\n"
            f"{_ABSTRACT_NATURAL_LANGUAGE_GUIDANCE}"
            "Prefer the smallest set of clear rules that still captures the necessary guidance.\n"
        )
    )


def build_reduction_critic_developer_prompt() -> str:
    """Build the instruction prompt for one source-specific reduction critic call."""
    return _with_objective_prefix(
        "You are a source-specific critic reviewing reduced demo build rules.\n"
        "Compare one existing source against the updated rules and the editor's applied changes.\n"
        "Identify only concrete pieces of information from the source that are now missing from, or no longer "
        "made sufficiently explicit by, the updated rules.\n"
        "Do not suggest edits. Do not report stylistic preferences. If nothing important is missing, return an "
        "empty list.\n"
        "Return JSON only.\n"
    )


def build_rule_update_user_prompt(
    *, rules: DemoBuildRulesLines, analysis: str, source: RefinementSource
) -> str:
    """Build the user prompt for one rules update suggestion call."""
    line_mapping_json = json.dumps(rules.lines, indent=2, sort_keys=True)
    analysis_text = analysis.strip() or "No missing aspects identified."
    return (
        f"Source key: {source.source_key}\n"
        f"Source title: {source.title}\n\n"
        "Current build rules line mapping:\n"
        f"```json\n{line_mapping_json}\n```\n\n"
        "Analysis of missing source aspects:\n"
        f"{analysis_text}\n\n"
        "Suggest only line replacements for existing lines and appends for new lines. "
        "Use appends only when information is completely missing from the rules."
    )


def build_narrative_critique_user_prompt(*, rules_text: str) -> str:
    """Build the user prompt for one narrative critique call."""
    return f"Current build rules raw text:\n```text\n{rules_text}\n```\n"


def build_narrative_improvement_user_prompt(
    *, rules: DemoBuildRulesLines, suggested_improvements: list[str]
) -> str:
    """Build the user prompt for one narrative improvement call."""
    line_mapping_json = json.dumps(rules.lines, indent=2, sort_keys=True)
    improvements_text = (
        "\n".join(f"- {improvement}" for improvement in suggested_improvements) or "- None"
    )
    return (
        "Suggested narrative improvements:\n"
        f"{improvements_text}\n\n"
        "Current build rules line mapping:\n"
        f"```json\n{line_mapping_json}\n```\n\n"
        "Suggest only line replacements for existing lines and appends for new lines. "
        "Use appends only when information is completely missing from the rules."
    )


def build_reduction_editor_user_prompt(
    *,
    rules: DemoBuildRulesLines,
    notes: list[str] | None = None,
) -> str:
    """Build the user prompt for one reduction editor pass."""
    line_mapping_json = json.dumps(rules.lines, indent=2, sort_keys=True)
    notes_text = "\n".join(f"- {note}" for note in (notes or [])) or "- None"
    return (
        "Parent notes for this reduction pass:\n"
        f"{notes_text}\n\n"
        "Current build rules line mapping:\n"
        f"```json\n{line_mapping_json}\n```\n\n"
        "Reduce redundancy without losing information: every substantive requirement must remain represented. "
        "Keep distinct rules on distinct lines, and use empty-string replacements only for lines made redundant "
        "by consolidation."
    )


def build_reduction_critic_user_prompt(
    *,
    rules_text: str,
    source: RefinementSource,
    editor_changes: RuleUpdateSuggestions,
) -> str:
    """Build the user prompt for one reduction critic call."""
    applied_changes_json = json.dumps(editor_changes.model_dump(), indent=2, sort_keys=True)
    return (
        f"Source key: {source.source_key}\n"
        f"Source title: {source.title}\n\n"
        "Existing source content:\n"
        f"```text\n{source.content}\n```\n\n"
        "Updated build rules raw text:\n"
        f"```text\n{rules_text}\n```\n\n"
        "Applied editor changes:\n"
        f"```json\n{applied_changes_json}\n```\n\n"
        "List the important information from the source that is missing from the updated rules."
    )


def build_rule_consolidation_user_prompt(*, rules: DemoBuildRulesLines) -> str:
    """Build the user prompt for one consolidation suggestion call."""
    line_mapping_json = json.dumps(rules.lines, indent=2, sort_keys=True)
    return (
        "Current build rules line mapping:\n"
        f"```json\n{line_mapping_json}\n```\n\n"
        "Suggest line replacements and appends that consolidate repetitive rules, add clearer structure "
        "or categories, and resolve conflicts where possible. Use appends only when information is "
        "completely missing; prefer replacements and consolidation."
    )
