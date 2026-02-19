"""Prompt and schema helpers for structured X-to-Demo phase calls."""

from __future__ import annotations

import copy
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import BaseModel

    from .models import PipelinePhaseDefinition


def build_phase_prompts(
    *, phase: PipelinePhaseDefinition, phase_input: BaseModel
) -> tuple[str, str]:
    """Build developer + user prompts for one structured phase execution."""
    schema_json = openai_compatible_schema(phase.output_model.model_json_schema())
    schema_excerpt = schema_excerpt_json(schema_json)
    input_payload = json.dumps(phase_input.model_dump(mode="json"), indent=2, sort_keys=True)

    developer_prompt = (
        "You are an expert product-to-engineering planning assistant. "
        f"Your task is {phase.objective} "
        "Return valid JSON that strictly matches the provided schema. "
        "Do not return markdown, prose, or wrapper text."
    )

    user_prompt = (
        f"Phase key: {phase.key}\n"
        f"Phase title: {phase.title}\n\n"
        "Output schema (source of truth):\n"
        f"```json\n{schema_excerpt}\n```\n\n"
        "Input payload:\n"
        f"```json\n{input_payload}\n```\n\n"
        "Return JSON only."
    )
    return developer_prompt, user_prompt


def schema_excerpt_json(schema_json: dict[str, Any]) -> str:
    """Render a concise schema excerpt to reduce prompt size while preserving constraints."""
    properties = schema_json.get("properties") if isinstance(schema_json, dict) else None
    required = schema_json.get("required") if isinstance(schema_json, dict) else None
    defs = schema_json.get("$defs") if isinstance(schema_json, dict) else None
    excerpt = {
        "title": schema_json.get("title") if isinstance(schema_json, dict) else None,
        "type": schema_json.get("type") if isinstance(schema_json, dict) else None,
        "required": required if isinstance(required, list) else [],
        "properties": properties if isinstance(properties, dict) else {},
    }
    if isinstance(defs, dict):
        excerpt["$defs"] = defs
    return json.dumps(excerpt, indent=2, sort_keys=True)


def openai_compatible_schema(schema_json: dict[str, Any]) -> dict[str, Any]:
    """Ensure generated JSON Schema satisfies strict response_format constraints.

    OpenAI Responses API requires:
    - additionalProperties: false on objects
    - every object schema to have 'required' including every key in 'properties'
    - $ref must be the sole keyword (no description, title, etc. alongside $ref)
    """
    normalized = copy.deepcopy(schema_json)
    enforce_no_additional_properties(normalized)
    enforce_required_includes_all_properties(normalized)
    strip_keywords_from_refs(normalized)
    return normalized


def strip_keywords_from_refs(node: object) -> None:
    """Remove keywords like description from schema objects that contain $ref."""
    if isinstance(node, dict):
        if "$ref" in node and len(node) > 1:
            # $ref cannot have sibling keywords; keep only $ref
            ref = node["$ref"]
            node.clear()
            node["$ref"] = ref

        for key in ("properties", "$defs", "definitions", "patternProperties"):
            value = node.get(key)
            if isinstance(value, dict):
                for child in value.values():
                    strip_keywords_from_refs(child)

        for key in ("items", "additionalItems", "contains", "if", "then", "else", "not"):
            if key in node:
                strip_keywords_from_refs(node[key])

        for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
            value = node.get(key)
            if isinstance(value, list):
                for child in value:
                    strip_keywords_from_refs(child)

    elif isinstance(node, list):
        for child in node:
            strip_keywords_from_refs(child)


def enforce_required_includes_all_properties(node: object) -> None:
    """Ensure every object schema has required=[...all property keys...]."""
    if isinstance(node, dict):
        node_type = node.get("type")
        if node_type == "object":
            props = node.get("properties")
            if isinstance(props, dict) and props:
                # OpenAI requires: required must include every key in properties
                required = set(node.get("required") or [])
                required.update(props.keys())
                node["required"] = sorted(required)

        for key in ("properties", "$defs", "definitions", "patternProperties"):
            value = node.get(key)
            if isinstance(value, dict):
                for child in value.values():
                    enforce_required_includes_all_properties(child)

        for key in ("items", "additionalItems", "contains", "if", "then", "else", "not"):
            if key in node:
                enforce_required_includes_all_properties(node[key])

        for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
            value = node.get(key)
            if isinstance(value, list):
                for child in value:
                    enforce_required_includes_all_properties(child)

    elif isinstance(node, list):
        for child in node:
            enforce_required_includes_all_properties(child)


def enforce_no_additional_properties(node: object) -> None:
    """Recursively set `additionalProperties` false on all object schema nodes."""
    if isinstance(node, dict):
        node_type = node.get("type")
        if node_type == "object":
            node["additionalProperties"] = False

        for key in ("properties", "$defs", "definitions", "patternProperties"):
            value = node.get(key)
            if isinstance(value, dict):
                for child in value.values():
                    enforce_no_additional_properties(child)

        for key in ("items", "additionalItems", "contains", "if", "then", "else", "not"):
            if key in node:
                enforce_no_additional_properties(node[key])

        for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
            value = node.get(key)
            if isinstance(value, list):
                for child in value:
                    enforce_no_additional_properties(child)

    elif isinstance(node, list):
        for child in node:
            enforce_no_additional_properties(child)
