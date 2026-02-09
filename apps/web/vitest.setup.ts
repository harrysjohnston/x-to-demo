import "@testing-library/jest-dom";
import { vi } from "vitest";

// Mock CSS imports
vi.mock("*.css", () => ({}));

// Mock localStorage for tests
const localStorageStore = new Map<string, string>();

const localStorageMock = {
  getItem: vi.fn((key: string) => localStorageStore.get(key) ?? null),
  setItem: vi.fn((key: string, value: string) => {
    localStorageStore.set(key, value);
  }),
  removeItem: vi.fn((key: string) => {
    localStorageStore.delete(key);
  }),
  clear: vi.fn(() => {
    localStorageStore.clear();
  }),
  get length() {
    return localStorageStore.size;
  },
  key: vi.fn((index: number) => {
    const keys = Array.from(localStorageStore.keys());
    return keys[index] ?? null;
  }),
};

Object.defineProperty(global, "localStorage", {
  value: localStorageMock,
  writable: true,
});
