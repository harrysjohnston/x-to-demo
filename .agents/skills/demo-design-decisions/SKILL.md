---
name: demo-design-decisions
description: "Canonical design decisions for x-to-demo: guardrails (server-side, relevance + safety verdicts), synthetic presets (UI-selectable, test-validated, every flow covered). Use when implementing or modifying demos, guardrails, or preset systems."
---

# Demo Design Decisions

Short, explicit decisions. Record them in code comments and keep this skill as the source of truth.

## When to Apply

- Implementing or modifying demos
- Adding or changing guardrails
- Designing or changing synthetic input / preset systems

---

## 1. Guardrails Are Server-Side Only

Guardrails run on the server. No client-side guardrail logic.

- **Rationale**: Prevents bypass, ensures consistent enforcement, keeps sensitive logic out of the client bundle.

---

## 2. Guardrails: Two Structured-Output Model Calls

Guardrails use exactly two structured-output model calls:

| Call | Purpose |
|------|---------|
| **Relevance verdict** | Whether the input is on-topic and appropriate for the demo |
| **Safety verdict** | Whether the input is safe (no harmful, abusive, or policy-violating content) |

Both verdicts are produced via structured output (e.g. JSON schema, Pydantic models). No free-form text for verdicts.

---

## 3. Synthetic Inputs Are Global Presets (UI-Selectable, Not Auto-Run)

Synthetic inputs are **global presets** that users select in the UI. They are never auto-run.

- **Global**: Presets are defined once and available across the demo, not per-component.
- **Selectable**: User explicitly chooses a preset from a dropdown, list, or similar control.
- **Not auto-run**: Presets do not execute automatically on load or navigation.
- **Flow coverage**: Every planned flow in the demo must be covered by at least one synthetic preset. No flow may exist without preset data that exercises it.

---

## 4. Presets Require Integration Test Validation

Every preset must be validated via integration tests.

| Tier | Required | Purpose |
|------|----------|---------|
| **Mocked-by-default** | Yes | Fast CI, deterministic, no external deps |
| **Live** | Optional | End-to-end validation against real services |

Presets without passing integration tests (mocked tier) must not ship.

---

## Checklist for New Presets

- [ ] Preset is a global, UI-selectable option (not auto-run)
- [ ] Every planned flow has at least one preset that exercises it
- [ ] Integration test exists in mocked-by-default tier
- [ ] Test asserts preset produces expected output or state
- [ ] Live-tier test added if needed for E2E validation

---

## Checklist for Guardrails

- [ ] All guardrail logic runs server-side
- [ ] Relevance verdict uses structured output
- [ ] Safety verdict uses structured output
- [ ] No free-form text for verdicts
