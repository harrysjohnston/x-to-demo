# Multimodal Inputs – Implementation Reference

## File-Type Allowlists

**Allowlists must be dictated by OpenAI APIs.** Look up supported formats via MCP when implementing:

```
mcp_openaiDeveloperDocs_search_openai_docs(query="image file types supported vision")
mcp_openaiDeveloperDocs_search_openai_docs(query="audio file types supported")
```

Example placeholders (verify against current OpenAI docs):
- **Image**: image/png, image/jpeg, image/webp, image/gif
- **Audio**: audio/webm, audio/mp4, audio/mpeg, audio/wav

Use the same allowlist for record, capture, and upload paths. Reject non-matching types with consistent messaging.

## Audio – State Machine (TypeScript)

```typescript
type RecordingState = "idle" | "recording" | "processing" | "error";
```

## Audio – Toggle Mode (React)

```tsx
function VoiceButton() {
  const [state, setState] = useState<RecordingState>("idle");
  const handleClick = () => {
    if (state === "idle") startRecording().then(() => setState("recording"));
    else if (state === "recording") stopRecording().then(() => setState("processing"));
  };
  return (
    <button onClick={handleClick} disabled={state === "processing"} aria-pressed={state === "recording"}>
      {state === "idle" && "Tap to record"}
      {state === "recording" && "Tap to stop"}
      {state === "processing" && "Processing…"}
      {state === "error" && "Error – tap to retry"}
    </button>
  );
}
```

## Audio – Hold Mode (React)

```tsx
<button
  onPointerDown={handlePointerDown}
  onPointerUp={handlePointerUp}
  onPointerLeave={handlePointerUp}
  onKeyDown={(e) => { if (e.key === " ") { e.preventDefault(); if (state === "idle") handlePointerDown(); } }}
  onKeyUp={(e) => { if (e.key === " ") { e.preventDefault(); if (state === "recording") handlePointerUp(); } }}
>
  Hold to record
</button>
```

## Audio – Playback

```tsx
function RecordedAudioPlayback({ blob }: { blob: Blob }) {
  const url = URL.createObjectURL(blob);
  return (
    <div>
      <audio src={url} controls data-testid="playback-audio" />
      <button onClick={() => document.querySelector("audio")?.play()}>Play</button>
    </div>
  );
}
```

## Audio – Mic Visualizer (AnalyserNode)

```typescript
const ctx = new AudioContext();
const source = ctx.createMediaStreamSource(stream);
const analyser = ctx.createAnalyser();
analyser.fftSize = 256;
source.connect(analyser);
// getByteTimeDomainData for RMS; update at ~60fps
```

## Image – Camera Capture Primary

```typescript
const stream = await navigator.mediaDevices.getUserMedia({ video: true });
// Capture frame to canvas -> Blob; ensure format in allowlist
```

## Image – Inspect Before Submit

```tsx
function ImagePreview({ blob }: { blob: Blob }) {
  const url = URL.createObjectURL(blob);
  return <img src={url} alt="Captured or uploaded" data-testid="image-preview" />;
}
```

## Tests

**Audio – mode semantics, playback, visualizer:**
- Toggle: tap starts, tap again stops
- Hold: press starts, release stops
- Playback control visible and playable after recording
- Visualizer in DOM when voice mode active; level updates with simulated audio

**Image – capture, upload, inspect:**
- Camera capture produces inspectable image
- Upload produces inspectable image
- Preview visible before submit
