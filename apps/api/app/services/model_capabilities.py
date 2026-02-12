"""Model capability helpers for X-to-Demo pipeline execution."""

from __future__ import annotations

SUPPORTED_X_TO_DEMO_MODELS: tuple[str, ...] = (
    "gpt-5.2",
    "gpt-5.1",
    "gpt-5-mini",
    "gpt-5-nano",
    "gpt-4.1-nano",
)

_GPT5_REASONING_EFFORTS: tuple[str, ...] = ("minimal", "low", "medium", "high")
_GPT52_REASONING_EFFORTS: tuple[str, ...] = ("none", "low", "medium", "high", "xhigh")
_O_SERIES_REASONING_EFFORTS: tuple[str, ...] = ("low", "medium", "high")


def supports_reasoning(model_name: str) -> bool:
    """Return whether the model accepts reasoning-level controls."""
    normalized_name = model_name.strip().lower()
    if normalized_name.startswith("gpt-5"):
        return True
    return len(normalized_name) >= 2 and normalized_name[0] == "o" and normalized_name[1].isdigit()


def supported_reasoning_efforts(model_name: str) -> tuple[str, ...] | None:
    """Return model-specific supported reasoning efforts when known."""
    normalized_name = model_name.strip().lower()
    if normalized_name.startswith("gpt-5.2"):
        return _GPT52_REASONING_EFFORTS
    if normalized_name.startswith("gpt-5"):
        return _GPT5_REASONING_EFFORTS
    if len(normalized_name) >= 2 and normalized_name[0] == "o" and normalized_name[1].isdigit():
        return _O_SERIES_REASONING_EFFORTS
    return None


def default_reasoning_effort(*, model_name: str) -> str:
    """Resolve a default reasoning effort for a model."""
    supported = supported_reasoning_efforts(model_name)
    if supported and "low" in supported:
        return "low"
    if supported:
        return supported[0]
    return "low"


def validate_model_name(*, model_name: str) -> str:
    """Normalize and validate the selected X-to-Demo model."""
    normalized_name = str(model_name).strip().lower()
    if not normalized_name:
        raise ValueError("model must be a non-empty string")

    if normalized_name not in SUPPORTED_X_TO_DEMO_MODELS:
        supported = ", ".join(f"'{value}'" for value in SUPPORTED_X_TO_DEMO_MODELS)
        raise ValueError(f"Unsupported model {normalized_name!r}. Supported values: {supported}.")
    return normalized_name


def validate_reasoning_effort(*, model_name: str, reasoning_effort: str) -> str:
    """Normalize and validate reasoning effort against known model constraints."""
    normalized_effort = str(reasoning_effort).strip().lower()
    if not normalized_effort:
        raise ValueError("reasoning effort must be a non-empty string")

    allowed = supported_reasoning_efforts(model_name)
    if allowed and normalized_effort not in allowed:
        allowed_text = ", ".join(f"'{value}'" for value in allowed)
        raise ValueError(
            f"Unsupported reasoning effort {normalized_effort!r} for model {model_name!r}. "
            f"Supported values: {allowed_text}."
        )
    return normalized_effort
