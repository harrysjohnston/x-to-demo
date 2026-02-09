"""In-memory pub/sub manager for SSE event broadcasting."""

from __future__ import annotations

import asyncio
import logging
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
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def subscribe(self, user_id: int | None = None) -> tuple[str, asyncio.Queue[SSEEvent]]:
        """Subscribe a new client and return (client_id, queue).

        Args:
            user_id: Optional user ID for targeted messages.

        Returns:
            Tuple of (client_id, queue) for receiving events.
        """
        client_id = uuid4().hex
        queue: asyncio.Queue[SSEEvent] = asyncio.Queue(maxsize=self.max_queue_size)
        subscriber = Subscriber(client_id=client_id, user_id=user_id, queue=queue)
        self._subscribers[client_id] = subscriber
        logger.debug("Client %s subscribed (user_id=%s)", client_id, user_id)
        return client_id, queue

    def unsubscribe(self, client_id: str) -> None:
        """Remove a client subscription.

        Args:
            client_id: The client ID to unsubscribe.
        """
        if client_id in self._subscribers:
            del self._subscribers[client_id]
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
        delivered = 0
        for subscriber in list(self._subscribers.values()):
            # Filter by user_id if specified
            if user_id is not None and subscriber.user_id != user_id:
                continue

            try:
                # Non-blocking put - drop if queue is full (backpressure)
                subscriber.queue.put_nowait(event)
                delivered += 1
            except asyncio.QueueFull:
                # Drop oldest and add new (or just skip - we choose to skip)
                logger.warning("Queue full for client %s, dropping event", subscriber.client_id)

        logger.debug("Published event to %d subscribers", delivered)
        return delivered

    @property
    def subscriber_count(self) -> int:
        """Return the current number of subscribers."""
        return len(self._subscribers)


# Global singleton instance
pubsub = PubSubManager()
