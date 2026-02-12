"""Model pricing and token-cost aggregation helpers."""

from __future__ import annotations

from pathlib import Path

PRICING_PATH = Path(__file__).resolve().parents[3] / "openai_model_pricing.md"
_PRICING_CACHE: dict[str, dict[str, float | None]] | None = None


def parse_price(value: str) -> float | None:
    """Parse a markdown table price value like `$0.123` into a float."""
    stripped = value.strip()
    if not stripped or stripped == "-":
        return None
    if stripped.startswith("$"):
        stripped = stripped[1:]
    try:
        return float(stripped)
    except ValueError:
        return None


def normalize_model_for_pricing(model_name: str, pricing_keys: list[str]) -> str | None:
    """Resolve a model variant name to the best matching pricing table key."""
    model_lower = model_name.lower()
    key_map = {key.lower(): key for key in pricing_keys}
    if model_lower in key_map:
        return key_map[model_lower]

    best: str | None = None
    for key in pricing_keys:
        lowered = key.lower()
        if not model_lower.startswith(lowered):
            continue
        if len(model_lower) > len(lowered):
            next_char = model_lower[len(lowered)]
            if next_char not in ("-", ":", "@"):
                continue
        if best is None or len(key) > len(best):
            best = key
    return best


def load_pricing_table(path: Path = PRICING_PATH) -> dict[str, dict[str, float | None]]:
    """Load and cache model pricing from the local markdown pricing table."""
    global _PRICING_CACHE
    if _PRICING_CACHE is not None:
        return _PRICING_CACHE

    pricing: dict[str, dict[str, float | None]] = {}
    if not path.exists():
        _PRICING_CACHE = pricing
        return pricing

    lines = path.read_text(encoding="utf-8").splitlines()
    header_index: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == "|Model|Input|Cached input|Output|":
            header_index = index
            break
    if header_index is None:
        _PRICING_CACHE = pricing
        return pricing

    for line in lines[header_index + 2 :]:
        if not line.strip().startswith("|"):
            break
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) != 4:
            continue
        model, input_price, cached_price, output_price = parts
        pricing[model] = {
            "input": parse_price(input_price),
            "cached_input": parse_price(cached_price),
            "output": parse_price(output_price),
        }

    _PRICING_CACHE = pricing
    return pricing


def estimate_cost(*, model_name: str, usage: dict[str, int]) -> dict[str, float] | None:
    """Estimate API cost from usage metrics and local pricing rates."""
    pricing = load_pricing_table()
    pricing_key = normalize_model_for_pricing(model_name, list(pricing.keys()))
    if not pricing_key:
        return None

    rates = pricing.get(pricing_key)
    if not rates:
        return None

    input_rate = rates.get("input")
    output_rate = rates.get("output")
    cached_rate = rates.get("cached_input") or input_rate
    if input_rate is None or output_rate is None or cached_rate is None:
        return None

    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    cached_tokens = int(usage.get("cached_input_tokens", 0) or 0)
    uncached_tokens = max(input_tokens - cached_tokens, 0)

    input_cost = (uncached_tokens / 1_000_000) * input_rate
    cached_cost = (cached_tokens / 1_000_000) * cached_rate
    output_cost = (output_tokens / 1_000_000) * output_rate
    total_cost = input_cost + cached_cost + output_cost
    return {
        "input_cost": input_cost,
        "cached_input_cost": cached_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
    }


def merge_usage(usages: list[dict[str, int] | object]) -> dict[str, int]:
    """Sum token usage metrics across phase calls."""
    merged: dict[str, int] = {}
    for usage in usages:
        if not isinstance(usage, dict):
            continue
        for key, value in usage.items():
            merged[key] = merged.get(key, 0) + int(value)
    return merged


def merge_costs(costs: list[dict[str, float] | None]) -> dict[str, float] | None:
    """Sum cost metrics across phase calls."""
    merged: dict[str, float] = {}
    any_cost = False
    for cost in costs:
        if cost is None:
            continue
        any_cost = True
        for key, value in cost.items():
            merged[key] = merged.get(key, 0.0) + float(value)
    return merged if any_cost else None
