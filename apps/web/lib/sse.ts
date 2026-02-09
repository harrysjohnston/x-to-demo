/**
 * Server-Sent Events (SSE) client utilities.
 *
 * Provides an EventSource wrapper with:
 * - Cookie-based authentication (credentials: include)
 * - Exponential backoff reconnection
 * - Typed event parsing
 * - Clean disconnect handling
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const SSE_EVENTS_PATH = "/sse/events";

/**
 * SSE event payload from the server.
 */
export interface SSEEvent<T = Record<string, unknown>> {
  event: string;
  data: T;
  id?: string;
}

/**
 * Connection status for SSE.
 */
export type SSEConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

/**
 * Options for creating an SSE connection.
 */
export interface SSEConnectionOptions {
  /** Called when an event is received */
  onMessage: (event: SSEEvent) => void;
  /** Called when the connection is established */
  onOpen?: () => void;
  /** Called when an error occurs */
  onError?: (error: Event) => void;
  /** Called when connection status changes */
  onStatusChange?: (status: SSEConnectionStatus) => void;
  /** Initial reconnect interval in milliseconds (default: 1000) */
  reconnectInterval?: number;
  /** Maximum reconnect interval in milliseconds (default: 30000) */
  maxReconnectInterval?: number;
  /** Event types to listen for (default: all) */
  eventTypes?: string[];
}

/**
 * SSE connection handle returned by createSSEConnection.
 */
export interface SSEConnection {
  /** Disconnect and stop reconnection attempts */
  disconnect: () => void;
  /** Get current connection status */
  getStatus: () => SSEConnectionStatus;
}

/**
 * Creates an SSE connection to the server.
 *
 * The connection automatically:
 * - Sends cookies (for authentication)
 * - Reconnects with exponential backoff on disconnection
 * - Parses JSON event data
 *
 * @param options - Connection options
 * @returns SSEConnection handle for managing the connection
 */
export function createSSEConnection(options: SSEConnectionOptions): SSEConnection {
  const {
    onMessage,
    onOpen,
    onError,
    onStatusChange,
    reconnectInterval = 1000,
    maxReconnectInterval = 30000,
    eventTypes,
  } = options;

  let eventSource: EventSource | null = null;
  let status: SSEConnectionStatus = "disconnected";
  let currentReconnectInterval = reconnectInterval;
  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  let shouldReconnect = true;

  const setStatus = (newStatus: SSEConnectionStatus) => {
    status = newStatus;
    onStatusChange?.(status);
  };

  const parseEventData = (data: string): unknown => {
    try {
      return JSON.parse(data);
    } catch {
      // If not valid JSON, return as string
      return data;
    }
  };

  const handleMessage = (event: MessageEvent) => {
    const sseEvent: SSEEvent = {
      event: event.type === "message" ? "message" : event.type,
      data: parseEventData(event.data) as Record<string, unknown>,
      id: event.lastEventId || undefined,
    };
    onMessage(sseEvent);
  };

  const connect = () => {
    if (typeof window === "undefined") {
      return; // Don't connect on server side
    }

    setStatus("connecting");

    const url = `${API_BASE_URL}${SSE_EVENTS_PATH}`;

    // EventSource with credentials for cookie auth
    eventSource = new EventSource(url, { withCredentials: true });

    eventSource.onopen = () => {
      setStatus("connected");
      currentReconnectInterval = reconnectInterval; // Reset backoff
      onOpen?.();
    };

    eventSource.onerror = (error) => {
      setStatus("error");
      onError?.(error);

      // Close and attempt reconnection
      eventSource?.close();
      eventSource = null;

      if (shouldReconnect) {
        scheduleReconnect();
      }
    };

    // Listen for specific event types or all messages
    if (eventTypes && eventTypes.length > 0) {
      for (const eventType of eventTypes) {
        eventSource.addEventListener(eventType, handleMessage);
      }
    } else {
      // Listen for all named events we might receive
      eventSource.addEventListener("connected", handleMessage);
      eventSource.addEventListener("message", handleMessage);
      // Also handle the default message event
      eventSource.onmessage = handleMessage;
    }
  };

  const scheduleReconnect = () => {
    if (!shouldReconnect) return;

    setStatus("disconnected");

    reconnectTimeout = setTimeout(() => {
      // Exponential backoff with jitter
      const jitter = Math.random() * 0.3 * currentReconnectInterval;
      currentReconnectInterval = Math.min(
        currentReconnectInterval * 2 + jitter,
        maxReconnectInterval,
      );
      connect();
    }, currentReconnectInterval);
  };

  const disconnect = () => {
    shouldReconnect = false;

    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }

    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }

    setStatus("disconnected");
  };

  const getStatus = () => status;

  // Start connection
  connect();

  return {
    disconnect,
    getStatus,
  };
}

/**
 * Get the SSE events URL (useful for debugging or custom implementations).
 */
export function getSSEEventsUrl(): string {
  return `${API_BASE_URL}${SSE_EVENTS_PATH}`;
}
