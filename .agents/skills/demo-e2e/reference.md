# Demo E2E Reference

Use this reference when implementing the baseline demo details that are now owned by `demo-e2e`.

## Generated Output Indicators

Use one reusable indicator component for every AI-generated or tool-generated surface.

- Accessible name: `Generated content`
- Minimum behavior: icon required, `Generated` label optional when space allows
- Placement should stay consistent per surface type and visible without scrolling

### Common Placements

| Context | Placement | Minimum label behavior |
| --- | --- | --- |
| Assistant/chat message | Start of message or avatar area | Icon, optional text |
| Inline generated text | Before or after the generated block | Text when space allows |
| Card or panel | Header or corner | Icon plus optional text |
| Code block | Header or adjacent label | Icon required |
| Tool result or log row | Header or row prefix | Icon required |

### Minimal React Pattern

```tsx
function GeneratedBadge({ showLabel = false }: { showLabel?: boolean }) {
  return (
    <span data-testid="generated-badge" role="img" aria-label="Generated content">
      <span aria-hidden>✨</span>
      {showLabel ? <span>Generated</span> : null}
    </span>
  );
}
```

### Tests

- Assert every generated surface contains the reusable badge or indicator.
- Query by `aria-label="Generated content"` or a stable test id when layouts are compact.
- Prefer parameterized tests when multiple generated surfaces exist.

## Async Request UI

Use an explicit request state model:

- `idle`
- `loading`
- `streaming`
- `success`
- `error`
- `timeout`

### Core Rules

- Show loading UI immediately when the request starts.
- Show working copy such as `Processing...`, `Generating...`, or equivalent.
- Disable the initiating control and declared conflicting controls during the request.
- Re-enable controls after success, error, or timeout.
- Keep timeout and error recovery explicit and retryable.

### Minimal React Pattern

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
      {status === "loading" ? (
        <div data-testid="loading-ui" role="status" aria-live="polite">
          Processing...
        </div>
      ) : null}
      {status === "error" ? <div data-testid="error-ui">{error}</div> : null}
      <button onClick={handleSubmit} disabled={status === "loading"}>
        Submit
      </button>
    </>
  );
}
```

### Streaming Indicator Pattern

```tsx
function StreamingOutput({ isStreaming, content }: { isStreaming: boolean; content: string }) {
  return (
    <div>
      {content}
      {isStreaming ? <span data-testid="streaming-indicator" aria-label="Generating">▋</span> : null}
    </div>
  );
}
```

### Timeout Pattern

```tsx
const TIMEOUT_MS = 30_000;

async function fetchWithTimeout(url: string) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return await fetch(url, { signal: controller.signal });
  } finally {
    clearTimeout(timeoutId);
  }
}
```

### Tests

- Loading UI appears immediately after the action starts.
- Submit and conflicting controls disable during the request.
- Loading clears on success and on failure.
- Timeout shows a specific timeout message and a retry path.

## Runtime Guardrails

### Canonical Flow

1. Client captures runtime input and sends it to the server.
2. Server runs deterministic validation first.
3. Server runs exactly one relevance verdict call.
4. Server runs exactly one safety verdict call if relevance allows the input.
5. Only `allowed` reaches the main AI call or tool flow.
6. Reject paths return a user-visible message and stop execution.

### Deterministic Validation

Run these before any model call:

- MIME, extension, or modality allowlist checks
- payload size checks
- parse or decode checks
- modality-specific technical constraints where applicable
- unsupported-format short-circuit behavior

If deterministic validation fails, return `unsupported` and skip relevance, safety, and main calls.

### Structured Verdict Contracts

Use strict structured outputs with no extra fields.

- `RelevanceVerdict { is_relevant: bool, reason: str, user_message: str }`
- `SafetyVerdict { is_safe: bool, reason: str, user_message: str }`

### Prompt Skeleton Rules

Each guardrail prompt should include:

- system instruction defining the classification task
- developer context with demo scope, supported modalities, and policy
- user payload containing normalized runtime metadata and safe extracted content when needed
- final instruction requiring JSON only with no extra keys

### Verdict Handling

- `unsupported`: unsupported type or out-of-scope input; no main call
- `blocked`: safety fail; no main call
- `allowed`: both guardrails pass; proceed

Return the guardrail `user_message` to the UI and show it near the input.

### Logging

Never log raw prompts, raw model outputs, API keys, or sensitive user payloads. Keep logs to:

- request or run id
- deterministic validation outcomes
- verdict labels
- timings
- structured-output parse success or failure

### Tests

- mocked tests for `allowed`, `unsupported`, and `blocked`
- rejected paths prove zero main-model calls
- deterministic-validation failures prove zero guardrail-model calls
- user-visible reject messaging is asserted

## Synthetic Presets

### UI Rules

- The preset selector is visible in the primary input area.
- `Apply preset` populates fields only.
- `Run` or `Submit` triggers guardrails and then the main flow.
- `Reset` or `Clear` restores empty or baseline seeded state per the demo contract.
- Presets never auto-run on app or page load.

### Storage Rules

- Store presets in project-owned, reviewable files.
- Use one canonical preset collection per feature.
- Keep stable `preset_id` values and deterministic field ordering.
- Keep preset content explicitly labeled as synthetic or example data.

### Inspectability

- Keep inputs short and field-like.
- Prefer structured expected outputs when the output is structured.
- Keep notes brief; use `none` when there is nothing to add.
- Use stable, descriptive preset ids and labels.

### Tests

- Every planned flow has at least one preset.
- Mocked tests iterate all presets: apply, run, assert guardrails pass for happy-path presets, assert main flow is reached.
- At least one rejected-case test proves zero main-model calls on guardrail fail.
- Optional live smoke can run one minimal preset subset.

## Seeded And Synthetic Input Labeling

Choose one base term and use it consistently:

- `Example`
- `Demo`
- `Synthetic`
- `Sample`

### Placement

| Context | Placement |
| --- | --- |
| Single prefilled input | Badge or inline label near the field |
| Multi-field seeded form | Banner above the form |
| Seeded dataset or list | Banner above the list or per-row tag |
| Seeded upload | Label near the file name or upload area |

### Reset Labels

Use one of these exact labels:

- `Reset`
- `Restore example`
- `Reload sample`
- `Clear and reseed`

### Minimal React Patterns

```tsx
function SeededInput({ value, label, syntheticLabel = "Example" }) {
  return (
    <div>
      <label>{label}</label>
      <span aria-label="Prefilled with example data">{syntheticLabel}</span>
      <textarea value={value} readOnly />
    </div>
  );
}
```

```tsx
function SeededForm({ children, onReset }: { children: ReactNode; onReset: () => void }) {
  return (
    <section>
      <div role="status">
        Prefilled with example data
        <button onClick={onReset}>Reset</button>
      </div>
      {children}
    </section>
  );
}
```

### Tests

- Seeded labels appear whenever seeded content is present.
- Reset restores the exact documented seeded state after user edits.

## OpenAI Environment And Model Configuration

### Credentials

- Read `OPENAI_API_KEY` through one shared config path.
- Trim and validate the configured key at startup or before first use.
- On missing config, raise a clear error that names `OPENAI_API_KEY`.
- Surface a clear HTTP or UI error instead of a generic 500.

### Environment Deliverables

- the project’s example env file documents required variables
- the project’s setup docs describe environment setup and run commands
- real secrets stay out of version control

### Minimal Python Pattern

```python
class Settings(BaseSettings):
    openai_api_key: str | None = None


def require_openai_api_key(settings: Settings) -> str:
    key = (settings.openai_api_key or "").strip()
    if not key:
        raise ValueError("OPENAI_API_KEY is not configured.")
    return key
```

### Model Defaults

- Responses and Agents: `gpt-5.2` with low reasoning effort
- Realtime: `gpt-realtime`
- Keep one override point through env vars or one config module.
- Do not hardcode model strings in call sites.

Recommended env override names:

- `OPENAI_MODEL`
- `OPENAI_REASONING_EFFORT`
- `OPENAI_REALTIME_MODEL`

### Default And Override Tests

- defaults resolve to documented values with no env override
- env or config override works end-to-end
- tests do not rely on ambient env files

## Pricing Guidance

- Prices are USD per 1M tokens.
- Treat reasoning tokens as output cost.
- Assume no caching unless the implementation explicitly uses cached input.
- Output cost is often materially higher than input cost.

### Usage Notes

- Use a current authoritative pricing source rather than hardcoded historical numbers.
- Consider cheaper models for high-volume or low-risk demo paths.
- Treat realtime, audio, and image pricing separately from standard text pricing when those modes are in use.
