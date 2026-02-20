# Voice Mic Visualizer – Implementation Reference

## Web Audio API – Analyser Setup

```typescript
function useMicLevel(stream: MediaStream | null) {
  const [level, setLevel] = useState(0);
  const [state, setState] = useState<"active" | "muted" | "paused" | "no-permission">("active");

  useEffect(() => {
    if (!stream) return;
    const ctx = new AudioContext();
    const source = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);

    const data = new Uint8Array(analyser.frequencyBinCount);
    let raf: number;

    const update = () => {
      analyser.getByteTimeDomainData(data);
      const rms = Math.sqrt(data.reduce((s, v) => s + (v - 128) ** 2, 0) / data.length);
      setLevel(Math.min(1, rms / 128));
      raf = requestAnimationFrame(update);
    };
    raf = requestAnimationFrame(update);
    return () => cancelAnimationFrame(raf);
  }, [stream]);

  return { level, state, setState };
}
```

## Visualizer Component (React)

```tsx
function MicLevelVisualizer({ level, state }: { level: number; state: string }) {
  if (state === "no-permission") {
    return <div data-testid="mic-visualizer">Microphone access denied</div>;
  }
  if (state === "muted" || state === "paused") {
    return (
      <div data-testid="mic-visualizer" aria-label={state}>
        {state.charAt(0).toUpperCase() + state.slice(1)}
      </div>
    );
  }
  return (
    <div data-testid="mic-visualizer" role="img" aria-label="Microphone level">
      <div className="bar" style={{ height: `${level * 100}%` }} />
    </div>
  );
}
```

## Mocked Tests

**Visualizer renders in voice mode:**

```tsx
it("renders visualizer when voice mode is active", () => {
  render(
    <VoiceInput mode="voice" stream={null} />
  );
  expect(screen.getByTestId("mic-visualizer")).toBeInTheDocument();
});
```

```tsx
it("renders visualizer in voice mode even without stream", () => {
  const { container } = render(<VoiceInput mode="voice" />);
  expect(container.querySelector("[data-testid='mic-visualizer']")).toBeInTheDocument();
});
```

**Level updates with simulated audio:**

```tsx
it("level updates with simulated audio", () => {
  const { rerender } = render(<MicLevelVisualizer level={0} state="active" />);
  const bar = screen.getByTestId("mic-visualizer").querySelector(".bar");
  expect(bar).toHaveStyle({ height: "0%" });

  rerender(<MicLevelVisualizer level={0.5} state="active" />);
  expect(bar).toHaveStyle({ height: "50%" });

  rerender(<MicLevelVisualizer level={1} state="active" />);
  expect(bar).toHaveStyle({ height: "100%" });
});
```

```tsx
it("shows muted state when muted", () => {
  render(<MicLevelVisualizer level={0} state="muted" />);
  expect(screen.getByText("Muted")).toBeInTheDocument();
});

it("shows no-permission state when denied", () => {
  render(<MicLevelVisualizer level={0} state="no-permission" />);
  expect(screen.getByText(/denied|permission/i)).toBeInTheDocument();
});
```
