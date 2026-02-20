---
name: generated-output-badge
description: Makes AI/tool-generated content distinguishable from user or static content. Use when building or modifying any UI surface that renders generated content. Requires a reusable badge/icon and optional label.
---

# Generated Outputs Must Be Visibly Marked

Makes AI/tool-generated content distinguishable from user or static content. Apply when any UI surface renders generated content.

## When to Apply

- UI surface renders AI-generated content (text, images, code, etc.)
- Tool-generated output is displayed
- Chat messages, summaries, suggestions, or other model/tool output

## Required Outputs

1. **Reusable badge/icon component** – sparkle (✨), AI icon, or similar; applied to all generated outputs
2. **Optional "Generated" label** – when space allows (e.g., tooltip, inline label, or caption)

## Implementation Checklist

- [ ] Create a single reusable component (e.g., `GeneratedBadge`, `AIIndicator`)
- [ ] Apply the badge/icon to every surface that shows generated content
- [ ] Use consistent placement (e.g., top-right of block, inline before content)
- [ ] Add "Generated" label where space permits; icon alone is acceptable for tight layouts

## Badge Placement

| Context | Placement | Label |
|---------|-----------|-------|
| Chat message (assistant) | Start of message or avatar area | Optional |
| Inline generated text | Before or after block | "Generated" when space allows |
| Card/panel with generated content | Header or corner | Icon + optional label |
| Code block output | Above or beside block | Icon minimum |

## Icon Options

- Sparkle (✨) – common convention for AI
- Robot/AI icon – explicit
- Wand – generation metaphor

Choose one and use consistently across the demo.

## Accessibility

- Add `aria-label="Generated content"` or `role="img"` with descriptive label
- Ensure sufficient contrast; icon should be visible on all backgrounds

## Tests (Required)

| Test | Purpose |
|------|---------|
| **Generated outputs include badge/icon** | Assert that every UI surface rendering generated content displays the badge or icon. Query by `data-testid`, `aria-label`, or icon/label text. |

Cover all generated surfaces: chat messages, summaries, code blocks, cards, etc. Use a shared test helper or parameterized tests if multiple surfaces exist.

## Additional Resources

- For implementation examples and test patterns, see [reference.md](reference.md)
