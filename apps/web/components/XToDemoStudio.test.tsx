import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { runXToDemoPipeline } from "@/lib/x-to-demo";
import { XToDemoStudio } from "./XToDemoStudio";

vi.mock("@/lib/x-to-demo", async () => {
  const actual = await vi.importActual<typeof import("@/lib/x-to-demo")>("@/lib/x-to-demo");
  return {
    ...actual,
    runXToDemoPipeline: vi.fn(),
  };
});

const mockedRunXToDemoPipeline = vi.mocked(runXToDemoPipeline);

vi.mock("@/hooks/useSSE", () => ({
  useSSE: vi.fn(() => ({
    status: "disconnected",
    lastEvent: null,
    events: [],
    disconnect: vi.fn(),
    reconnect: vi.fn(),
    clearEvents: vi.fn(),
  })),
}));

const fakeResponse = {
  run_id: "run-test-1",
  created_at: "2026-02-12T12:00:00Z",
  model: "gpt-5.2" as const,
  reasoning_effort: "xhigh" as const,
  artifacts: [],
  final_code_spec: "# Code Spec",
  final_code_spec_path: "artifacts/x-to-demo/run-test-1/04-phase-4.md",
};

describe("XToDemoStudio", () => {
  beforeEach(() => {
    mockedRunXToDemoPipeline.mockReset();
    mockedRunXToDemoPipeline.mockResolvedValue(fakeResponse);
  });

  it("sends selected model and reasoning effort in the run payload", async () => {
    render(<XToDemoStudio />);

    const inputField = screen.getByLabelText(/^Input X$/i);
    fireEvent.change(inputField, {
      target: {
        value: "This input has enough content to run the pipeline successfully.",
      },
    });
    fireEvent.change(screen.getByLabelText("Reasoning effort"), {
      target: { value: "xhigh" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Run pipeline/i }));

    await waitFor(() => {
      expect(mockedRunXToDemoPipeline).toHaveBeenCalledWith({
        x_input: "This input has enough content to run the pipeline successfully.",
        additional_context: undefined,
        feature_name_hint: undefined,
        model: "gpt-5.2",
        reasoning_effort: "xhigh",
      });
    });
  });

  it("resets reasoning effort when switching to a model that does not support current value", async () => {
    render(<XToDemoStudio />);

    const modelSelect = screen.getByLabelText("Model");
    const reasoningSelect = screen.getByLabelText("Reasoning effort");

    fireEvent.change(reasoningSelect, { target: { value: "xhigh" } });
    expect((reasoningSelect as HTMLSelectElement).value).toBe("xhigh");

    fireEvent.change(modelSelect, { target: { value: "gpt-5.1" } });

    await waitFor(() => {
      expect((reasoningSelect as HTMLSelectElement).value).toBe("low");
    });
    expect(screen.queryByRole("option", { name: "xhigh" })).not.toBeInTheDocument();
  });
});
