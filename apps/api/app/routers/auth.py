"""Authentication endpoints (register/login/refresh/logout)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    require_active_refresh_token,
    verify_password,
)
from app.config import settings
from app.database import get_session
from app.email import EmailSendError, EmailTemplate, send_email
from app.models import RefreshToken, User, UserCreate, UserRead
from app.schemas import ResponseEnvelope

# Cookie configuration
SSE_COOKIE_NAME = "sse_token"
SSE_COOKIE_MAX_AGE = settings.jwt_access_token_expire_minutes * 60

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    token_type: str = "bearer"
    access_token: str
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post(
    "/register", response_model=ResponseEnvelope[UserRead], status_code=status.HTTP_201_CREATED
)
def register(
    payload: UserCreate, session: Session = Depends(get_session)
) -> ResponseEnvelope[User]:
    existing_user = session.exec(select(User).where(User.email == payload.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user = User(
        email=payload.email,
        name=payload.name,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    try:
        send_email(
            template=EmailTemplate.WELCOME,
            to_email=user.email,
            to_name=user.name,
            context={
                "app_name": settings.app_name,
                "user_name": user.name,
                "login_url": f"{settings.email_web_base_url}/login",
            },
        )
    except EmailSendError as exc:
        logger.warning("Welcome email failed to send.", exc_info=exc)

    return ResponseEnvelope(data=user)


@router.post("/login", response_model=ResponseEnvelope[TokenResponse])
def login(
    payload: LoginRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> ResponseEnvelope[TokenResponse]:
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not user.is_active or not user.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token, _access_exp = create_access_token(user_id=user.id)  # type: ignore[arg-type]
    refresh_token, jti, refresh_exp = create_refresh_token(user_id=user.id)  # type: ignore[arg-type]

    session.add(RefreshToken(jti=jti, user_id=user.id, expires_at=refresh_exp))  # type: ignore[arg-type]
    session.commit()

    # Set HTTP-only cookie for SSE authentication
    response.set_cookie(
        key=SSE_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=settings.is_production,  # HTTPS only in production
        samesite="lax",
        max_age=SSE_COOKIE_MAX_AGE,
    )

    return ResponseEnvelope(
        data=TokenResponse(access_token=access_token, refresh_token=refresh_token)
    )


@router.post("/refresh", response_model=ResponseEnvelope[TokenResponse])
def refresh(
    payload: RefreshRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> ResponseEnvelope[TokenResponse]:
    token_data, row = require_active_refresh_token(token=payload.refresh_token, session=session)

    # Revoke old refresh token (rotation).
    row.revoked_at = datetime.now(UTC).replace(tzinfo=None)
    session.add(row)

    access_token, _access_exp = create_access_token(user_id=token_data.user_id)
    refresh_token, new_jti, refresh_exp = create_refresh_token(user_id=token_data.user_id)

    session.add(RefreshToken(jti=new_jti, user_id=token_data.user_id, expires_at=refresh_exp))
    session.commit()

    # Update HTTP-only cookie for SSE authentication
    response.set_cookie(
        key=SSE_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=SSE_COOKIE_MAX_AGE,
    )

    return ResponseEnvelope(
        data=TokenResponse(access_token=access_token, refresh_token=refresh_token)
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> None:
    _token_data, row = require_active_refresh_token(token=payload.refresh_token, session=session)

    row.revoked_at = datetime.now(UTC).replace(tzinfo=None)
    session.add(row)
    session.commit()

    # Clear SSE cookie
    response.delete_cookie(key=SSE_COOKIE_NAME)
