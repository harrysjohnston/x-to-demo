# Generated Output Badge – Implementation Reference

## Reusable Component (React)

```tsx
function GeneratedBadge({ showLabel = false }: { showLabel?: boolean }) {
  return (
    <span
      data-testid="generated-badge"
      role="img"
      aria-label="Generated content"
      className="generated-badge"
    >
      <span aria-hidden>✨</span>
      {showLabel && <span className="label">Generated</span>}
    </span>
  );
}
```

## Usage in Chat Message

```tsx
function AssistantMessage({ content }: { content: string }) {
  return (
    <div className="message assistant" data-testid="generated-output">
      <GeneratedBadge showLabel />
      <p>{content}</p>
    </div>
  );
}
```

## Usage in Compact Layout

```tsx
function GeneratedSummary({ text }: { text: string }) {
  return (
    <div data-testid="generated-output">
      <GeneratedBadge />
      <span>{text}</span>
    </div>
  );
}
```

## Usage in Code Block

```tsx
function GeneratedCodeBlock({ code }: { code: string }) {
  return (
    <div data-testid="generated-output">
      <div className="header">
        <GeneratedBadge showLabel />
      </div>
      <pre><code>{code}</code></pre>
    </div>
  );
}
```

## UI Tests

**Single surface:**

```tsx
it("generated output includes badge", () => {
  render(<AssistantMessage content="Hello" />);
  expect(screen.getByTestId("generated-badge")).toBeInTheDocument();
});
```

**All generated surfaces:**

```tsx
const GENERATED_COMPONENTS = [
  { name: "AssistantMessage", Component: () => <AssistantMessage content="Hi" /> },
  { name: "GeneratedSummary", Component: () => <GeneratedSummary text="Summary" /> },
  { name: "GeneratedCodeBlock", Component: () => <GeneratedCodeBlock code="x" /> },
];

it.each(GENERATED_COMPONENTS)("$name includes generated badge", ({ Component }) => {
  render(<Component />);
  expect(screen.getByTestId("generated-badge")).toBeInTheDocument();
});
```

**Query by data-testid on generated output:**

```tsx
it("all generated outputs include badge", () => {
  render(
    <>
      <AssistantMessage content="A" />
      <GeneratedSummary text="B" />
    </>
  );
  const outputs = screen.getAllByTestId("generated-output");
  outputs.forEach((el) => {
    expect(el.querySelector("[data-testid='generated-badge']")).toBeInTheDocument();
  });
});
```
