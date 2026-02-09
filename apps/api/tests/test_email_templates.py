"""Tests for email template rendering."""

import pytest
from pydantic import ValidationError

from app.email import EmailTemplate, render_email, validate_context


def test_render_welcome_email() -> None:
    result = render_email(
        EmailTemplate.WELCOME,
        {
            "app_name": "ExampleApp",
            "user_name": "Ada",
            "login_url": "https://example.com/login",
        },
    )

    assert "Welcome to ExampleApp" in result.subject
    assert "Ada" in result.html
    assert "https://example.com/login" in result.html


def test_render_password_reset_email() -> None:
    result = render_email(
        EmailTemplate.PASSWORD_RESET,
        {
            "app_name": "ExampleApp",
            "user_name": "Ada",
            "reset_url": "https://example.com/reset",
            "support_email": "support@example.com",
        },
    )

    assert "Reset your ExampleApp password" in result.subject
    assert "https://example.com/reset" in result.html
    assert "support@example.com" in result.html


def test_password_reset_requires_reset_url() -> None:
    with pytest.raises(ValidationError):
        validate_context(
            EmailTemplate.PASSWORD_RESET,
            {
                "app_name": "ExampleApp",
                "support_email": "support@example.com",
            },
        )
