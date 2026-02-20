---
name: in-flight-loading-ui
description: Ensures demos never show a stuck UI while waiting on API responses. Use when building or modifying any action that triggers async requests (OpenAI, tools, backend). Covers loading states, control disable rules, streaming indicators, and timeout/error handling.
---

# Clear In-Flight UI While Awaiting API Responses

Ensures the demo never looks stuck during network/model/tool calls. Apply when any action triggers an async request.

## When to Apply

- Action triggers async request (OpenAI, tools, backend API)
- User submits form, clicks button, or initiates operation that waits on network
- Streaming or incremental responses from API

## Required Outputs

1. **Animated loading UI** – spinner, skeleton, or progress indicator + "working" copy
2. **Control disable/enable rules** – during in-flight requests
3. **Streaming indicator** – for incremental responses
4. **Clear timeout and error states** – user sees when something went wrong

## Implementation Checklist

- [ ] Show loading animation immediately when request starts (no delay)
- [ ] Display "working" copy (e.g., "Thinking…", "Processing…", "Generating…")
- [ ] Disable conflicting controls while in-flight; re-enable on success/failure
- [ ] For streaming: show incremental indicator (e.g., typing dots, partial content)
- [ ] Handle timeout: show message and retry option
- [ ] Handle error: show clear message and recovery option

## Loading UI Options

| Type | Use | Example |
|------|-----|---------|
| Spinner | Short operations | Circular spinner + "Processing…" |
| Skeleton | Content replacement | Placeholder blocks where content will appear |
| Progress | Long operations | Bar or indeterminate progress |
| Streaming | Incremental output | Typing indicator, partial text with cursor |

## Control Rules

- **In-flight**: Disable submit/trigger button, other actions that would conflict
- **On success**: Re-enable controls; optionally show success message
- **On failure**: Re-enable controls; show error message and retry
- **On timeout**: Re-enable controls; show timeout message

## Timeout and Error States

- **Timeout**: Clear message, e.g. "Request timed out. Try again." + retry button
- **Error**: Show error message from API or generic "Something went wrong" + retry
- **Network error**: "Connection failed. Check your network and try again."

## Tests (Required)

| Test | Purpose |
|------|---------|
| **Loading animation appears immediately on request start** | Trigger the async action; assert loading UI (spinner/skeleton/progress) and "working" copy are visible within 1 frame or before any mock delay |
| **Loading clears on success/failure** | After request completes (success or error), assert loading UI is hidden and controls are re-enabled |
| **Controls follow disable/enable rules** | Assert submit/trigger button is disabled during request; assert it is enabled after completion |

Use mocked or delayed API responses. Do not rely on real network in tests.

## Additional Resources

- For implementation examples and test patterns, see [reference.md](reference.md)
