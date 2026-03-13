# Multimodal Module

## When It Applies

Apply when audio or image input/output is part of the core demo, whether primary or secondary.

## Extra Responsibilities

- Define modality-specific capture or upload behavior.
- Define permission, feasibility, and recovery states.
- Keep client allowlists and server deterministic validation aligned to the chosen OpenAI workflow.
- Require inspect-before-submit for images and playback-before-submit for recorded audio.
- Label generated media outputs where they are shown.

## Extra Outputs Or Checks

- audio or image interaction model and state machine
- capture/upload/preview or playback behavior
- permission-denied and hardware-missing behavior
- modality allowlist and deterministic validation notes
- modality-specific mocked tests and opt-in live tests when OpenAI calls exist

## Reuse These Skills

- `../../multimodal-inputs/SKILL.md` as the authoritative UI contract for audio/image input behavior
- `../../openai-images-vision/SKILL.md` for image and vision workflow selection
- `../../openai-audio-speech/SKILL.md` for audio, speech, transcription, translation, and TTS workflow selection
- [../reference.md](../reference.md) for generated media labeling, long or streaming modality requests, and baseline OpenAI config conventions
- `../../openai-live-integration-tests/SKILL.md` for live-test mapping

## Notes

- Do not restate unstable file-type or limit details here; check the authoritative OpenAI docs when implementing.
- If multimodal is not part of the requested demo, keep this module inactive.
