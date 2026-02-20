---
name: voice-mic-visualizer
description: Ensures voice/microphone input shows a live mic-level visualizer so users know audio is being captured. Use only when the demo includes voice input or microphone capture. Covers RMS/peak visualization and muted/paused/no-permission states.
---

# Voice Input Requires a Live Mic-Level Visualizer

Makes it obvious that the microphone is capturing audio. Apply **only** when voice/mic input is used.

## When to Apply

- Demo uses voice input or microphone capture
- Recording or streaming audio from the user's mic
- User asks about mic feedback, audio levels, or voice UI

## Required Outputs

1. **Real-time mic-level visualizer** – RMS or peak level, visible while recording/streaming
2. **Visual states** – UI must reflect: `muted` | `paused` | `no-permission`

## Implementation Checklist

- [ ] Show a live level indicator (bar, waveform, or meter) while mic is active
- [ ] Use RMS or peak amplitude; update in real time (e.g., via `AnalyserNode` or equivalent)
- [ ] Display visual states: muted (user muted), paused (recording paused), no-permission (denied)
- [ ] Visualizer is visible whenever voice mode is active (recording or streaming)

## Visualizer Behavior

| State | Visual | Meaning |
|-------|--------|---------|
| Active | Animated bars/level | Mic capturing; level reflects input |
| Muted | Static or dimmed, "Muted" label | User muted; no level updates |
| Paused | Static, "Paused" label | Recording paused; no capture |
| No permission | Message + retry | `getUserMedia` denied; no visualizer |

## Level Source

- **Web Audio API**: `AnalyserNode` + `getByteFrequencyData` or `getByteTimeDomainData` for RMS/peak
- **MediaRecorder**: Use `AudioContext` + `createMediaStreamSource` to feed analyser from stream
- **Update rate**: 60fps or ~16ms interval for smooth animation

## Tests (Required)

| Test | Purpose |
|------|---------|
| **Visualizer renders in voice mode** | When voice/recording UI is shown, assert the visualizer component is in the DOM (mocked `AnalyserNode` or no real mic) |
| **Level updates with simulated audio** | Mock or inject level values; assert the visualizer reflects updates (e.g., bar height, displayed value) |

Use mocks for `getUserMedia`, `AudioContext`, or a test double that provides level values. Do not require a real microphone in CI.

## Additional Resources

- For implementation examples and test patterns, see [reference.md](reference.md)
