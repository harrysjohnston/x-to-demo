# In-Flight Loading UI – Implementation Reference

## React – Loading State Pattern

```tsx
function AsyncForm() {
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setStatus("loading");
    setError(null);
    try {
      await api.submit();
      setStatus("success");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
      setStatus("error");
    }
  };

  return (
    <>
      {status === "loading" && (
        <div data-testid="loading-ui" role="status" aria-live="polite">
          <Spinner /> Processing…
        </div>
      )}
      {status === "error" && <div data-testid="error-ui">{error}</div>}
      <button onClick={handleSubmit} disabled={status === "loading"}>
        Submit
      </button>
    </>
  );
}
```

## Streaming Indicator

```tsx
function StreamingOutput({ isStreaming, content }) {
  return (
    <div>
      {content}
      {isStreaming && (
        <span data-testid="streaming-indicator" aria-label="Generating">
          ▋
        </span>
      )}
    </div>
  );
}
```

## Timeout Handling

```tsx
const TIMEOUT_MS = 30_000;

async function fetchWithTimeout(url: string) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(id);
    return res;
  } catch (e) {
    clearTimeout(id);
    if (e instanceof Error && e.name === "AbortError") {
      throw new Error("Request timed out. Try again.");
    }
    throw e;
  }
}
```

## UI Tests (React Testing Library)

**Loading appears immediately on request start:**

```tsx
it("shows loading animation immediately on request start", async () => {
  const mockApi = vi.fn().mockImplementation(() => new Promise(() => {}));
  render(<AsyncForm onSubmit={mockApi} />);

  await userEvent.click(screen.getByRole("button", { name: /submit/i }));

  expect(screen.getByTestId("loading-ui")).toBeInTheDocument();
  expect(screen.getByText(/processing|thinking|generating/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /submit/i })).toBeDisabled();
});
```

**Loading clears on success/failure:**

```tsx
it("clears loading on success", async () => {
  const mockApi = vi.fn().mockResolvedValue(undefined);
  render(<AsyncForm onSubmit={mockApi} />);

  await userEvent.click(screen.getByRole("button", { name: /submit/i }));
  expect(screen.getByTestId("loading-ui")).toBeInTheDocument();

  await waitFor(() => expect(screen.queryByTestId("loading-ui")).not.toBeInTheDocument());
  expect(screen.getByRole("button", { name: /submit/i })).toBeEnabled();
});

it("clears loading on failure", async () => {
  const mockApi = vi.fn().mockRejectedValue(new Error("API error"));
  render(<AsyncForm onSubmit={mockApi} />);

  await userEvent.click(screen.getByRole("button", { name: /submit/i }));
  await waitFor(() => expect(screen.queryByTestId("loading-ui")).not.toBeInTheDocument());

  expect(screen.getByTestId("error-ui")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /submit/i })).toBeEnabled();
});
```

**Controls follow disable/enable rules:**

```tsx
it("disables submit during request, enables after", async () => {
  let resolve: () => void;
  const mockApi = vi.fn().mockImplementation(() => new Promise((r) => { resolve = r; }));
  render(<AsyncForm onSubmit={mockApi} />);
  const btn = screen.getByRole("button", { name: /submit/i });

  await userEvent.click(btn);
  expect(btn).toBeDisabled();

  resolve!();
  await waitFor(() => expect(btn).toBeEnabled());
});
```
