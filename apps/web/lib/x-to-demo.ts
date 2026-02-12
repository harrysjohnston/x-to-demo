import { api } from "@/lib/api";

export const X_TO_DEMO_MODELS = [
  "gpt-5.2",
  "gpt-5.1",
  "gpt-5-mini",
  "gpt-5-nano",
  "gpt-4.1-nano",
] as const;
export type XToDemoModel = (typeof X_TO_DEMO_MODELS)[number];

export const GPT5_REASONING_EFFORTS = ["minimal", "low", "medium", "high"] as const;
export const GPT52_REASONING_EFFORTS = ["none", "low", "medium", "high", "xhigh"] as const;
export type XToDemoReasoningEffort =
  | (typeof GPT5_REASONING_EFFORTS)[number]
  | (typeof GPT52_REASONING_EFFORTS)[number];

export function reasoningEffortsForModel(model: XToDemoModel): readonly XToDemoReasoningEffort[] {
  if (model === "gpt-5.2") {
    return GPT52_REASONING_EFFORTS;
  }
  return GPT5_REASONING_EFFORTS;
}

export interface XToDemoRunRequest {
  x_input: string;
  additional_context?: string;
  feature_name_hint?: string;
  model?: XToDemoModel;
  reasoning_effort?: XToDemoReasoningEffort;
}

export interface XToDemoArtifact {
  phase_key: string;
  title: string;
  markdown: string;
  saved_path: string;
}

export interface XToDemoRunResponse {
  run_id: string;
  created_at: string;
  model: XToDemoModel;
  reasoning_effort: XToDemoReasoningEffort;
  artifacts: XToDemoArtifact[];
  final_code_spec: string;
  final_code_spec_path: string;
}

export async function runXToDemoPipeline(request: XToDemoRunRequest): Promise<XToDemoRunResponse> {
  return api.post<XToDemoRunResponse>("/x-to-demo/runs", request);
}
