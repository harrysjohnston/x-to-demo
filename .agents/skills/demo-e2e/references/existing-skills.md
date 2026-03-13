# Existing Skills Map

Use this file to decide when `demo-e2e` should delegate instead of restating guidance.

## Authoritative Reuse

| Concern | Skill path | When to reuse | Status |
| --- | --- | --- | --- |
| Audio and image input UX | `../../multimodal-inputs/SKILL.md` | Any demo with audio or image input | Authoritative |
| OpenAI live-test posture | `../../openai-live-integration-tests/SKILL.md` | Any demo with OpenAI runtime calls and live coverage | Authoritative |
| Vision and image workflows | `../../openai-images-vision/SKILL.md` | Image understanding, generation, or editing flows | Authoritative for API/workflow choices |
| Audio and speech workflows | `../../openai-audio-speech/SKILL.md` | STT, translation, TTS, or realtime audio flows | Authoritative for API/workflow choices |
| Long-running execution process | `../../long-running-tasks/SKILL.md` | Multi-milestone or interruption-prone demo work | Authoritative |

## Advisory Or Operational Reuse

| Concern | Skill path | When to reuse | Status |
| --- | --- | --- | --- |
| Browser automation and evidence capture | `../../playwright-cli/SKILL.md` | When verifying the demo through automated browser interaction | Advisory / operational |

## Concerns Absorbed Into `demo-e2e`

| Concern | Local doc | Status |
| --- | --- | --- |
| Runtime guardrails pipeline, verdict handling, prompt skeletons, and preset integration rules | [../reference.md](../reference.md) | Local authority |
| Generated-output indicator behavior and tests | [../reference.md](../reference.md) | Local authority |
| Async loading, streaming, timeout, and retry patterns | [../reference.md](../reference.md) | Local authority |
| Seeded/synthetic input labeling and reset behavior | [../reference.md](../reference.md) | Local authority |
| OpenAI credentials, model defaults, override behavior, and pricing posture | [../reference.md](../reference.md) | Local authority |
| Baseline guardrails, presets, and label invariants | [../invariants.md](../invariants.md) | Local authority |
| Baseline demo obligations and outputs | [../modules/baseline.md](../modules/baseline.md) | Local authority |

## Coverage Gaps Kept In `demo-e2e`

These concerns do not currently have a narrower skill and therefore remain locally owned by `demo-e2e`:
These concerns do not currently have a narrower skill and therefore remain locally owned by `demo-e2e`:

- foundational baseline demo decisions about guardrails and preset posture
- generated-output indicators, async UI, seeded-label behavior, OpenAI config/defaults, and pricing posture
- walkthrough behavior and state-machine expectations
- tools-mode policy and synthetic tool-data constraints
- synthetic asset-generation policy for demos
- orchestration across scope, UX contract, implementation notes, and proof plan

If a future skill becomes the better canonical home for any of these, replace the local guidance with a pointer.
