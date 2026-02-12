"""Progress-event publication helpers for X-to-Demo pipeline runs."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from app.schemas import SSEEvent

if TYPE_CHECKING:
    import logging
    from collections.abc import Callable


def publish_progress_event(
    *,
    user_id: int,
    payload: dict[str, Any],
    logger: logging.Logger,
    publish_call: Callable[..., asyncio.Future[int] | Any],
    on_done: Callable[[asyncio.Task[int]], None],
) -> None:
    """Publish an SSE progress event from sync and async contexts."""
    event = SSEEvent(event="x_to_demo_run_progress", data=payload)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        try:
            asyncio.run(publish_call(event, user_id=user_id))
        except Exception:
            logger.warning(
                "Failed to publish X-to-Demo progress event",
                extra={"event_name": event.event, "run_id": payload.get("run_id")},
                exc_info=True,
            )
        return

    try:
        publish_task = loop.create_task(publish_call(event, user_id=user_id))
        publish_task.add_done_callback(on_done)
    except Exception:
        logger.warning(
            "Failed to schedule X-to-Demo progress event",
            extra={"event_name": event.event, "run_id": payload.get("run_id")},
            exc_info=True,
        )
