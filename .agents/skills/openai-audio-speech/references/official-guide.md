# OpenAI Audio and Speech Reference

Source pages:

- `https://developers.openai.com/api/docs/guides/audio`
- `https://developers.openai.com/api/docs/guides/speech-to-text/`
- `https://developers.openai.com/api/docs/guides/text-to-speech/`
- `https://developers.openai.com/api/docs/guides/realtime-transcription/`
- `https://developers.openai.com/api/reference/resources/audio/subresources/transcriptions/methods/create/`
- `https://developers.openai.com/api/reference/resources/audio/subresources/speech/methods/create/`

Use OpenAI docs MCP tools to re-check current model snapshots, voice availability, and parameter support before shipping.

## Overview

The OpenAI audio surface breaks down into four common jobs:

- transcribe audio into text
- translate spoken audio into English text
- generate speech from text
- stream audio or transcription in realtime

Choose the simplest endpoint that satisfies the product requirement.

## Speech To Text

The Audio API speech-to-text surface provides:

- `transcriptions`
- `translations`

Current speech-to-text guide notes:

- file uploads are limited to 25 MB
- supported input file types are `mp3`, `mp4`, `mpeg`, `mpga`, `m4a`, `wav`, and `webm`
- known speaker reference clips for diarization accept the same formats when passed as data URLs

Documented transcription models include:

- `whisper-1`
- `gpt-4o-mini-transcribe`
- `gpt-4o-transcribe`
- `gpt-4o-transcribe-diarize`

Use the translation path only when the product specifically needs English output from spoken audio. Do not use translation when the requirement is “transcribe faithfully in the original language.”

## Response Shapes For Transcription

Common output shapes and options include:

- basic JSON text output
- verbose JSON with metadata
- word timestamps
- segment timestamps
- diarized JSON
- streaming transcript deltas
- optional logprobs on supported paths

Choose the lightest response format that still supports downstream requirements.

Examples:

- plain transcript for note-taking
- word timestamps for subtitle alignment
- segment timestamps for chunked playback UI
- diarized JSON for call or meeting workflows

## Text To Speech

The `audio/speech` endpoint generates audio from input text.

Current API reference notes:

- input text max length: 4096 characters
- available TTS models include `tts-1`, `tts-1-hd`, and `gpt-4o-mini-tts`
- built-in voices include `alloy`, `ash`, `ballad`, `coral`, `echo`, `fable`, `nova`, `onyx`, `sage`, `shimmer`, `verse`, `marin`, and `cedar`
- output formats include `mp3`, `opus`, `aac`, `flac`, `wav`, and `pcm`
- supported speed range is `0.25` to `4.0`

Important constraint:

- `instructions` for controlling voice style does not work with `tts-1` or `tts-1-hd`

The text-to-speech guide notes that voices are currently optimized for English. It also calls out `marin` and `cedar` as the best-quality built-in voices.

## Streaming TTS

Streaming TTS is useful only when the UX benefits from hearing speech start before the full response is complete.

Do not add streaming by default if:

- the audio clip is short
- the user is waiting on a complete file anyway
- the player expects a finished file blob or URL

## Realtime Transcription

Use realtime transcription or speech interaction when:

- microphone audio is arriving continuously
- turn detection matters
- the app needs partial transcripts while the user is still speaking
- you need conversational audio latency rather than upload-and-wait behavior

The realtime transcription guide documents these input encodings:

- `audio/pcm` at 24 kHz mono PCM
- `audio/pcmu` (G.711 mu-law)
- `audio/pcma` (G.711 A-law)

Realtime sessions can also configure:

- noise reduction
- asynchronous input transcription
- VAD / turn detection
- extra event fields such as transcription logprobs

## Practical Decision Rules

### Use file-based transcription when:

- the user uploads an existing file
- you only need a final transcript
- latency is not interactive
- infrastructure simplicity matters more than streaming

### Use realtime transcription when:

- audio is captured live
- the app should react while the user is still talking
- automatic turn boundaries are part of the UX

### Use TTS when:

- the product needs playable spoken output from text
- voice, pacing, or delivery is a user-facing feature

## Implementation Cautions

- Do not assume recorder output matches accepted API formats; convert when necessary.
- Do not treat STT transcripts as exact ground truth in evals; clipping, ASR mistakes, or turn-boundary issues can distort them.
- Keep UI accept lists, server validation, and endpoint support aligned.
- Avoid moving to Realtime because it feels more advanced; use it only when the product actually needs streaming semantics.
- If speaker separation matters, choose a diarization-capable workflow intentionally rather than trying to infer speakers after a plain transcript.

## Related Official Pages

- Audio overview: `https://developers.openai.com/api/docs/guides/audio`
- Speech to text: `https://developers.openai.com/api/docs/guides/speech-to-text/`
- Text to speech: `https://developers.openai.com/api/docs/guides/text-to-speech/`
- Realtime transcription: `https://developers.openai.com/api/docs/guides/realtime-transcription/`
