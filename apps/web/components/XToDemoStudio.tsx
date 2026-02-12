"use client";

import { useCallback, useEffect, useId, useMemo, useState } from "react";
import { useSSE } from "@/hooks/useSSE";
import { ApiError } from "@/lib/api";
import {
  reasoningEffortsForModel,
  runXToDemoPipeline,
  X_TO_DEMO_MODELS,
  type XToDemoModel,
  type XToDemoReasoningEffort,
  type XToDemoRunResponse,
} from "@/lib/x-to-demo";
import { Button } from "./ui/button";

const PIPELINE_PHASES = [
  {
    key: "phase-1-input-to-feature-spec",
    title: "Phase 1: Input -> SDD Feature Spec",
  },
  {
    key: "phase-2-feature-spec-to-demo-spec",
    title: "Phase 2: Feature Spec -> Demo Spec",
  },
  {
    key: "phase-3-demo-spec-to-code-spec",
    title: "Phase 3: Demo Spec -> Code Spec",
  },
] as const;

const PHASE_KEYS = PIPELINE_PHASES.map((phase) => phase.key);

interface XToDemoRunProgressEventData {
  pipeline: string;
  run_id: string;
  status: string;
  phase_key?: string;
  error?: string;
}

const MAX_INPUT_CHARS = 60000;

function formatTimestamp(isoDate: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(isoDate));
}

export function XToDemoStudio() {
  const transcriptInputId = useId();
  const [transcriptText, setTranscriptText] = useState("");
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [additionalContext, setAdditionalContext] = useState("");
  const [featureNameHint, setFeatureNameHint] = useState("");
  const [selectedModel, setSelectedModel] = useState<XToDemoModel>("gpt-5.2");
  const [reasoningEffort, setReasoningEffort] = useState<XToDemoReasoningEffort>("low");
  const [isDragging, setIsDragging] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [activePhaseKey, setActivePhaseKey] = useState<string | null>(null);
  const [completedPhaseKeys, setCompletedPhaseKeys] = useState<string[]>([]);
  const [trackedRunId, setTrackedRunId] = useState<string | null>(null);
  const [runResult, setRunResult] = useState<XToDemoRunResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const completedPhaseSet = useMemo(() => new Set(completedPhaseKeys), [completedPhaseKeys]);

  const canRun = useMemo(
    () =>
      transcriptText.trim().length >= 20 &&
      transcriptText.trim().length <= MAX_INPUT_CHARS &&
      !isRunning,
    [transcriptText, isRunning],
  );
  const availableReasoningEfforts = useMemo(
    () => reasoningEffortsForModel(selectedModel),
    [selectedModel],
  );
  const { lastEvent } = useSSE<XToDemoRunProgressEventData>({
    enabled: true,
    eventTypes: ["x_to_demo_run_progress"],
    maxEvents: 20,
  });

  const markPhaseComplete = useCallback((phaseKey: string) => {
    setCompletedPhaseKeys((previous) => {
      if (!PHASE_KEYS.includes(phaseKey as (typeof PHASE_KEYS)[number])) {
        return previous;
      }
      return previous.includes(phaseKey) ? previous : [...previous, phaseKey];
    });
  }, []);

  useEffect(() => {
    if (!availableReasoningEfforts.includes(reasoningEffort)) {
      setReasoningEffort(
        availableReasoningEfforts.includes("low") ? "low" : availableReasoningEfforts[0],
      );
    }
  }, [availableReasoningEfforts, reasoningEffort]);

  useEffect(() => {
    if (lastEvent?.event !== "x_to_demo_run_progress") return;
    if (!lastEvent.data || typeof lastEvent.data !== "object" || Array.isArray(lastEvent.data)) {
      return;
    }

    const payload = lastEvent.data as Partial<XToDemoRunProgressEventData>;
    if (payload.pipeline !== "x-to-demo") return;
    if (typeof payload.run_id !== "string" || typeof payload.status !== "string") return;

    if (trackedRunId && payload.run_id !== trackedRunId) return;
    if (!trackedRunId) {
      setTrackedRunId(payload.run_id);
    }

    if (payload.status === "run_started") {
      setActivePhaseKey(null);
      setCompletedPhaseKeys([]);
      return;
    }

    if (payload.status === "phase_started") {
      if (typeof payload.phase_key === "string") {
        setActivePhaseKey(payload.phase_key);
      }
      return;
    }

    if (payload.status === "phase_completed") {
      if (typeof payload.phase_key === "string") {
        markPhaseComplete(payload.phase_key);
      }
      setActivePhaseKey(null);
      return;
    }

    if (payload.status === "phase_failed" || payload.status === "run_failed") {
      if (typeof payload.error === "string" && payload.error.trim()) {
        setError(payload.error);
      }
      setActivePhaseKey(null);
      return;
    }

    if (payload.status === "run_completed") {
      setActivePhaseKey(null);
    }
  }, [lastEvent, markPhaseComplete, trackedRunId]);

  const applyTranscriptFile = async (file: File) => {
    setError(null);
    try {
      const text = await file.text();
      if (!text.trim()) {
        setError("The selected file is empty. Upload an Input X file with text content.");
        return;
      }
      setTranscriptText(text);
      setSelectedFileName(file.name);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not read Input X file");
    }
  };

  const handleTranscriptDrop = async (file: File | null) => {
    setIsDragging(false);
    if (!file) return;
    await applyTranscriptFile(file);
  };

  const handleRunPipeline = async () => {
    if (!canRun) return;

    setError(null);
    setRunResult(null);
    setCopied(false);
    setTrackedRunId(null);
    setCompletedPhaseKeys([]);
    setActivePhaseKey(null);
    setIsRunning(true);

    try {
      const response = await runXToDemoPipeline({
        x_input: transcriptText,
        additional_context: additionalContext || undefined,
        feature_name_hint: featureNameHint || undefined,
        model: selectedModel,
        reasoning_effort: reasoningEffort,
      });
      setRunResult(response);
      setTrackedRunId(response.run_id);
      setCompletedPhaseKeys(response.artifacts.map((artifact) => artifact.phase_key));
      setActivePhaseKey(null);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.error.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Pipeline execution failed");
      }
    } finally {
      setIsRunning(false);
    }
  };

  const handleCopySpec = async () => {
    if (!runResult?.final_code_spec) return;
    try {
      await navigator.clipboard.writeText(runResult.final_code_spec);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      setError("Clipboard access failed. Copy manually from the code spec panel.");
    }
  };

  return (
    <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
      <section className="relative overflow-hidden rounded-2xl border border-border/70 bg-card/40 p-6 backdrop-blur-sm">
        <div className="absolute right-0 top-0 h-20 w-20 bg-gradient-to-bl from-primary/20 to-transparent" />
        <header className="mb-6">
          <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Input workspace
          </p>
          <h2 className="mt-2 text-2xl font-display leading-tight">
            Feed input X into the pipeline
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Upload an Input X file or paste raw material, then run all three plan phases to generate
            a saved code spec.
          </p>
        </header>

        <div className="space-y-5">
          <label
            htmlFor={transcriptInputId}
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={(event) => {
              event.preventDefault();
              setIsDragging(false);
            }}
            onDrop={async (event) => {
              event.preventDefault();
              await handleTranscriptDrop(event.dataTransfer.files?.[0] ?? null);
            }}
            className={`block cursor-pointer rounded-xl border border-dashed p-5 transition-all duration-300 ${
              isDragging
                ? "border-primary bg-primary/10 shadow-lg shadow-primary/10"
                : "border-border/70 hover:border-primary/50 hover:bg-primary/5"
            }`}
          >
            <input
              id={transcriptInputId}
              type="file"
              accept=".txt,.md,.rtf,.json"
              className="hidden"
              onChange={async (event) => {
                await handleTranscriptDrop(event.target.files?.[0] ?? null);
              }}
            />
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-medium">
                  {selectedFileName ?? "Drop Input X file here or click to browse"}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Accepted: `.txt`, `.md`, `.rtf`, `.json`
                </p>
              </div>
              <span className="rounded-full border border-border/80 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
                File input
              </span>
            </div>
          </label>

          <div>
            <label
              htmlFor="x-transcript-text"
              className="mb-2 block text-xs uppercase tracking-[0.16em] text-muted-foreground"
            >
              Input X
            </label>
            <textarea
              id="x-transcript-text"
              value={transcriptText}
              onChange={(event) => setTranscriptText(event.target.value)}
              placeholder="Paste raw Input X here..."
              rows={10}
              className="w-full rounded-xl border border-border/70 bg-background/50 px-4 py-3 text-sm leading-relaxed focus:border-primary focus:outline-none"
            />
            <p className="mt-2 text-xs text-muted-foreground">
              {transcriptText.trim().length} / {MAX_INPUT_CHARS} chars
            </p>
          </div>

          <div>
            <label
              htmlFor="x-feature-hint"
              className="mb-2 block text-xs uppercase tracking-[0.16em] text-muted-foreground"
            >
              Feature name hint (optional)
            </label>
            <input
              id="x-feature-hint"
              type="text"
              value={featureNameHint}
              onChange={(event) => setFeatureNameHint(event.target.value)}
              placeholder="e.g. Meeting notes to demo plan"
              className="w-full rounded-xl border border-border/70 bg-background/50 px-4 py-3 text-sm focus:border-primary focus:outline-none"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label
                htmlFor="x-model"
                className="mb-2 block text-xs uppercase tracking-[0.16em] text-muted-foreground"
              >
                Model
              </label>
              <select
                id="x-model"
                value={selectedModel}
                onChange={(event) => setSelectedModel(event.target.value as XToDemoModel)}
                className="w-full rounded-xl border border-border/70 bg-background/50 px-4 py-3 text-sm focus:border-primary focus:outline-none"
              >
                {X_TO_DEMO_MODELS.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label
                htmlFor="x-reasoning-effort"
                className="mb-2 block text-xs uppercase tracking-[0.16em] text-muted-foreground"
              >
                Reasoning effort
              </label>
              <select
                id="x-reasoning-effort"
                value={reasoningEffort}
                onChange={(event) =>
                  setReasoningEffort(event.target.value as XToDemoReasoningEffort)
                }
                className="w-full rounded-xl border border-border/70 bg-background/50 px-4 py-3 text-sm focus:border-primary focus:outline-none"
              >
                {availableReasoningEfforts.map((effort) => (
                  <option key={effort} value={effort}>
                    {effort}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label
              htmlFor="x-context"
              className="mb-2 block text-xs uppercase tracking-[0.16em] text-muted-foreground"
            >
              Additional context (optional)
            </label>
            <textarea
              id="x-context"
              value={additionalContext}
              onChange={(event) => setAdditionalContext(event.target.value)}
              placeholder="Roadmap constraints, existing decisions, target users, etc."
              rows={4}
              className="w-full rounded-xl border border-border/70 bg-background/50 px-4 py-3 text-sm leading-relaxed focus:border-primary focus:outline-none"
            />
          </div>

          {error && (
            <div className="rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <Button
            onClick={handleRunPipeline}
            disabled={!canRun}
            className="h-12 w-full tracking-wide uppercase"
          >
            {isRunning ? "Running X-to-Demo pipeline..." : "Run pipeline"}
          </Button>
        </div>
      </section>

      <section className="rounded-2xl border border-border/70 bg-card/40 p-6 backdrop-blur-sm">
        <header className="mb-6">
          <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Pipeline output
          </p>
          <h2 className="mt-2 text-2xl font-display leading-tight">Progress and generated spec</h2>
        </header>

        <ol className="space-y-3">
          {PIPELINE_PHASES.map((phase) => {
            const isComplete = completedPhaseSet.has(phase.key);
            const isActive = activePhaseKey === phase.key;
            return (
              <li
                key={phase.key}
                className={`rounded-lg border px-3 py-2 text-sm transition-all ${
                  isComplete
                    ? "border-primary/40 bg-primary/10"
                    : isActive
                      ? "border-primary/50 bg-primary/15 animate-pulse"
                      : "border-border/60 bg-background/30 text-muted-foreground"
                }`}
              >
                <span className="font-medium">{phase.title}</span>
              </li>
            );
          })}
        </ol>

        {!runResult && (
          <p className="mt-6 rounded-xl border border-border/60 bg-background/30 px-4 py-3 text-sm text-muted-foreground">
            Run the pipeline to generate phase artifacts and a final code spec.
          </p>
        )}

        {runResult && (
          <div className="mt-6 space-y-4 animate-fade-up">
            <div className="rounded-xl border border-primary/30 bg-primary/10 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-primary">Run complete</p>
              <p className="mt-1 text-sm text-foreground">
                {runResult.run_id} • {formatTimestamp(runResult.created_at)} • {runResult.model} •{" "}
                {runResult.reasoning_effort}
              </p>
              <p className="mt-2 text-xs text-muted-foreground">
                Saved code spec: <code>{runResult.final_code_spec_path}</code>
              </p>
            </div>

            <div className="flex gap-3">
              <Button type="button" variant="secondary" onClick={handleCopySpec} className="h-10">
                {copied ? "Copied" : "Copy code spec"}
              </Button>
            </div>

            <div className="rounded-xl border border-border/60 bg-background/40 p-4">
              <p className="mb-3 text-xs uppercase tracking-[0.16em] text-muted-foreground">
                Final code spec
              </p>
              <pre className="max-h-[22rem] overflow-auto whitespace-pre-wrap text-xs leading-relaxed text-foreground">
                {runResult.final_code_spec}
              </pre>
            </div>

            <div className="space-y-3">
              {runResult.artifacts.map((artifact) => (
                <details
                  key={artifact.phase_key}
                  className="rounded-xl border border-border/60 bg-background/30 px-4 py-3"
                >
                  <summary className="cursor-pointer list-none text-sm font-medium">
                    {artifact.title}
                  </summary>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Saved path: <code>{artifact.saved_path}</code>
                  </p>
                  <pre className="mt-3 max-h-56 overflow-auto whitespace-pre-wrap text-xs leading-relaxed text-foreground">
                    {artifact.markdown}
                  </pre>
                </details>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
