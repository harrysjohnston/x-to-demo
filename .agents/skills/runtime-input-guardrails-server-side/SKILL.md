---
name: runtime-input-guardrails-server-side
description: Canonical server-side guardrails workflow for runtime demo inputs with deterministic validation, two structured-output model verdicts (relevance, safety), strict reject handling, privacy-safe logging, and test requirements.
---

# Server-Side Runtime Input Guardrails

Use this skill when a demo accepts runtime user input and must gate inputs before the main AI call.

## When to Apply

- Runtime input is captured in UI and sent to API
- Input can be text, file, image, or audio
- The demo requires relevance/safety checks before feature execution

## Audio Input Capture

For audio/voice input, capture must follow the **multimodal-inputs** skill: push-to-record (press-and-hold or explicit start/stop) is the primary path. Do not use file-upload-only, auto-recording, or background capture as the primary input path.

## Canonical Architecture (Server-Side Only)

1. Client captures runtime input and sends it to the API.
2. Server runs deterministic type/format/size checks first.
3. Server calls model for relevance verdict (`RelevanceVerdict` structured output).
4. If relevant, server calls model for safety verdict (`SafetyVerdict` structured output).
5. Only `allow` reaches the main AI moment/model call.
6. Reject paths return user-visible messages and stop the flow.

Never run authoritative guardrails in the client.

## Deterministic Type Validation Guidance

Run deterministic checks before model calls:

- MIME/type allowlist and extension sanity checks
- Max payload size and per-modality limits
- Decode/parsing checks (e.g., valid UTF-8 text, readable JSON/image/audio container)
- Audio constraints (duration, channels/sample rate as needed)
- Unsupported modality/format short-circuit

If deterministic checks fail, return unsupported verdict and skip relevance/safety/main model calls.

## Two-Step Model Guardrails

Order is fixed:

1. Relevance model call -> `RelevanceVerdict`
2. Safety model call -> `SafetyVerdict`

Do not merge both into one call. Do not call the main model before both pass.

## Structured Output Schemas

Use strict JSON outputs with no extra fields.

```json
{
  "RelevanceVerdict": {
    "type": "object",
    "additionalProperties": false,
    "required": ["is_relevant", "reason", "user_message"],
    "properties": {
      "is_relevant": { "type": "boolean" },
      "reason": { "type": "string" },
      "user_message": { "type": "string" }
    }
  }
}
```

```json
{
  "SafetyVerdict": {
    "type": "object",
    "additionalProperties": false,
    "required": ["is_safe", "reason", "user_message"],
    "properties": {
      "is_safe": { "type": "boolean" },
      "reason": { "type": "string" },
      "user_message": { "type": "string" }
    }
  }
}
```

## Prompt Skeletons (Structured Output)

Each guardrail call should include system/developer/user layers and end with an explicit JSON-only instruction.

### Relevance Call

```text
System:
You classify whether an input is relevant to a specific demo scope.
Return JSON only matching the provided schema.

Developer:
Demo scope/context: <what this demo does>
Supported modalities: <text,image,audio,...>
Decision policy: mark not relevant when input falls outside demo scope.
Output schema: RelevanceVerdict.

User:
Runtime input summary/metadata: <normalized payload details>
Optional extracted content: <safe truncated text or derived metadata>

Final instruction:
Output JSON only. Do not include prose, markdown, or extra keys.
```

### Safety Call

```text
System:
You classify whether a relevant input is safe for the demo policy.
Return JSON only matching the provided schema.

Developer:
Demo scope/context: <what this demo does>
Supported modalities: <text,image,audio,...>
Safety policy: <demo policy constraints>
Output schema: SafetyVerdict.

User:
Runtime input summary/metadata: <normalized payload details>
Optional extracted content: <safe truncated text or derived metadata>

Final instruction:
Output JSON only. Do not include prose, markdown, or extra keys.
```

## Verdict Handling Conventions

- `unsupported`: input type is unsupported or relevance says out-of-scope
  - User message style: "That input is not supported for this demo" / "That input is not relevant to this demo."
  - Action: stop flow, no main model call
- `block`: safety fails
  - User message style: "I can't help with that request in this demo."
  - Action: stop flow, no main model call
- `allow`: both checks pass
  - Action: proceed to main model call

## Logging Constraints

- Never persist raw prompts/responses or sensitive user content
- Log only:
  - request/run id
  - deterministic validation outcomes
  - relevance/safety decision labels
  - timing/latency for each step
  - structured-output schema parse success/failure

## Testing Checklist (Required)

- [ ] Mocked-by-default tests for `allow`, `unsupported`, and `block`
- [ ] Assertions that rejected paths trigger zero main model calls
- [ ] Assertions for user-visible reject messages
- [ ] Assertions for deterministic validation short-circuit behavior
- [ ] Optional live smoke test (opt-in) with minimal safe input
