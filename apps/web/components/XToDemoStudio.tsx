"use client";

import { useCallback, useEffect, useId, useMemo, useState } from "react";
import { ApiError } from "@/lib/api";
import {
  downloadBlob,
  downloadXToDemoArtifact,
  downloadXToDemoRun,
  getXToDemoRun,
  reasoningEffortsForModel,
  resumeXToDemoRun,
  runXToDemoPipeline,
  updateXToDemoArtifact,
  X_TO_DEMO_MODELS,
  type XToDemoArtifact,
  type XToDemoModel,
  type XToDemoPhaseKey,
  type XToDemoReasoningEffort,
  type XToDemoRunDetailResponse,
  type XToDemoRunResponse,
} from "@/lib/x-to-demo";
import { Button } from "./ui/button";

const PIPELINE_PHASES: Array<{ key: XToDemoPhaseKey; title: string }> = [
  {
    key: "feature_spec",
    title: "Phase 1: Input -> Feature Spec",
  },
  {
    key: "demo_spec",
    title: "Phase 2: Feature Spec -> Demo Spec",
  },
  {
    key: "code_spec",
    title: "Phase 3: Demo Spec -> Code Spec",
  },
];

const PHASE_KEYS = PIPELINE_PHASES.map((phase) => phase.key);

const MAX_INPUT_CHARS = 60000;

function formatTimestamp(isoDate: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(isoDate));
}

function toRunResponse(detail: XToDemoRunDetailResponse): XToDemoRunResponse {
  const codeSpecArtifact = detail.artifacts.find((artifact) => artifact.phase_key === "code_spec");
  return {
    run_id: detail.run_id,
    created_at: detail.created_at,
    model: detail.model,
    reasoning_effort: detail.reasoning_effort,
    artifacts: detail.artifacts,
    final_code_spec: codeSpecArtifact?.markdown ?? null,
    final_code_spec_path: codeSpecArtifact?.saved_path ?? null,
    stop_after_phase: detail.stop_after_phase,
    next_phase_key: detail.next_phase_key,
    usage_totals: detail.usage_totals,
    cost_totals: detail.cost_totals,
  };
}

function phaseTitle(phaseKey: XToDemoPhaseKey): string {
  return PIPELINE_PHASES.find((phase) => phase.key === phaseKey)?.title ?? phaseKey;
}

export function XToDemoStudio() {
  const transcriptInputId = useId();
  const [transcriptText, setTranscriptText] = useState("");
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [additionalContext, setAdditionalContext] = useState("");
  const [featureNameHint, setFeatureNameHint] = useState("");
  const [selectedModel, setSelectedModel] = useState<XToDemoModel>("gpt-5.2");
  const [reasoningEffort, setReasoningEffort] = useState<XToDemoReasoningEffort>("low");
  const [stopAfterPhase, setStopAfterPhase] = useState<XToDemoPhaseKey>("code_spec");
  const [isDragging, setIsDragging] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isResuming, setIsResuming] = useState(false);
  const [isSavingArtifact, setIsSavingArtifact] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [activePhaseKey, setActivePhaseKey] = useState<XToDemoPhaseKey | null>(null);
  const [completedPhaseKeys, setCompletedPhaseKeys] = useState<XToDemoPhaseKey[]>([]);
  const [failedPhaseKeys, setFailedPhaseKeys] = useState<XToDemoPhaseKey[]>([]);
  const [stalePhaseKeys, setStalePhaseKeys] = useState<XToDemoPhaseKey[]>([]);
  const [trackedRunId, setTrackedRunId] = useState<string | null>(null);
  const [runResult, setRunResult] = useState<XToDemoRunResponse | null>(null);
  const [activeArtifactTab, setActiveArtifactTab] = useState<XToDemoPhaseKey | null>(null);
  const [artifactJsonDraft, setArtifactJsonDraft] = useState("");
  const [copied, setCopied] = useState(false);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const completedPhaseSet = useMemo(() => new Set(completedPhaseKeys), [completedPhaseKeys]);
  const failedPhaseSet = useMemo(() => new Set(failedPhaseKeys), [failedPhaseKeys]);
  const stalePhaseSet = useMemo(() => new Set(stalePhaseKeys), [stalePhaseKeys]);

  const canRun = useMemo(
    () =>
      transcriptText.trim().length >= 20 &&
      transcriptText.trim().length <= MAX_INPUT_CHARS &&
      !isRunning &&
      !isResuming,
    [transcriptText, isRunning, isResuming],
  );

  const availableReasoningEfforts = useMemo(
    () => reasoningEffortsForModel(selectedModel),
    [selectedModel],
  );

  const activeArtifact: XToDemoArtifact | null = useMemo(() => {
    if (!runResult || !activeArtifactTab) return null;
    return runResult.artifacts.find((artifact) => artifact.phase_key === activeArtifactTab) ?? null;
  }, [runResult, activeArtifactTab]);

  const hydrateFromRunResult = useCallback((result: XToDemoRunResponse) => {
    setRunResult(result);
    setTrackedRunId(result.run_id);
    setCompletedPhaseKeys(result.artifacts.map((artifact) => artifact.phase_key));
    setFailedPhaseKeys([]);
    setStalePhaseKeys([]);
    setActivePhaseKey(null);
    if (result.artifacts.length > 0) {
      const tab =
        result.artifacts[result.artifacts.length - 1]?.phase_key ?? result.artifacts[0]?.phase_key;
      setActiveArtifactTab(tab);
    }
  }, []);

  useEffect(() => {
    if (!availableReasoningEfforts.includes(reasoningEffort)) {
      setReasoningEffort(
        availableReasoningEfforts.includes("low") ? "low" : availableReasoningEfforts[0],
      );
    }
  }, [availableReasoningEfforts, reasoningEffort]);

  useEffect(() => {
    if (!activeArtifact) {
      setArtifactJsonDraft("");
      return;
    }
    setArtifactJsonDraft(JSON.stringify(activeArtifact.json_content, null, 2));
  }, [activeArtifact]);

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

  const refreshRun = async (runId: string) => {
    const detail = await getXToDemoRun(runId);
    const nextRun = toRunResponse(detail);
    hydrateFromRunResult(nextRun);

    const running = detail.phases.find((phase) => phase.status === "running")?.phase_key ?? null;
    const stale = detail.phases
      .filter((phase) => phase.status === "stale")
      .map((phase) => phase.phase_key);
    const failed = detail.phases
      .filter((phase) => phase.status === "failed")
      .map((phase) => phase.phase_key);
    setActivePhaseKey(running);
    setStalePhaseKeys(stale);
    setFailedPhaseKeys(failed);
  };

  useEffect(() => {
    if (!trackedRunId) return;
    if (!isRunning && !isResuming) return;

    let cancelled = false;
    const poll = async () => {
      try {
        const detail = await getXToDemoRun(trackedRunId);
        if (cancelled) return;
        setRunResult(toRunResponse(detail));

        const completed = detail.phases
          .filter((phase) => phase.status === "completed")
          .map((phase) => phase.phase_key);
        const stale = detail.phases
          .filter((phase) => phase.status === "stale")
          .map((phase) => phase.phase_key);
        const failed = detail.phases
          .filter((phase) => phase.status === "failed")
          .map((phase) => phase.phase_key);
        const running =
          detail.phases.find((phase) => phase.status === "running")?.phase_key ?? null;

        setCompletedPhaseKeys(completed);
        setStalePhaseKeys(stale);
        setFailedPhaseKeys(failed);
        setActivePhaseKey(running);
      } catch {
        // Best-effort polling while run is in progress.
      }
    };

    void poll();
    const interval = window.setInterval(() => {
      void poll();
    }, 1200);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [isResuming, isRunning, trackedRunId]);

  const handleRunPipeline = async () => {
    if (!canRun) return;

    setError(null);
    setExportMessage(null);
    setRunResult(null);
    setCopied(false);
    setTrackedRunId(null);
    setCompletedPhaseKeys([]);
    setFailedPhaseKeys([]);
    setStalePhaseKeys([]);
    setActivePhaseKey(null);
    setIsRunning(true);

    try {
      const response = await runXToDemoPipeline({
        x_input: transcriptText,
        additional_context: additionalContext || undefined,
        feature_name_hint: featureNameHint || undefined,
        model: selectedModel,
        reasoning_effort: reasoningEffort,
        stop_after_phase: stopAfterPhase,
      });
      hydrateFromRunResult(response);
      await refreshRun(response.run_id);
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

  const handleResume = async () => {
    if (!runResult?.run_id || !runResult.next_phase_key) return;
    setError(null);
    setIsResuming(true);
    try {
      const response = await resumeXToDemoRun(runResult.run_id, {
        from_phase: runResult.next_phase_key,
        stop_after_phase: stopAfterPhase,
        use_edited_artifacts: true,
      });
      hydrateFromRunResult(response);
      await refreshRun(response.run_id);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.error.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Pipeline resume failed");
      }
    } finally {
      setIsResuming(false);
    }
  };

  const handleSaveArtifact = async () => {
    if (!runResult?.run_id || !activeArtifactTab) return;
    setError(null);
    setIsSavingArtifact(true);
    try {
      const parsed = JSON.parse(artifactJsonDraft) as Record<string, unknown>;
      await updateXToDemoArtifact(runResult.run_id, activeArtifactTab, {
        json_content: parsed,
      });
      await refreshRun(runResult.run_id);
    } catch (err) {
      if (err instanceof SyntaxError) {
        setError(`Artifact JSON is invalid: ${err.message}`);
      } else if (err instanceof ApiError) {
        setError(err.error.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Artifact save failed");
      }
    } finally {
      setIsSavingArtifact(false);
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

  const handleExportToAIStudio = async () => {
    if (!runResult?.final_code_spec) return;
    try {
      await navigator.clipboard.writeText(runResult.final_code_spec);
      setExportMessage("Code spec copied. Paste it into Google AI Studio.");
    } catch {
      downloadBlob(
        new Blob([runResult.final_code_spec], { type: "text/markdown" }),
        "ai-studio-prompt.md",
      );
      setExportMessage("Clipboard unavailable. Downloaded ai-studio-prompt.md instead.");
    }
  };

  const handleDownloadArtifact = async (phaseKey: XToDemoPhaseKey) => {
    if (!runResult?.run_id) return;
    setError(null);
    setIsDownloading(true);
    try {
      const blob = await downloadXToDemoArtifact(runResult.run_id, phaseKey);
      downloadBlob(blob, `${runResult.run_id}-${phaseKey}.md`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Artifact download failed");
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDownloadAllArtifacts = async () => {
    if (!runResult?.run_id) return;
    setError(null);
    setIsDownloading(true);
    try {
      const blob = await downloadXToDemoRun(runResult.run_id);
      downloadBlob(blob, `${runResult.run_id}-artifacts.zip`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bundle download failed");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="grid items-start gap-8 lg:grid-cols-[1.1fr_0.9fr]">
      <section className="relative min-w-0 overflow-hidden rounded-2xl border border-border/70 bg-card/40 p-6 backdrop-blur-sm">
        <div className="absolute right-0 top-0 h-20 w-20 bg-gradient-to-bl from-primary/20 to-transparent" />
        <header className="mb-6">
          <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Input workspace
          </p>
          <h2 className="mt-2 text-2xl font-display leading-tight">
            Feed input X into the pipeline
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Upload an Input X file or paste raw material, then run all phases or stop early for
            edits.
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

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label
                htmlFor="x-stop-after"
                className="mb-2 block text-xs uppercase tracking-[0.16em] text-muted-foreground"
              >
                Stop after phase
              </label>
              <select
                id="x-stop-after"
                value={stopAfterPhase}
                onChange={(event) => setStopAfterPhase(event.target.value as XToDemoPhaseKey)}
                className="w-full rounded-xl border border-border/70 bg-background/50 px-4 py-3 text-sm focus:border-primary focus:outline-none"
              >
                {PIPELINE_PHASES.map((phase) => (
                  <option key={phase.key} value={phase.key}>
                    {phase.title}
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

      <section className="min-w-0 rounded-2xl border border-border/70 bg-card/40 p-6 backdrop-blur-sm">
        <header className="mb-6">
          <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Pipeline output
          </p>
          <h2 className="mt-2 text-2xl font-display leading-tight">Progress and artifacts</h2>
        </header>

        <ol className="space-y-3">
          {PIPELINE_PHASES.map((phase) => {
            const isComplete = completedPhaseSet.has(phase.key);
            const isFailed = failedPhaseSet.has(phase.key);
            const isStale = stalePhaseSet.has(phase.key);
            const isActive = activePhaseKey === phase.key;
            return (
              <li
                key={phase.key}
                className={`rounded-lg border px-3 py-2 text-sm transition-all ${
                  isFailed
                    ? "border-destructive/40 bg-destructive/10"
                    : isStale
                      ? "border-amber-400/40 bg-amber-100/20"
                      : isComplete
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
            Run the pipeline to generate phase artifacts and enable review/edit/resume.
          </p>
        )}

        {runResult && (
          <div className="mt-6 space-y-4 animate-fade-up">
            <div className="rounded-xl border border-primary/30 bg-primary/10 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-primary">Run state</p>
              <p className="mt-1 break-all text-sm text-foreground">
                {runResult.run_id} • {formatTimestamp(runResult.created_at)} • {runResult.model} •{" "}
                {runResult.reasoning_effort}
              </p>
              <p className="mt-2 text-xs text-muted-foreground">
                Stop after: <code>{phaseTitle(runResult.stop_after_phase)}</code>
                {runResult.next_phase_key && (
                  <>
                    {" "}
                    • Next phase: <code>{phaseTitle(runResult.next_phase_key)}</code>
                  </>
                )}
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button type="button" variant="secondary" onClick={handleCopySpec} className="h-10">
                {copied ? "Copied" : "Copy code spec"}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={handleDownloadAllArtifacts}
                className="h-10"
                disabled={isDownloading}
              >
                {isDownloading ? "Downloading..." : "Download all artifacts"}
              </Button>
              {runResult.next_phase_key && (
                <Button type="button" onClick={handleResume} className="h-10" disabled={isResuming}>
                  {isResuming
                    ? "Resuming..."
                    : `Resume from ${phaseTitle(runResult.next_phase_key)}`}
                </Button>
              )}
            </div>

            {runResult.final_code_spec && (
              <div className="rounded-xl border border-border/60 bg-background/40 p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    Final code spec
                  </p>
                  <Button
                    type="button"
                    variant="secondary"
                    className="h-8"
                    onClick={handleExportToAIStudio}
                  >
                    Export to Google AI Studio (Mock)
                  </Button>
                </div>
                {exportMessage && (
                  <p className="mb-3 rounded border border-primary/30 bg-primary/10 px-3 py-2 text-xs text-primary">
                    {exportMessage}
                  </p>
                )}
                <pre className="max-h-[18rem] overflow-auto whitespace-pre-wrap text-xs leading-relaxed text-foreground">
                  {runResult.final_code_spec}
                </pre>
              </div>
            )}

            <div className="rounded-xl border border-border/60 bg-background/30 p-4">
              <p className="mb-3 text-xs uppercase tracking-[0.16em] text-muted-foreground">
                Artifacts
              </p>

              <div className="mb-4 flex flex-wrap gap-2">
                {PHASE_KEYS.map((phaseKey) => {
                  const artifact = runResult.artifacts.find((item) => item.phase_key === phaseKey);
                  return (
                    <button
                      key={phaseKey}
                      type="button"
                      disabled={!artifact}
                      onClick={() => setActiveArtifactTab(phaseKey)}
                      className={`rounded-lg border px-3 py-2 text-xs transition ${
                        activeArtifactTab === phaseKey
                          ? "border-primary/60 bg-primary/15 text-foreground"
                          : artifact
                            ? "border-border/70 bg-background/40 text-muted-foreground hover:border-primary/40"
                            : "cursor-not-allowed border-border/40 bg-background/20 text-muted-foreground/50"
                      }`}
                    >
                      {phaseTitle(phaseKey)}
                    </button>
                  );
                })}
              </div>

              {activeArtifact ? (
                <div className="space-y-3">
                  <div className="break-all rounded-lg border border-border/60 bg-background/40 px-3 py-2 text-xs text-muted-foreground">
                    Markdown path: <code>{activeArtifact.saved_path}</code>
                    <br />
                    JSON path: <code>{activeArtifact.json_path}</code>
                    <br />
                    Hash: <code>{activeArtifact.content_hash}</code>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      className="h-9"
                      onClick={handleSaveArtifact}
                      disabled={isSavingArtifact}
                    >
                      {isSavingArtifact ? "Saving..." : "Save JSON edits"}
                    </Button>
                    <Button
                      type="button"
                      variant="secondary"
                      className="h-9"
                      onClick={() => handleDownloadArtifact(activeArtifact.phase_key)}
                      disabled={isDownloading}
                    >
                      Download markdown
                    </Button>
                  </div>

                  <div className="grid gap-4 xl:grid-cols-2">
                    <div className="rounded-lg border border-border/60 bg-background/30 p-3">
                      <p className="mb-2 text-xs uppercase tracking-[0.14em] text-muted-foreground">
                        Markdown preview
                      </p>
                      <pre className="max-h-72 overflow-auto whitespace-pre-wrap text-xs leading-relaxed text-foreground">
                        {activeArtifact.markdown}
                      </pre>
                    </div>

                    <div className="rounded-lg border border-border/60 bg-background/30 p-3">
                      <p className="mb-2 text-xs uppercase tracking-[0.14em] text-muted-foreground">
                        Canonical JSON editor
                      </p>
                      <textarea
                        value={artifactJsonDraft}
                        onChange={(event) => setArtifactJsonDraft(event.target.value)}
                        rows={16}
                        className="w-full rounded-md border border-border/70 bg-background/60 px-3 py-2 font-mono text-xs leading-relaxed text-foreground focus:border-primary focus:outline-none"
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <p className="rounded-lg border border-border/60 bg-background/30 px-3 py-2 text-sm text-muted-foreground">
                  Select a completed phase to inspect or edit its artifact.
                </p>
              )}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
