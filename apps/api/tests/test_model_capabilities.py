"""Unit tests for model capability helpers."""

from __future__ import annotations

import pytest

from app.services.model_capabilities import (
    default_reasoning_effort,
    supported_reasoning_efforts,
    supports_reasoning,
    validate_model_name,
    validate_reasoning_effort,
)


def test_supports_reasoning_for_gpt5_and_o_series() -> None:
    assert supports_reasoning(" GPT-5.1 ")
    assert supports_reasoning("o3-mini")
    assert not supports_reasoning("gpt-4.1-nano")


def test_supported_reasoning_efforts_by_family() -> None:
    assert supported_reasoning_efforts("gpt-5.2") == ("none", "low", "medium", "high", "xhigh")
    assert supported_reasoning_efforts("gpt-5-mini") == ("minimal", "low", "medium", "high")
    assert supported_reasoning_efforts("o3-mini") == ("low", "medium", "high")
    assert supported_reasoning_efforts("gpt-4.1-nano") is None


def test_default_reasoning_effort_prefers_low() -> None:
    assert default_reasoning_effort(model_name="gpt-5.2") == "low"
    assert default_reasoning_effort(model_name="unknown-model") == "low"


def test_validate_model_name_normalizes_supported_values() -> None:
    assert validate_model_name(model_name=" GPT-5.2 ") == "gpt-5.2"


def test_validate_model_name_rejects_unsupported_values() -> None:
    with pytest.raises(ValueError, match="Unsupported model"):
        validate_model_name(model_name="gpt-4.1")


def test_validate_reasoning_effort_rejects_invalid_known_values() -> None:
    with pytest.raises(ValueError, match="Unsupported reasoning effort"):
        validate_reasoning_effort(model_name="gpt-5.2", reasoning_effort="minimal")


def test_validate_reasoning_effort_accepts_valid_and_unknown_models() -> None:
    assert validate_reasoning_effort(model_name="gpt-5.2", reasoning_effort="xhigh") == "xhigh"
    assert (
        validate_reasoning_effort(model_name="custom-model", reasoning_effort="whatever")
        == "whatever"
    )
