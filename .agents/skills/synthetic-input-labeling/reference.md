# Synthetic Input Labeling – Implementation Reference

## Input Field with Prefill Badge (React)

```tsx
function SeededInput({ value, label, syntheticLabel = "Example" }) {
  return (
    <div className="relative">
      <label>{label}</label>
      <span className="badge" aria-label="Prefilled with example data">
        {syntheticLabel}
      </span>
      <textarea value={value} readOnly aria-describedby="synthetic-badge" />
    </div>
  );
}
```

## Form Section Banner

```tsx
function SeededForm({ children, onReset }) {
  return (
    <section>
      <div role="status" className="banner">
        Prefilled with example data
        <button onClick={onReset}>Reset</button>
      </div>
      {children}
    </section>
  );
}
```

## Dataset Tag

```tsx
function DatasetList({ items, isSeeded }) {
  return (
    <div>
      {isSeeded && (
        <span className="tag" data-testid="synthetic-label">
          Sample dataset
        </span>
      )}
      <ul>{items.map((item) => <li key={item.id}>{item.name}</li>)}</ul>
    </div>
  );
}
```

## Reset Logic

```tsx
const INITIAL_SEEDED_STATE = { input: "Example text...", items: [...] };

function useSeededState(initial = INITIAL_SEEDED_STATE) {
  const [state, setState] = useState(initial);
  const reset = () => setState(initial);
  return [state, setState, reset];
}
```

## UI Tests (React Testing Library)

**Synthetic label is rendered when seeded data is present:**

```tsx
it("renders synthetic label when seeded data is present", () => {
  render(<SeededForm initialData={SEEDED_DATA} />);
  expect(screen.getByText(/example|demo|synthetic|sample/i)).toBeInTheDocument();
  expect(screen.getByRole("status") || screen.getByTestId("synthetic-label")).toBeInTheDocument();
});
```

```tsx
it("shows prefill badge when input is seeded", () => {
  render(<SeededInput value="Prefilled example..." syntheticLabel="Example" />);
  expect(screen.getByText("Example")).toBeInTheDocument();
});
```

**Reset restores seeded state:**

```tsx
it("reset restores seeded state", async () => {
  const INITIAL = { input: "Original seed" };
  render(<SeededForm initialData={INITIAL} />);
  const input = screen.getByRole("textbox");

  await userEvent.clear(input);
  await userEvent.type(input, "User edited");
  expect(input).toHaveValue("User edited");

  await userEvent.click(screen.getByRole("button", { name: /reset|restore/i }));
  expect(input).toHaveValue(INITIAL.input);
});
```
