"""In-memory pub/sub manager for SSE event broadcasting."""

from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from app.schemas import SSEEvent

logger = logging.getLogger(__name__)


@dataclass
class Subscriber:
    """Represents a connected SSE client."""

    client_id: str
    user_id: int | None
    queue: asyncio.Queue[SSEEvent]
    loop: asyncio.AbstractEventLoop | None


@dataclass
class PubSubManager:
    """Simple in-memory pub/sub manager for SSE broadcasting.

    Features:
    - Broadcast to all subscribers
    - Target specific users by user_id
    - Bounded queue per client (drops oldest if full)
    - Thread-safe subscriber management
    """

    max_queue_size: int = 100
    _subscribers: dict[str, Subscriber] = field(default_factory=dict)
    _lock: threading.RLock = field(default_factory=threading.RLock)

    def subscribe(self, user_id: int | None = None) -> tuple[str, asyncio.Queue[SSEEvent]]:
        """Subscribe a new client and return (client_id, queue).

        Args:
            user_id: Optional user ID for targeted messages.

        Returns:
            Tuple of (client_id, queue) for receiving events.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        client_id = uuid4().hex
        queue: asyncio.Queue[SSEEvent] = asyncio.Queue(maxsize=self.max_queue_size)
        subscriber = Subscriber(client_id=client_id, user_id=user_id, queue=queue, loop=loop)
        with self._lock:
            self._subscribers[client_id] = subscriber
        logger.debug("Client %s subscribed (user_id=%s)", client_id, user_id)
        return client_id, queue

    def unsubscribe(self, client_id: str) -> None:
        """Remove a client subscription.

        Args:
            client_id: The client ID to unsubscribe.
        """
        removed = False
        with self._lock:
            if client_id in self._subscribers:
                del self._subscribers[client_id]
                removed = True
        if removed:
            logger.debug("Client %s unsubscribed", client_id)

    async def publish(self, event: SSEEvent, user_id: int | None = None) -> int:
        """Publish an event to subscribers.

        Args:
            event: The SSE event to publish.
            user_id: If provided, only send to subscribers with this user_id.
                    If None, broadcast to all subscribers.

        Returns:
            Number of subscribers that received the event.
        """
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        with self._lock:
            subscribers = list(self._subscribers.values())

        delivered = 0
        for subscriber in subscribers:
            # Filter by user_id if specified
            if user_id is not None and subscriber.user_id != user_id:
                continue

            if subscriber.loop and subscriber.loop is not current_loop:
                if subscriber.loop.is_closed():
                    logger.debug("Skipping publish for closed loop client %s", subscriber.client_id)
                    continue
                if subscriber.queue.full():
                    logger.warning("Queue full for client %s, dropping event", subscriber.client_id)
                    continue
                subscriber.loop.call_soon_threadsafe(
                    self._put_event_nowait,
                    subscriber,
                    event,
                )
                delivered += 1
                continue

            if self._put_event_nowait(subscriber, event):
                delivered += 1

        logger.debug("Published event to %d subscribers", delivered)
        return delivered

    @staticmethod
    def _put_event_nowait(subscriber: Subscriber, event: SSEEvent) -> bool:
        try:
            # Non-blocking put - drop if queue is full (backpressure)
            subscriber.queue.put_nowait(event)
            return True
        except asyncio.QueueFull:
            logger.warning("Queue full for client %s, dropping event", subscriber.client_id)
            return False

    @property
    def subscriber_count(self) -> int:
        """Return the current number of subscribers."""
        with self._lock:
            return len(self._subscribers)


# Global singleton instance
pubsub = PubSubManager()
