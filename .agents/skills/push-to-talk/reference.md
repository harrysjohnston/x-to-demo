# Push-to-Talk – Implementation Reference

## State Machine (TypeScript)

```typescript
type RecordingState = "idle" | "recording" | "processing" | "error";

const VALID_TRANSITIONS: Partial<Record<RecordingState, RecordingState[]>> = {
  idle: ["recording"],
  recording: ["processing", "error"],
  processing: ["idle", "error"],
  error: ["idle"],
};

function canTransition(from: RecordingState, to: RecordingState): boolean {
  return VALID_TRANSITIONS[from]?.includes(to) ?? false;
}
```

## Toggle Mode (React)

```tsx
function VoiceButton() {
  const [state, setState] = useState<RecordingState>("idle");

  const handleClick = () => {
    if (state === "idle") {
      startRecording().then(() => setState("recording"));
    } else if (state === "recording") {
      stopRecording().then(() => setState("processing"));
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={state === "processing"}
      aria-pressed={state === "recording"}
      aria-label={state === "recording" ? "Stop recording" : "Start recording"}
    >
      {state === "idle" && "Tap to record"}
      {state === "recording" && "Tap to stop"}
      {state === "processing" && "Processing…"}
      {state === "error" && "Error – tap to retry"}
    </button>
  );
}
```

## Hold Mode (React)

```tsx
function VoiceButton() {
  const [state, setState] = useState<RecordingState>("idle");

  const handlePointerDown = () => {
    if (state === "idle") startRecording().then(() => setState("recording"));
  };

  const handlePointerUp = () => {
    if (state === "recording") stopRecording().then(() => setState("processing"));
  };

  return (
    <button
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
      disabled={state === "processing"}
      aria-pressed={state === "recording"}
    >
      Hold to record
    </button>
  );
}
```

## Permission Handling

```typescript
async function startRecording(): Promise<void> {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    // ... start MediaRecorder
  } catch (err) {
    if (err instanceof DOMException && err.name === "NotAllowedError") {
      setState("error");
      setErrorMessage("Microphone access denied. Please allow access and try again.");
    }
    throw err;
  }
}
```

## Interaction Tests (React Testing Library)

**Toggle mode:**

```tsx
it("toggle mode: tap starts, tap again stops", async () => {
  render(<VoiceButton />);
  const btn = screen.getByRole("button", { name: /tap to record/i });

  await userEvent.click(btn);
  expect(screen.getByRole("button", { name: /tap to stop/i })).toBeInTheDocument();

  await userEvent.click(btn);
  expect(screen.getByText(/processing/i)).toBeInTheDocument();
});
```

**Hold mode:**

```tsx
it("hold mode: press starts, release stops", () => {
  render(<VoiceButton />);
  const btn = screen.getByRole("button", { name: /hold to record/i });

  fireEvent.pointerDown(btn);
  expect(screen.getByRole("button", { pressed: true })).toBeInTheDocument();

  fireEvent.pointerUp(btn);
  expect(screen.getByText(/processing/i)).toBeInTheDocument();
});
```

## State Transition Tests

```tsx
it("transitions idle → recording → processing → idle", async () => {
  const { result } = renderHook(() => useRecordingState());
  expect(result.current.state).toBe("idle");

  act(() => { result.current.start(); });
  expect(result.current.state).toBe("recording");

  act(() => { result.current.stop(); });
  expect(result.current.state).toBe("processing");

  await waitFor(() => expect(result.current.state).toBe("idle"));
});
```
