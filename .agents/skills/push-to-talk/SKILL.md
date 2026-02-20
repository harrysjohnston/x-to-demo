---
name: push-to-talk
description: Ensures voice controls with microphone capture behave predictably and match user expectations. Use only when the demo includes microphone capture, push-to-talk, or press-and-hold recording. Covers toggle vs hold semantics, visual states, and permission handling.
---

# Push-to-Talk / Press-and-Hold Semantics

Ensures voice recording controls behave predictably. Apply **only** when the demo includes microphone capture or push-to-talk.

## When to Apply

- Demo includes microphone capture
- User implements or modifies push-to-talk or press-and-hold recording
- Voice input / speech-to-text features with manual recording control

## Required Outputs

1. **Exactly one explicit mode** – choose one:
   - **Toggle**: Tap to start, tap to stop; persistent active state between taps
   - **Hold**: Press-and-hold to record; release to stop

2. **Clear visual states** – UI must reflect: `idle` | `recording` | `processing` | `error`

## Implementation Checklist

- [ ] Treat recording state as a **state machine** (no ambiguous or overlapping states)
- [ ] Disable conflicting controls while recording (e.g., other record buttons, submit, navigation that would interrupt)
- [ ] Handle **permission denied** gracefully: show clear message, offer retry or settings link; do not fail silently

## State Machine

```
idle ──(start)──> recording ──(stop)──> processing ──(done)──> idle
  ^                                                      │
  └────────────────────(cancel/error)───────────────────┘
  recording ──(error)──> error
  processing ──(error)──> error
```

Valid transitions:
- `idle` → `recording` (user starts)
- `recording` → `processing` (user stops; audio sent for processing)
- `recording` → `error` (permission denied, media error, etc.)
- `processing` → `idle` (success)
- `processing` → `error` (transcription/API failure)
- `error` → `idle` (user dismisses or retries)

## Mode Semantics

| Mode | Start | Stop | Notes |
|------|-------|------|-------|
| **Toggle** | Tap/click | Tap/click again | Same control; state persists until second tap |
| **Hold** | Press down | Release | Pointer/touch events: `pointerdown` start, `pointerup`/`pointerleave` stop |

Do not mix modes (e.g., tap-to-start + release-to-stop). Pick one and document it.

## Permission Handling

On `getUserMedia` rejection (e.g., `NotAllowedError`):
- Transition to `error` state
- Show message: "Microphone access denied. Please allow microphone access and try again."
- Provide retry action (re-request permission)
- Optionally link to browser/OS settings for microphone

## Tests (Required)

| Test | Purpose |
|------|---------|
| **Interaction – mode semantics** | Toggle: tap starts, tap again stops. Hold: press starts, release stops. Assert correct start/stop behavior for chosen mode. |
| **State transitions** | `idle` → `recording` → `processing` → `idle`. Assert only valid transitions occur; no illegal state combinations. |

Use pointer/touch event simulation (e.g., `fireEvent.pointerDown`, `fireEvent.pointerUp`) for hold mode. Use click simulation for toggle mode.

## Additional Resources

- For implementation examples and test patterns, see [reference.md](reference.md)
