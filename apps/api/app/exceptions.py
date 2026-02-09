"""Exception handlers for standardized error responses."""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.schemas import ErrorDetail, ErrorResponse


def setup_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for standardized error responses."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTPException with standardized error format."""
        # Extract error code from status code
        status_code_map = {
            400: "bad_request",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            409: "conflict",
            422: "validation_error",
            500: "internal_server_error",
        }
        code = status_code_map.get(exc.status_code, "error")

        error_detail = ErrorDetail(
            code=code,
            message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error=error_detail).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors from request parsing."""
        errors = exc.errors()
        if errors:
            # Use first error for simplicity (could be enhanced to return all errors)
            first_error = errors[0]
            field = ".".join(str(loc) for loc in first_error.get("loc", []))
            error_detail = ErrorDetail(
                code="validation_error",
                message=first_error.get("msg", "Validation error"),
                field=field if field != "body" else None,
            )
        else:
            error_detail = ErrorDetail(code="validation_error", message="Invalid request data")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(error=error_detail).model_dump(),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        _request: Request, exc: ValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        errors = exc.errors()
        if errors:
            first_error = errors[0]
            field = ".".join(str(loc) for loc in first_error.get("loc", []))
            error_detail = ErrorDetail(
                code="validation_error",
                message=first_error.get("msg", "Validation error"),
                field=field if field != "body" else None,
            )
        else:
            error_detail = ErrorDetail(code="validation_error", message="Invalid data")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(error=error_detail).model_dump(),
        )
