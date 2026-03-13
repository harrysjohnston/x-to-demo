# Assets Module

## When It Applies

Apply when the demo needs project-owned synthetic text, image, audio, or seeded datasets as named assets rather than only simple inline presets.

## Extra Responsibilities

- Decide whether assets are truly required. If not, keep the asset inventory empty.
- Keep assets synthetic, deterministic, and committed or otherwise project-owned.
- Do not depend on live asset generation at startup.
- Keep asset provenance obvious in both storage and UI labeling.

## Extra Outputs Or Checks

- required asset inventory with purpose and where-used mapping
- generation or sourcing notes for each asset
- storage and naming plan
- synthetic labeling plan in the UI
- validation checks proving the assets exist, are sane, and are not generated live at startup

## Reuse These Skills

- [../reference.md](../reference.md) for seeded asset labeling and generated-output indicators
- `../../openai-images-vision/SKILL.md` for image asset generation or analysis flows
- `../../openai-audio-speech/SKILL.md` for audio asset generation or transcription flows
- `../../openai-live-integration-tests/SKILL.md` when new OpenAI calls are introduced

## Local Authority That Stays Here

No narrower skill currently owns the synthetic asset-generation policy for demo E2E work. Keep these rules here:

- use project-owned synthetic assets only
- avoid ad-hoc internet assets
- make startup independent from live generation
