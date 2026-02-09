"use client";

/**
 * React hook for Server-Sent Events (SSE) connections.
 *
 * Manages the SSE connection lifecycle with React component mount/unmount,
 * providing connection status and event buffering.
 */

import { useCallback, useEffect, useRef, useState } from "react";

import {
  createSSEConnection,
  type SSEConnection,
  type SSEConnectionStatus,
  type SSEEvent,
} from "@/lib/sse";

/**
 * Options for the useSSE hook.
 */
export interface UseSSEOptions<T = unknown> {
  /** Whether the connection should be active (default: true) */
  enabled?: boolean;
  /** Event types to listen for (default: all) */
  eventTypes?: string[];
  /** Maximum number of events to buffer (default: 50) */
  maxEvents?: number;
  /** Callback when an event is received */
  onEvent?: (event: SSEEvent<T>) => void;
  /** Callback when connection status changes */
  onStatusChange?: (status: SSEConnectionStatus) => void;
}

/**
 * Return value from the useSSE hook.
 */
export interface UseSSEResult<T = unknown> {
  /** Current connection status */
  status: SSEConnectionStatus;
  /** Most recent event received */
  lastEvent: SSEEvent<T> | null;
  /** Buffer of recent events (newest first) */
  events: SSEEvent<T>[];
  /** Manually disconnect the SSE connection */
  disconnect: () => void;
  /** Manually reconnect the SSE connection */
  reconnect: () => void;
  /** Clear the events buffer */
  clearEvents: () => void;
}

/**
 * React hook for managing SSE connections.
 *
 * @example
 * ```tsx
 * function NotificationBell() {
 *   const { status, lastEvent, events } = useSSE<NotificationPayload>({
 *     eventTypes: ['notification'],
 *   });
 *
 *   return (
 *     <div>
 *       <span>Status: {status}</span>
 *       {events.map((e, i) => <Notification key={i} data={e.data} />)}
 *     </div>
 *   );
 * }
 * ```
 *
 * @param options - Hook options
 * @returns SSE connection state and controls
 */
export function useSSE<T = unknown>(options: UseSSEOptions<T> = {}): UseSSEResult<T> {
  const { enabled = true, eventTypes, maxEvents = 50, onEvent, onStatusChange } = options;

  const [status, setStatus] = useState<SSEConnectionStatus>("disconnected");
  const [lastEvent, setLastEvent] = useState<SSEEvent<T> | null>(null);
  const [events, setEvents] = useState<SSEEvent<T>[]>([]);

  const connectionRef = useRef<SSEConnection | null>(null);
  const enabledRef = useRef(enabled);

  // Keep enabled ref in sync
  useEffect(() => {
    enabledRef.current = enabled;
  }, [enabled]);

  const handleEvent = useCallback(
    (event: SSEEvent) => {
      const typedEvent = event as SSEEvent<T>;
      setLastEvent(typedEvent);
      setEvents((prev) => [typedEvent, ...prev].slice(0, maxEvents));
      onEvent?.(typedEvent);
    },
    [maxEvents, onEvent],
  );

  const handleStatusChange = useCallback(
    (newStatus: SSEConnectionStatus) => {
      setStatus(newStatus);
      onStatusChange?.(newStatus);
    },
    [onStatusChange],
  );

  const connect = useCallback(() => {
    if (connectionRef.current) {
      connectionRef.current.disconnect();
    }

    connectionRef.current = createSSEConnection({
      onMessage: handleEvent,
      onStatusChange: handleStatusChange,
      eventTypes,
    });
  }, [handleEvent, handleStatusChange, eventTypes]);

  const disconnect = useCallback(() => {
    if (connectionRef.current) {
      connectionRef.current.disconnect();
      connectionRef.current = null;
    }
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    if (enabledRef.current) {
      connect();
    }
  }, [connect, disconnect]);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setLastEvent(null);
  }, []);

  // Connect/disconnect based on enabled state
  useEffect(() => {
    if (enabled) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return {
    status,
    lastEvent,
    events,
    disconnect,
    reconnect,
    clearEvents,
  };
}

export default useSSE;
