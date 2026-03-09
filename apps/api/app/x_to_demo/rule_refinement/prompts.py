"""Prompt builders for rule refinement model calls."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .extractors import DemoBuildRulesLines
    from .models import RefinementSource

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


def _with_objective_prefix(instructions: str) -> str:
    """Prepend the shared rule refinement objective to developer prompts."""
    return f"{_OBJECTIVE_PREFIX}{instructions}"


def build_principle_extraction_developer_prompt() -> str:
    """Build the instruction prompt for distilling principles from a source string."""
    return _with_objective_prefix(
        "You extract concise, implementation-relevant principles from source rule text.\n"
        "Read the provided source carefully and distill the principles it describes.\n"
        "Return only principles that are directly supported by the source.\n"
        "Keep each principle atomic, concrete, and non-duplicative.\n"
        "Preserve important constraints, prohibitions, defaults, and sequencing.\n"
        "When the source cites line numbers or cross-references, express them as section/topic names "
        "in the distilled principles.\n"
        "Do not suggest edits to the build rules yet."
    )


def build_principle_extraction_user_prompt(source: RefinementSource) -> str:
    """Build the user prompt for one source string."""
    return (
        f"Source key: {source.source_key}\n"
        f"Source title: {source.title}\n\n"
        "Distill the principles described by this source string.\n\n"
        "Source content:\n"
        f"```text\n{source.content}\n```\n"
    )


def build_rule_update_developer_prompt() -> str:
    """Build the instruction prompt for line-based rule update suggestions."""
    return _with_objective_prefix(
        "You update a line-mapped build rules document using distilled principles.\n"
        "Reason over the principles against the current rules and suggest only necessary changes.\n"
        "Use replacements for edits to existing lines and appends for new lines at the end.\n"
        "Each replacement must be an object with line_number and new_line.\n"
        "Do not delete, reorder, or renumber lines.\n"
        "Avoid duplicate semantics and preserve existing meaning unless a clearer rule is needed.\n"
        "Prefer minimal edits when the current rules already cover a principle.\n"
        "Suggesting no updates (empty replacements and appends) is fine when the current rules "
        "already satisfy the principles."
    )


def build_rule_consolidation_developer_prompt() -> str:
    """Build the instruction prompt for consolidating the current rule set."""
    return _with_objective_prefix(
        "You consolidate a line-mapped build rules document after source-specific updates.\n"
        "Suggest line updates that combine similar or repetitive rules into fewer rules, impose clear "
        "categories or sections, and resolve conflicting rules where possible.\n"
        "Use replacements for edits to existing lines and appends for new lines at the end.\n"
        "Each replacement must be an object with line_number and new_line.\n"
        "You may replace a redundant rule line with an empty string when consolidation removes it.\n"
        "Do not reorder or renumber lines.\n"
        "Prefer a cleaner, more structured final document with less duplication."
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
        "You update a line-mapped build rules document to apply narrative-structure improvements.\n"
        "Use the suggested improvements to make the rules easier to follow, clearer, and more procedural "
        "without changing their substantive intent.\n"
        "Suggest only necessary changes; if an improvement is already reflected in the current rules, do "
        "not duplicate it.\n"
        "Use replacements for edits to existing lines and appends for new lines at the end.\n"
        "Each replacement must be an object with line_number and new_line.\n"
        "Do not delete, reorder, or renumber lines."
    )


def build_rule_update_user_prompt(
    *, rules: DemoBuildRulesLines, principles: list[str], source: RefinementSource
) -> str:
    """Build the user prompt for one rules update suggestion call."""
    line_mapping_json = json.dumps(rules.lines, indent=2, sort_keys=True)
    principles_text = "\n".join(f"- {principle}" for principle in principles) or "- None"
    return (
        f"Source key: {source.source_key}\n"
        f"Source title: {source.title}\n\n"
        "Current build rules line mapping:\n"
        f"```json\n{line_mapping_json}\n```\n\n"
        "Distilled principles:\n"
        f"{principles_text}\n\n"
        "Suggest only line replacements for existing lines and appends for new lines."
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
        "Suggest only line replacements for existing lines and appends for new lines."
    )


def build_rule_update_user_prompt_for_section(
    *,
    section_rules: DemoBuildRulesLines,
    principles: list[str],
    source: RefinementSource,
    section_label: str,
) -> str:
    """Build the user prompt for one section's rules update suggestion call."""
    line_mapping_json = json.dumps(section_rules.lines, indent=2, sort_keys=True)
    principles_text = "\n".join(f"- {principle}" for principle in principles) or "- None"
    return (
        f"Source key: {source.source_key}\n"
        f"Source title: {source.title}\n"
        f"Section: {section_label}\n\n"
        "Current build rules line mapping for this section:\n"
        f"```json\n{line_mapping_json}\n```\n\n"
        "Distilled principles:\n"
        f"{principles_text}\n\n"
        "Suggest only line replacements for existing lines and appends for new lines."
    )


def build_rule_consolidation_user_prompt(*, rules: DemoBuildRulesLines) -> str:
    """Build the user prompt for one consolidation suggestion call."""
    line_mapping_json = json.dumps(rules.lines, indent=2, sort_keys=True)
    return (
        "Current build rules line mapping:\n"
        f"```json\n{line_mapping_json}\n```\n\n"
        "Suggest line replacements and appends that consolidate repetitive rules, add clearer structure "
        "or categories, and resolve conflicts where possible."
    )
