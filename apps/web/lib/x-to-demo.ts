import { api } from "@/lib/api";
import { AUTH_ACCESS_TOKEN_KEY } from "@/lib/storage-keys";

export const X_TO_DEMO_MODELS = [
  "gpt-5.2",
  "gpt-5.1",
  "gpt-5-mini",
  "gpt-5-nano",
  "gpt-4.1-nano",
] as const;
export type XToDemoModel = (typeof X_TO_DEMO_MODELS)[number];

export const X_TO_DEMO_PHASE_KEYS = ["feature_spec", "demo_spec", "code_spec"] as const;
export type XToDemoPhaseKey = (typeof X_TO_DEMO_PHASE_KEYS)[number];

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
  stop_after_phase?: XToDemoPhaseKey;
}

export interface XToDemoArtifact {
  phase_key: XToDemoPhaseKey;
  title: string;
  markdown: string;
  saved_path: string;
  json_path: string;
  json_content: Record<string, unknown>;
  content_hash: string;
}

export interface XToDemoRunResponse {
  run_id: string;
  created_at: string;
  model: XToDemoModel;
  reasoning_effort: XToDemoReasoningEffort;
  artifacts: XToDemoArtifact[];
  final_code_spec?: string | null;
  final_code_spec_path?: string | null;
  stop_after_phase: XToDemoPhaseKey;
  next_phase_key?: XToDemoPhaseKey | null;
  usage_totals: Record<string, number>;
  cost_totals?: Record<string, number> | null;
}

export interface XToDemoPhaseStatus {
  phase_key: XToDemoPhaseKey;
  title: string;
  status: "pending" | "running" | "completed" | "failed" | "stale";
  input_artifact_ref?: XToDemoPhaseKey | null;
  output_json_path?: string | null;
  output_md_path?: string | null;
  content_hash?: string | null;
  error?: string | null;
}

export interface XToDemoRunDetailResponse {
  run_id: string;
  created_at: string;
  updated_at: string;
  model: XToDemoModel;
  reasoning_effort: XToDemoReasoningEffort;
  stop_after_phase: XToDemoPhaseKey;
  next_phase_key?: XToDemoPhaseKey | null;
  phases: XToDemoPhaseStatus[];
  artifacts: XToDemoArtifact[];
  usage_totals: Record<string, number>;
  cost_totals?: Record<string, number> | null;
}

export interface XToDemoArtifactResponse {
  run_id: string;
  artifact: XToDemoArtifact;
}

export interface XToDemoUpdateArtifactRequest {
  markdown?: string;
  json_content?: Record<string, unknown>;
}

export interface XToDemoResumeRequest {
  from_phase?: XToDemoPhaseKey;
  stop_after_phase?: XToDemoPhaseKey;
  use_edited_artifacts?: boolean;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchBinary(path: string): Promise<Blob> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const token = typeof window !== "undefined" ? localStorage.getItem(AUTH_ACCESS_TOKEN_KEY) : null;
  const response = await fetch(`${API_BASE_URL}${normalizedPath}`, {
    method: "GET",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });

  if (!response.ok) {
    throw new Error(`Download failed (${response.status})`);
  }

  return response.blob();
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export async function runXToDemoPipeline(request: XToDemoRunRequest): Promise<XToDemoRunResponse> {
  return api.post<XToDemoRunResponse>("/x-to-demo/runs", request);
}

export async function getXToDemoRun(runId: string): Promise<XToDemoRunDetailResponse> {
  return api.get<XToDemoRunDetailResponse>(`/x-to-demo/runs/${runId}`);
}

export async function getXToDemoArtifact(
  runId: string,
  phaseKey: XToDemoPhaseKey,
): Promise<XToDemoArtifactResponse> {
  return api.get<XToDemoArtifactResponse>(`/x-to-demo/runs/${runId}/artifacts/${phaseKey}`);
}

export async function updateXToDemoArtifact(
  runId: string,
  phaseKey: XToDemoPhaseKey,
  request: XToDemoUpdateArtifactRequest,
): Promise<XToDemoArtifactResponse> {
  return api.put<XToDemoArtifactResponse>(
    `/x-to-demo/runs/${runId}/artifacts/${phaseKey}`,
    request,
  );
}

export async function resumeXToDemoRun(
  runId: string,
  request: XToDemoResumeRequest,
): Promise<XToDemoRunResponse> {
  return api.post<XToDemoRunResponse>(`/x-to-demo/runs/${runId}/resume`, request);
}

export async function downloadXToDemoArtifact(
  runId: string,
  phaseKey: XToDemoPhaseKey,
): Promise<Blob> {
  return fetchBinary(`/x-to-demo/runs/${runId}/artifacts/${phaseKey}/download`);
}

export async function downloadXToDemoRun(runId: string): Promise<Blob> {
  return fetchBinary(`/x-to-demo/runs/${runId}/download`);
}
