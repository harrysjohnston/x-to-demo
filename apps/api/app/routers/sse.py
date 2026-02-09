"""Server-Sent Events (SSE) endpoints for realtime streaming."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Cookie, Depends
from fastapi.responses import StreamingResponse
from jose import JWTError

from app.auth import decode_token
from app.database import get_session
from app.models import User
from app.pubsub import pubsub
from app.schemas import SSEEvent

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlmodel import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sse", tags=["sse"])

# SSE configuration
HEARTBEAT_INTERVAL_SECONDS = 15


def get_user_from_cookie(sse_token: str | None, session: Session) -> User | None:
    """Validate SSE token from cookie and return user if valid.

    Args:
        sse_token: JWT token from cookie (may be None for unauthenticated access).
        session: Database session.

    Returns:
        User if token is valid, None otherwise.
    """
    if not sse_token:
        return None

    try:
        token_data = decode_token(sse_token)
        if token_data.token_type != "access":
            return None

        user = session.get(User, token_data.user_id)
        if not user or not user.is_active:
            return None

        return user
    except JWTError:
        return None


def format_sse_event(event: SSEEvent) -> str:
    """Format an SSEEvent as SSE wire format.

    Args:
        event: The event to format.

    Returns:
        SSE-formatted string ready to send over the wire.
    """
    lines = []
    if event.id:
        lines.append(f"id: {event.id}")
    lines.append(f"event: {event.event}")
    # Data must be JSON-encoded and can span multiple lines
    lines.append(f"data: {event.data}")
    lines.append("")  # Empty line to end the event
    return "\n".join(lines) + "\n"


async def event_generator(
    user: User | None,
) -> AsyncGenerator[str, None]:
    """Generate SSE events for a connected client.

    Args:
        user: The authenticated user (or None for anonymous).

    Yields:
        SSE-formatted event strings.
    """
    user_id = user.id if user else None
    client_id, queue = pubsub.subscribe(user_id=user_id)

    try:
        # Send initial connection event
        connect_event = SSEEvent(
            event="connected",
            data={"client_id": client_id, "authenticated": user is not None},
        )
        yield format_sse_event(connect_event)

        while True:
            try:
                # Wait for event with timeout for heartbeat
                event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_INTERVAL_SECONDS)
                yield format_sse_event(event)
            except TimeoutError:
                # Send heartbeat comment to keep connection alive
                yield ": heartbeat\n\n"
            except asyncio.CancelledError:
                # Client disconnected
                break
    finally:
        pubsub.unsubscribe(client_id)
        logger.debug("Client %s disconnected", client_id)


@router.get("/events")
async def event_stream(
    sse_token: str | None = Cookie(default=None),
    session: Session = Depends(get_session),
) -> StreamingResponse:
    """SSE endpoint for realtime event streaming.

    Authentication is optional via HTTP-only cookie. Authenticated users
    can receive targeted events; unauthenticated users receive only
    broadcast events.

    Returns:
        StreamingResponse with text/event-stream content type.
    """
    user = get_user_from_cookie(sse_token, session)

    return StreamingResponse(
        event_generator(user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/status")
async def sse_status() -> dict[str, int]:
    """Return current SSE connection status.

    Returns:
        Dictionary with subscriber count.
    """
    return {"subscribers": pubsub.subscriber_count}
