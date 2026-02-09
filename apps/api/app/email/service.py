"""Email rendering and sending helpers (dev sink)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from pydantic import BaseModel, ValidationError

from app.config import settings

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


class EmailTemplate(StrEnum):
    """Supported email templates."""

    WELCOME = "welcome"
    PASSWORD_RESET = "password_reset"


class WelcomeEmailContext(BaseModel):
    app_name: str
    user_name: str
    login_url: str


class PasswordResetEmailContext(BaseModel):
    app_name: str
    reset_url: str
    support_email: str
    user_name: str | None = None


@dataclass(frozen=True)
class EmailRenderResult:
    template: EmailTemplate
    subject: str
    html: str
    context: dict[str, Any]


class EmailSendError(RuntimeError):
    """Raised when email rendering or delivery fails."""


_TEMPLATE_FILES = {
    EmailTemplate.WELCOME: "welcome.mjml.j2",
    EmailTemplate.PASSWORD_RESET: "password_reset.mjml.j2",
}

_SUBJECT_TEMPLATES = {
    EmailTemplate.WELCOME: "Welcome to {{ app_name }}",
    EmailTemplate.PASSWORD_RESET: "Reset your {{ app_name }} password",
}

_CONTEXT_MODELS: dict[EmailTemplate, type[BaseModel]] = {
    EmailTemplate.WELCOME: WelcomeEmailContext,
    EmailTemplate.PASSWORD_RESET: PasswordResetEmailContext,
}


def _get_environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml", "mjml"]),
        undefined=StrictUndefined,
    )


_ENV = _get_environment()


def validate_context(template: EmailTemplate, context: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize the template context."""
    model = _CONTEXT_MODELS[template]
    return model.model_validate(context).model_dump()


def render_mjml(mjml_source: str) -> str:
    """Render MJML markup into HTML."""
    try:
        from mjml import mjml2html
    except Exception as exc:  # pragma: no cover - runtime dependency
        raise EmailSendError("MJML rendering dependency is unavailable") from exc

    result = mjml2html.mjml_to_html(mjml_source)
    if hasattr(result, "html"):
        errors = getattr(result, "errors", []) or []
        html = result.html
    elif isinstance(result, dict):
        errors = result.get("errors") or []
        html = result.get("html")
    else:
        errors = []
        html = result

    if errors:
        raise EmailSendError(f"MJML rendering failed: {errors}")
    if not html:
        raise EmailSendError("MJML rendering returned empty HTML")
    return html


def render_email(template: EmailTemplate, context: dict[str, Any]) -> EmailRenderResult:
    """Render MJML template and return subject + HTML."""
    normalized = validate_context(template, context)

    mjml_template = _ENV.get_template(_TEMPLATE_FILES[template])
    mjml_body = mjml_template.render(**normalized)

    subject = _ENV.from_string(_SUBJECT_TEMPLATES[template]).render(**normalized).strip()
    html = render_mjml(mjml_body)

    return EmailRenderResult(template=template, subject=subject, html=html, context=normalized)


def send_email(
    *,
    template: EmailTemplate,
    to_email: str,
    context: dict[str, Any],
    to_name: str | None = None,
) -> None:
    """Send an email using the development log sink."""
    if not settings.email_enabled:
        logger.info("Email sending disabled; skipping delivery.")
        return

    try:
        rendered = render_email(template, context)
    except (ValidationError, EmailSendError) as exc:
        raise EmailSendError("Failed to render email") from exc

    payload: dict[str, Any] = {
        "template": rendered.template,
        "to": to_email,
        "to_name": to_name,
        "from": settings.email_from_address,
        "from_name": settings.email_from_name,
        "subject": rendered.subject,
    }
    if settings.email_log_payload:
        payload["html"] = rendered.html
        payload["context"] = rendered.context

    logger.info("Email send (dev sink)", extra={"email": payload})
