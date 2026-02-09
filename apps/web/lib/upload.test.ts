import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { type UploadInstruction, uploadFile } from "./upload";

// Mock XMLHttpRequest
class MockXMLHttpRequest {
  static instances: MockXMLHttpRequest[] = [];
  static original: typeof XMLHttpRequest | null = null;

  url: string = "";
  method: string = "";
  upload: {
    onprogress: ((event: ProgressEvent) => void) | null;
  } = {
    onprogress: null,
  };
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onabort: (() => void) | null = null;
  status: number = 200;
  statusText: string = "OK";
  readyState: number = 0;
  private sentData: FormData | null = null;

  constructor() {
    MockXMLHttpRequest.instances.push(this);
  }

  open(method: string, url: string) {
    this.method = method;
    this.url = url;
    this.readyState = 1;
  }

  send(data?: FormData) {
    this.sentData = data || null;
    this.readyState = 2;
  }

  // Test helpers
  simulateProgress(loaded: number, total: number) {
    if (this.upload.onprogress) {
      const event = {
        lengthComputable: true,
        loaded,
        total,
      } as ProgressEvent;
      this.upload.onprogress(event);
    }
  }

  simulateSuccess(status: number = 200) {
    this.status = status;
    this.statusText = status === 200 ? "OK" : "Created";
    this.readyState = 4;
    if (this.onload) {
      this.onload();
    }
  }

  simulateError() {
    this.status = 0;
    this.readyState = 4;
    if (this.onerror) {
      this.onerror();
    }
  }

  simulateAbort() {
    this.readyState = 4;
    if (this.onabort) {
      this.onabort();
    }
  }

  getSentFormData(): FormData | null {
    return this.sentData;
  }
}

describe("uploadFile", () => {
  beforeEach(() => {
    MockXMLHttpRequest.instances = [];
    globalThis.XMLHttpRequest = MockXMLHttpRequest as unknown as typeof XMLHttpRequest;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const createInstruction = (overrides?: Partial<UploadInstruction>): UploadInstruction => ({
    url: "https://s3.example.com/bucket/upload",
    method: "POST",
    fields: {
      key: "uploads/1/test-file.txt",
      policy: "test-policy",
      "x-amz-signature": "test-signature",
      "Content-Type": "text/plain",
    },
    objectKey: "uploads/1/test-file.txt",
    expiresAt: new Date().toISOString(),
    ...overrides,
  });

  it("should upload file successfully", async () => {
    const instruction = createInstruction();
    const file = new File(["test content"], "test.txt", { type: "text/plain" });
    const progressCallback = vi.fn();

    const uploadPromise = uploadFile(instruction, file, progressCallback);

    // Simulate progress
    const xhr = MockXMLHttpRequest.instances[0];
    expect(xhr).toBeDefined();
    expect(xhr.method).toBe("POST");
    expect(xhr.url).toBe(instruction.url);

    xhr.simulateProgress(50, 100);
    expect(progressCallback).toHaveBeenCalledWith(50);

    xhr.simulateProgress(100, 100);
    expect(progressCallback).toHaveBeenCalledWith(100);

    // Simulate success
    xhr.simulateSuccess(204);

    await expect(uploadPromise).resolves.toBeUndefined();
  });

  it("should build FormData correctly", async () => {
    const instruction = createInstruction();
    const file = new File(["test"], "test.txt", { type: "text/plain" });

    const uploadPromise = uploadFile(instruction, file);

    const xhr = MockXMLHttpRequest.instances[0];
    const formData = xhr.getSentFormData();

    expect(formData).toBeDefined();
    // Verify fields are included
    expect(formData?.has("key")).toBe(true);
    expect(formData?.has("policy")).toBe(true);
    expect(formData?.has("x-amz-signature")).toBe(true);
    expect(formData?.has("Content-Type")).toBe(true);
    expect(formData?.has("file")).toBe(true);

    xhr.simulateSuccess();
    await uploadPromise;
  });

  it("should handle upload errors", async () => {
    const instruction = createInstruction();
    const file = new File(["test"], "test.txt", { type: "text/plain" });

    const uploadPromise = uploadFile(instruction, file);

    const xhr = MockXMLHttpRequest.instances[0];
    xhr.simulateError();

    await expect(uploadPromise).rejects.toThrow("Network error");
  });

  it("should handle HTTP error status codes", async () => {
    const instruction = createInstruction();
    const file = new File(["test"], "test.txt", { type: "text/plain" });

    const uploadPromise = uploadFile(instruction, file);

    const xhr = MockXMLHttpRequest.instances[0];
    xhr.status = 403;
    xhr.statusText = "Forbidden";
    xhr.simulateSuccess(403);

    await expect(uploadPromise).rejects.toThrow("Upload failed");
  });

  it("should handle abort", async () => {
    const instruction = createInstruction();
    const file = new File(["test"], "test.txt", { type: "text/plain" });

    const uploadPromise = uploadFile(instruction, file);

    const xhr = MockXMLHttpRequest.instances[0];
    xhr.simulateAbort();

    await expect(uploadPromise).rejects.toThrow("Upload aborted");
  });

  it("should call progress callback when provided", async () => {
    const instruction = createInstruction();
    const file = new File(["test"], "test.txt", { type: "text/plain" });
    const progressCallback = vi.fn();

    const uploadPromise = uploadFile(instruction, file, progressCallback);

    const xhr = MockXMLHttpRequest.instances[0];
    xhr.simulateProgress(25, 100);
    expect(progressCallback).toHaveBeenCalledWith(25);

    xhr.simulateProgress(75, 100);
    expect(progressCallback).toHaveBeenCalledWith(75);

    xhr.simulateSuccess();
    await uploadPromise;
  });

  it("should not call progress callback if not provided", async () => {
    const instruction = createInstruction();
    const file = new File(["test"], "test.txt", { type: "text/plain" });

    const uploadPromise = uploadFile(instruction, file);

    const xhr = MockXMLHttpRequest.instances[0];
    xhr.simulateProgress(50, 100);
    // Should not throw even without callback

    xhr.simulateSuccess();
    await uploadPromise;
  });

  it("should handle non-computable progress", async () => {
    const instruction = createInstruction();
    const file = new File(["test"], "test.txt", { type: "text/plain" });
    const progressCallback = vi.fn();

    const uploadPromise = uploadFile(instruction, file, progressCallback);

    const xhr = MockXMLHttpRequest.instances[0];
    // Simulate non-computable progress
    if (xhr.upload.onprogress) {
      const event = {
        lengthComputable: false,
        loaded: 0,
        total: 0,
      } as ProgressEvent;
      xhr.upload.onprogress(event);
    }

    // Progress callback should not be called for non-computable progress
    expect(progressCallback).not.toHaveBeenCalled();

    xhr.simulateSuccess();
    await uploadPromise;
  });
});
