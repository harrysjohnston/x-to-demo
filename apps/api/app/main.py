import logging

import colorlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.exceptions import setup_exception_handlers
from app.routers import x_to_demo

_LOG_STANDARD = {
    "name",
    "msg",
    "args",
    "asctime",
    "created",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "exc_info",
    "exc_text",
    "message",
    "thread",
    "threadName",
    "taskName",
}


class _ColoredExtraFormatter(colorlog.ColoredFormatter):
    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        extras = {k: v for k, v in record.__dict__.items() if k not in _LOG_STANDARD}
        if not extras:
            return base
        parts = [f"{k}={v}" for k, v in sorted(extras.items())]
        return f"{base} {', '.join(parts)}"


_log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
_log_format = "%(log_color)s%(asctime)s %(levelname)-8s%(reset)s %(name)s: %(message)s"
_formatter = _ColoredExtraFormatter(_log_format, log_colors=colorlog.default_log_colors)
logging.basicConfig(level=_log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
root = logging.getLogger()
root.setLevel(_log_level)
for h in root.handlers:
    h.setFormatter(_formatter)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    openapi_url=settings.openapi_url,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
)

# Add CORS middleware (must be added before exception handlers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup exception handlers for standardized error responses
setup_exception_handlers(app)

# Include routers with API version prefix
app.include_router(x_to_demo.router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
