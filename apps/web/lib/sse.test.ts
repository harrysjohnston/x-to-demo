import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createSSEConnection, getSSEEventsUrl } from "./sse";

// Mock EventSource
class MockEventSource {
  static instances: MockEventSource[] = [];

  url: string;
  withCredentials: boolean;
  readyState: number = 0;
  onopen: ((event: Event) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  private listeners: Map<string, ((event: MessageEvent) => void)[]> = new Map();

  constructor(url: string, options?: { withCredentials?: boolean }) {
    this.url = url;
    this.withCredentials = options?.withCredentials ?? false;
    MockEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: (event: MessageEvent) => void) {
    const existing = this.listeners.get(type) || [];
    existing.push(listener);
    this.listeners.set(type, existing);
  }

  removeEventListener(type: string, listener: (event: MessageEvent) => void) {
    const existing = this.listeners.get(type) || [];
    this.listeners.set(
      type,
      existing.filter((l) => l !== listener),
    );
  }

  close() {
    this.readyState = 2;
  }

  // Test helpers
  simulateOpen() {
    this.readyState = 1;
    this.onopen?.(new Event("open"));
  }

  simulateError() {
    this.onerror?.(new Event("error"));
  }

  simulateMessage(type: string, data: unknown, lastEventId?: string) {
    const event = {
      type,
      data: JSON.stringify(data),
      lastEventId: lastEventId || "",
    } as MessageEvent;

    // Call type-specific listeners
    const listeners = this.listeners.get(type) || [];
    for (const listener of listeners) {
      listener(event);
    }

    // Also call onmessage for "message" type
    if (type === "message" && this.onmessage) {
      this.onmessage(event);
    }
  }

  static reset() {
    MockEventSource.instances = [];
  }

  static getLastInstance(): MockEventSource | undefined {
    return MockEventSource.instances[MockEventSource.instances.length - 1];
  }
}

// Setup global EventSource mock
const originalEventSource = globalThis.EventSource;

beforeEach(() => {
  MockEventSource.reset();
  // @ts-expect-error - Mocking global EventSource
  globalThis.EventSource = MockEventSource;
});

afterEach(() => {
  globalThis.EventSource = originalEventSource;
  vi.restoreAllMocks();
});

describe("createSSEConnection", () => {
  it("creates an EventSource with credentials", () => {
    const onMessage = vi.fn();
    createSSEConnection({ onMessage });

    const instance = MockEventSource.getLastInstance();
    expect(instance).toBeDefined();
    expect(instance?.withCredentials).toBe(true);
  });

  it("connects to the correct URL", () => {
    const onMessage = vi.fn();
    createSSEConnection({ onMessage });

    const instance = MockEventSource.getLastInstance();
    expect(instance?.url).toContain("/sse/events");
  });

  it("calls onOpen when connection opens", () => {
    const onMessage = vi.fn();
    const onOpen = vi.fn();
    createSSEConnection({ onMessage, onOpen });

    const instance = MockEventSource.getLastInstance();
    instance?.simulateOpen();

    expect(onOpen).toHaveBeenCalled();
  });

  it("updates status to connected on open", () => {
    const onMessage = vi.fn();
    const onStatusChange = vi.fn();
    createSSEConnection({ onMessage, onStatusChange });

    const instance = MockEventSource.getLastInstance();

    // First call should be "connecting"
    expect(onStatusChange).toHaveBeenCalledWith("connecting");

    instance?.simulateOpen();

    // Should now be "connected"
    expect(onStatusChange).toHaveBeenCalledWith("connected");
  });

  it("calls onError when error occurs", () => {
    const onMessage = vi.fn();
    const onError = vi.fn();
    createSSEConnection({ onMessage, onError });

    const instance = MockEventSource.getLastInstance();
    instance?.simulateError();

    expect(onError).toHaveBeenCalled();
  });

  it("parses JSON event data", () => {
    const onMessage = vi.fn();
    createSSEConnection({ onMessage });

    const instance = MockEventSource.getLastInstance();
    instance?.simulateOpen();
    instance?.simulateMessage("connected", { client_id: "abc123", authenticated: false });

    expect(onMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        event: "connected",
        data: { client_id: "abc123", authenticated: false },
      }),
    );
  });

  it("disconnect closes the EventSource", () => {
    const onMessage = vi.fn();
    const connection = createSSEConnection({ onMessage });

    const instance = MockEventSource.getLastInstance();
    expect(instance?.readyState).toBe(0);

    connection.disconnect();

    expect(instance?.readyState).toBe(2); // CLOSED
  });

  it("disconnect updates status to disconnected", () => {
    const onMessage = vi.fn();
    const onStatusChange = vi.fn();
    const connection = createSSEConnection({ onMessage, onStatusChange });

    connection.disconnect();

    expect(onStatusChange).toHaveBeenLastCalledWith("disconnected");
  });

  it("getStatus returns current status", () => {
    const onMessage = vi.fn();
    const connection = createSSEConnection({ onMessage });

    expect(connection.getStatus()).toBe("connecting");

    const instance = MockEventSource.getLastInstance();
    instance?.simulateOpen();

    expect(connection.getStatus()).toBe("connected");
  });

  it("listens to specific event types when provided", () => {
    const onMessage = vi.fn();
    createSSEConnection({
      onMessage,
      eventTypes: ["notification", "update"],
    });

    const instance = MockEventSource.getLastInstance();

    // Check that listeners were added for specific types
    instance?.simulateMessage("notification", { message: "hello" });
    expect(onMessage).toHaveBeenCalledWith(expect.objectContaining({ event: "notification" }));
  });
});

describe("getSSEEventsUrl", () => {
  it("returns the SSE events URL", () => {
    const url = getSSEEventsUrl();
    expect(url).toContain("/sse/events");
  });
});

describe("SSE reconnection", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("schedules reconnection after error", () => {
    const onMessage = vi.fn();
    const onStatusChange = vi.fn();
    createSSEConnection({
      onMessage,
      onStatusChange,
      reconnectInterval: 1000,
    });

    const firstInstance = MockEventSource.getLastInstance();
    firstInstance?.simulateError();

    // Status should be error then disconnected
    expect(onStatusChange).toHaveBeenCalledWith("error");
    expect(onStatusChange).toHaveBeenCalledWith("disconnected");

    // Advance timer past reconnect interval
    vi.advanceTimersByTime(1500);

    // A new instance should have been created
    expect(MockEventSource.instances.length).toBe(2);
  });

  it("stops reconnection after disconnect is called", () => {
    const onMessage = vi.fn();
    const connection = createSSEConnection({
      onMessage,
      reconnectInterval: 1000,
    });

    const firstInstance = MockEventSource.getLastInstance();
    firstInstance?.simulateError();

    // Disconnect before reconnection timer fires
    connection.disconnect();

    // Advance timer
    vi.advanceTimersByTime(2000);

    // No new instance should have been created after the first error
    expect(MockEventSource.instances.length).toBe(1);
  });
});

describe("SSE event ID handling", () => {
  it("includes lastEventId in event", () => {
    const onMessage = vi.fn();
    createSSEConnection({ onMessage });

    const instance = MockEventSource.getLastInstance();
    instance?.simulateMessage("connected", { test: true }, "event-123");

    expect(onMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "event-123",
      }),
    );
  });
});
