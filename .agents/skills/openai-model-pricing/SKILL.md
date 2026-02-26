---
name: openai-model-pricing
description: Provides OpenAI model pricing per 1M tokens for cost-aware model selection and estimation. Use when selecting models, estimating API costs, or when the user asks about OpenAI pricing, model costs, or token rates.
---

# OpenAI Model Pricing

Provides per-1M-token pricing for cost-aware model selection and estimation. Apply when choosing models or estimating API costs.

## When to Apply

- Selecting OpenAI models for a demo or feature
- Estimating API costs or token usage
- User asks about pricing, model costs, or token rates
- Comparing models for cost/performance trade-offs

## Key Concepts

- **Prices per 1M tokens**: Input, cached input, output
- **Reasoning tokens**: Billed as output tokens; not visible via API but consume context
- **Cached input**: Lower rate for repeated context (where supported)

## Quick Reference (Common Models)

| Model | Input | Cached | Output |
|-------|-------|--------|--------|
| gpt-5.2 | $1.75 | $0.175 | $14.00 |
| gpt-5.1 | $1.25 | $0.125 | $10.00 |
| gpt-5-mini | $0.25 | $0.025 | $2.00 |
| gpt-5-nano | $0.05 | $0.005 | $0.40 |
| gpt-realtime | $4.00 | $0.40 | $16.00 |
| gpt-4.1-nano | $0.10 | $0.025 | $0.40 |

## Full Pricing Table

See [reference.md](reference.md) for the complete table from `apps/api/openai_model_pricing.md`.

## Usage Notes

- Output is typically 5–10× input cost for standard models
- Use `gpt-5-nano` or `gpt-5-mini` for high-volume, low-cost demos
- Use `gpt-5.2` when quality justifies cost
- Realtime/audio models have separate pricing tiers
