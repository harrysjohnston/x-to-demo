---
name: canonical-spec-format-parity
description: Ensures schema changes that affect canonical JSON are reflected in markdown and XML renderers so no data is lost between formats. Use when modifying x-to-demo schemas (feature_spec, demo_spec, code_spec) or when adding/removing fields that serialize to canonical artifacts.
---

# Canonical Spec Format Parity

Every spec exists in three formats: **JSON**, **markdown**, and **XML**. Schema changes that alter the canonical structure must propagate to all three so nothing is lost.

## When to Apply

- Adding, removing, or renaming fields on `FeatureSpecArtifact`, `DemoSpecArtifact`, or `CodeSpecArtifact`
- Changing nested schema structure (e.g. `innovation_focus`, `acceptance_criteria`)
- Modifying field types that affect serialization

## Three Formats

| Format | Location | Source |
|--------|----------|--------|
| JSON | `{phase}.json` | `model.model_dump(mode="json")` |
| Markdown | `{phase}.md` | `render_*_spec_markdown()` in `renderers.py` |
| XML | `{phase}.xml` | `_dict_to_xml()` in `renderers.py` |

JSON and XML derive from the same dict; markdown is hand-authored per field.

## Required Updates on Schema Change

1. **Markdown** – Add or remove sections in the appropriate `render_*_spec_markdown()` so every schema field has a human-readable representation.
2. **XML** – No explicit changes; `_dict_to_xml()` recurses over the dict. New fields appear automatically.
3. **JSON** – No explicit changes; `model_dump(mode="json")` follows the schema.

## Checklist

- [ ] Identify all new/removed/renamed fields in the schema
- [ ] Update `render_feature_spec_markdown`, `render_demo_spec_markdown`, or `render_code_spec_markdown` for each affected field
- [ ] Add bullet/section helpers if needed (e.g. `_acceptance_lines`, `_bullet_lines`)
- [ ] Run roundtrip: `model → model_dump → _dict_to_xml → (parse) → model` to verify XML preserves structure
- [ ] Regenerate existing artifacts if schema changed: `python -c "..."` using `render_markdown` and `_dict_to_xml` from JSON

## Anti-Patterns

- **Silent omission** – Adding a schema field but not rendering it in markdown
- **Stale artifacts** – Changing schema without regenerating `.md`/`.xml` in artifact directories
- **Format-specific logic** – Putting format-specific transformations in the schema instead of in renderers

## Key Files

- `apps/api/app/x_to_demo/schemas/` – feature_spec.py, demo_spec.py, code_spec.py
- `apps/api/app/x_to_demo/renderers.py` – `render_*_spec_markdown`, `_dict_to_xml`
- `apps/api/app/x_to_demo/pipeline/artifacts.py` – `persist_phase_output` writes all three formats
