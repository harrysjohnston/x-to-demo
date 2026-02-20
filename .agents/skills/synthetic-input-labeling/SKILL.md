---
name: synthetic-input-labeling
description: Prevents confusion between seeded synthetic data and real user inputs. Use when building or modifying demos that use seeded/synthetic inputs, prefilled fields, or synthetic datasets. Ensures visible labels and reset controls.
---

# Synthetic Inputs Must Be Clearly Labeled

Prevents users from mistaking seeded synthetic data for real input. Apply when the demo uses prefilled fields, seeded datasets, or synthetic assets.

## When to Apply

- Demo uses seeded/synthetic inputs or assets
- Input fields are prefilled with example data
- Datasets or content are programmatically seeded for demo purposes

## Required Outputs

1. **Visible labeling**:
   - **Seeded input fields**: Prefill badge (e.g., "Example", "Demo data", "Synthetic") near or on the field
   - **Seeded datasets**: Banner or tag (e.g., "Sample dataset", "Synthetic data") on the dataset or list

2. **Reset/reseed control**: Button or link to restore the initial synthetic state (clear user edits, reload seeded data)

## Implementation Checklist

- [ ] Every seeded input field shows a prefill badge or label
- [ ] Every seeded dataset shows a banner or tag
- [ ] Reset/reseed control is visible and restores the original synthetic state
- [ ] Labels use consistent terminology (pick one: "Example", "Demo", "Synthetic", "Sample")

## Label Placement

| Context | Label type | Placement |
|---------|------------|-----------|
| Single input (text, textarea) | Badge or inline label | Adjacent to field, above/below, or inside placeholder with "(example)" |
| Form with multiple prefilled fields | Section banner | Above the form: "Prefilled with example data" |
| Dataset / list / table | Banner or tag | Above the list or on each row/card |
| File upload with seeded file | Badge | Near the file name or upload area |

## Reset Control

- **Label**: "Reset", "Restore example", "Reload sample", or "Clear and reseed"
- **Behavior**: Restores the exact initial seeded state (not just clear-all)
- **Placement**: Near the labeled content or in a toolbar

## Terminology

Choose one and use consistently:
- "Example" / "Example data"
- "Demo" / "Demo data"
- "Synthetic" / "Synthetic data"
- "Sample" / "Sample data"

## Tests (Required)

| Test | Purpose |
|------|---------|
| **Synthetic label is rendered when seeded data is present** | Assert that when the UI shows seeded/prefilled content, a label (badge, banner, or tag) with the chosen terminology is visible in the DOM |
| **Reset restores seeded state** | Assert that after user edits, clicking reset restores the initial seeded values (compare before-edit and after-reset) |

## Additional Resources

- For implementation examples and test patterns, see [reference.md](reference.md)
