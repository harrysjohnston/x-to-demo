---
name: multimodal-inputs
description: Requirements for audio and image input wherever such inputs feature. Incorporates push-to-record, mic visualizer, playback for audio; camera-primary capture, upload, and inspect for images. File-type allowlists dictated by OpenAI APIs (look up via MCP). Use when demo includes audio or image input.
---

# Multimodal Inputs

Requirements for audio and image input apply **wherever such inputs feature** – whenever audio or image is used, whether single-modality or multimodal.

## When to Apply

- Demo includes audio input (microphone, voice, speech-to-text)
- Demo includes image input (camera, upload, vision)
- User implements or modifies multimodal capture

---

## Audio Inputs

### Primary Capture

**Push-to-record** – required and primary. Choose one:
- **Hold**: Press-and-hold to record; release to stop
- **Toggle**: Explicit press-to-start / press-to-stop button

Do not use as primary: auto-recording, background capture, file-upload-only (upload may exist as secondary).

### Control Requirements

- Clearly visible; keyboard and touch accessible
- Expose explicit states: `idle` | `recording` | `processing` | `error`
- Treat recording state as a **state machine** (no ambiguous states)
- Disable conflicting controls while recording

### Playback

Recorded audio must always be playable. Provide a play button or equivalent so the user can listen before submitting or discarding.

### Mic Visualizer

When voice/mic is active: show a **live mic-level visualizer** (RMS or peak) visible while recording/streaming. Visual states: `active` | `muted` | `paused` | `no-permission`.

### State Machine

```
idle ──(start)──> recording ──(stop)──> processing ──(done)──> idle
  ^                                                      │
  └────────────────────(cancel/error)───────────────────┘
  recording ──(error)──> error
  processing ──(error)──> error
```

### Permission Handling

On `getUserMedia` rejection (e.g., `NotAllowedError`):
- Transition to `error` state
- Show message: "Microphone access denied. Please allow microphone access and try again."
- Provide retry action; optionally link to browser/OS settings

### Tests (Audio)

- Interaction – mode semantics (toggle: tap start/stop; hold: press/release)
- State transitions
- Playback visible and playable after recording
- Visualizer renders in voice mode

---

## Image Inputs

### Primary Capture

**Device camera capture** – required and primary. Use `getUserMedia` video or equivalent as the default path.

Do not use as primary: file-upload-only, auto-capture on load.

### Secondary: Upload

Image upload allowed as secondary (cannot be sole path).

### Inspect

User must be able to **view/inspect** already uploaded or captured image before submitting (analogous to audio playback).

### Control Requirements

- Clearly visible; keyboard and touch accessible
- Expose explicit states: `idle` | `capturing` | `processing` | `error`
- Treat capture state as a **state machine**

### Permission Handling

On camera denied: transition to `error`; show clear message; provide retry.

### Tests (Image)

- Camera capture primary path works
- Upload secondary path works
- Inspect/preview visible before submit

---

## File Types

### Allowlists Dictated by OpenAI APIs

MIME types and extensions per modality must match what the target OpenAI API accepts. **Look up OpenAI API documentation via MCP** (e.g., `mcp_openaiDeveloperDocs_search_openai_docs`) when implementing – formats may vary by API/version.

### Consistent Handling Across Input Modes

All input paths (record, capture, upload) must align to the same allowlist per modality:

- **Record/capture output**: MediaRecorder (audio) and canvas/Blob (image) must produce formats in the allowlist, or convert before send
- **Upload input**: Accept only allowlist types; reject others
- **Server validation**: Same allowlist in deterministic_type_checks; unsupported verdict for non-matching types
- **Reject messaging**: Consistent "Unsupported file type" (or similar) regardless of whether input came from record, capture, or upload

## Additional Resources

- For implementation examples, MCP lookup, and test patterns, see [reference.md](reference.md)
