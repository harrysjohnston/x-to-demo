---
name: openai-audio-speech
description: "Implement OpenAI audio workflows across speech-to-text, translation, text-to-speech, and realtime audio transcription. Use when building with the Audio API or Realtime API for: transcribing uploaded audio files, translating speech into English, generating spoken audio from text, choosing voices and output formats, handling audio file constraints, or deciding when file-based endpoints should become realtime streaming."
---

# OpenAI Audio and Speech

Implement OpenAI audio features without re-deriving endpoint choice or parameter support each time. Use this skill for file-based STT/TTS first, then switch to realtime only when latency, live turn handling, or streaming transcription actually requires it.

## Choose The API First

- Use the **Audio API** for:
  - file-based transcription
  - translation to English
  - text-to-speech generation
  - batch-like or request/response audio workflows
- Use the **Realtime API** for:
  - live microphone streaming
  - automatic turn detection
  - low-latency speech interactions
  - realtime transcription over WebSocket/WebRTC

Default to the simpler file endpoint unless the product truly needs streaming behavior.

## Build Speech-To-Text Flows

1. Decide which result you need:
   - transcription in the source language
   - translation into English
   - diarized transcript
   - streamed transcript deltas
2. Validate the uploaded audio before calling OpenAI.
3. Prefer the modern transcription models first, then fall back only when a feature requires it.
4. Choose response shape deliberately:
   - simple text
   - JSON with metadata
   - verbose JSON with timestamps
   - diarized JSON when speaker separation matters
5. Treat transcripts as model output, not ground truth, in evaluation or debugging workflows.

## Build Text-To-Speech Flows

1. Pick the TTS model based on latency/quality needs.
2. Choose a voice explicitly instead of relying on implicit defaults.
3. Use `instructions` only on models that support it.
4. Pick the output format that matches downstream playback or storage requirements.
5. Stream audio only when the UX benefits from progressive playback.

## Decide When To Use Realtime

Switch from file-based audio endpoints to Realtime only when one or more are true:

- the user speaks live into the app
- turn detection must be automatic
- partial transcripts or partial speech output matter
- end-to-end latency is part of the product experience

If none of those are true, keep the system on the simpler Audio API.

## Validate Inputs And Limits Up Front

- Reject unsupported audio file types before upload.
- Reject files above the documented upload limit before calling OpenAI.
- Keep server validation aligned with the target endpoint, not only the UI accept list.
- Normalize or convert capture output if the recorder produces a format your chosen endpoint does not accept.

## Coordinate With Other Skills

- Use `multimodal-inputs` when you modify microphone capture, playback, or upload UI.
- Use `demo-e2e` when you need this repo's baseline demo guidance for async audio UX, generated-media labeling, or shared OpenAI config conventions.
- Use `openai-live-integration-tests` when you add real OpenAI audio calls that need opt-in live coverage.

## Read The Reference

Open [references/official-guide.md](references/official-guide.md) when you need:

- endpoint selection rules
- file limits and allowed formats
- transcription model options
- timestamp, diarization, and streaming notes
- TTS model, voice, speed, and format constraints
- realtime escalation rules
