---
name: synthetic-input-presets
description: Conventions for synthetic demo inputs as global, selectable presets that populate UI without auto-running. Every planned flow must be covered by some preset. Includes storage layout and integration-test coverage expectations.
---

# Synthetic Input Presets

Use this skill when a demo includes seeded/synthetic example inputs.

## When to Apply

- Demo uses sample/synthetic data to make flows reproducible
- Inputs should be user-selectable at runtime
- You need predictable integration coverage for all presets

## Flow Coverage (Required)

Every planned flow within the demo must be covered by at least one synthetic preset. Collectively, presets must exercise all flows (headline items, main paths, guardrail-allow paths). No flow may exist without preset data that reaches it.

## UI Conventions (Required)

- Global preset selector is visible in the primary input area
- "Apply preset" populates fields only; it never executes the flow
- "Run/Submit" triggers guardrails and then main flow
- "Reset/Clear" restores empty state or baseline preset state, per demo contract

Presets must never auto-run on app/page load.

## Interaction Contract

Each preset-enabled surface should define:

- Selector control id and label
- Apply action behavior (populate-only)
- Run action behavior (guardrails -> main call)
- Reset/Clear behavior
- Disabled/loading states for all controls

## Storage Conventions

Store preset definitions in repo-owned, reviewable files (not ad-hoc literals in UI code).

Recommended conventions:

- Path: `apps/<surface>/src/presets/` for frontend-owned presets
- Or path: `apps/api/app/<domain>/presets/` for server-shared presets
- One canonical preset collection file per feature (JSON/YAML/TS module)
- Stable `preset_id` keys and deterministic field ordering

Keep preset content explicitly labeled synthetic/example data.

## Inspectability (Required)

Preset data must be human-readable at a glance and reviewable in git diffs.

- `ordered_inputs`: one short value per UI field; avoid long paragraphs
- `expected_outputs`: prefer `EmbeddedDataObject` (summary + sample_records) when outputs are structured; use concise string only for simple single-line expectations
- `notes`: keep brief; use "none" when no notes
- Preset labels and IDs must be stable and descriptive for quick scanning

## Execution Semantics

- Applying presets and manually entered inputs must go through the same server-side guardrails
- Guardrail rejects must show user-visible messages and prevent main model calls
- Successful guardrails allow normal execution

## Test Conventions (Required)

- [ ] Every planned flow is covered by at least one preset
- [ ] Integration tests iterate all defined presets
- [ ] For each preset: apply -> run -> assert guardrails pass in mocked tier
- [ ] For each preset: assert main flow is reached in mocked tier
- [ ] At least one rejected-case test verifies zero main-model calls on guardrail fail
- [ ] Optional live tier (opt-in) runs one minimal preset when credentials/flags are enabled

## CI Guidance

- Default CI runs mocked preset integration coverage for every preset
- Live preset smoke tests remain non-blocking opt-in checks unless explicitly required
