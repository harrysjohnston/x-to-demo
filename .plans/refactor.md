Refactor goals recap
	1.	Strip unnecessary code / reduce surface area.
	2.	Modularise x-to-demo pipeline (phases as composable units).
	3.	OpenAI calls use Structured Outputs with Pydantic (remove current validation/warning routines).  ￼
	4.	Pydantic models are the single source of truth for output schemas; prompts “read” from those models.
	5.	Allow partial pipeline execution: “run up to phase N”.
	6.	Frontend renders markdown artefacts for inspection + edit.
	7.	Resume pipeline after edits (phase N depends on edited artefact N-1).
	8.	Download each/all markdown artefacts.
	9.	Mock “Export to Google AI Studio” button for the final (demo-to-code-spec) artefact.

⸻

Proposed target architecture

A. Pipeline as a typed DAG (but linear by default)

Even if you keep it linear (Phase 1 → 2 → 3), structure it as a small DAG engine where each phase declares:
	•	key (e.g. feature_spec, demo_spec, code_spec)
	•	input_types (Pydantic model(s) it expects)
	•	output_type (Pydantic model it produces)
	•	prompt_builder(model_schema) (renders instruction strings + examples)
	•	runner(openai_client, input_model) -> output_model

This matches the “fixed multi-phase pipeline” reality today  ￼ but makes partial execution + resume natural.

B. Store canonical artefacts as JSON + render Markdown views

Right now artefacts are persisted as markdown files per phase  ￼. Keep markdown for humans, but make the canonical persisted form the structured JSON (the Pydantic model dump). Then derive markdown from that JSON deterministically.
	•	Canonical: artifacts/<run_id>/<phase_key>.json
	•	Human view: artifacts/<run_id>/<phase_key>.md (generated)
	•	Manifest ties it all together (run-manifest.json already exists)  ￼

This enables “edit markdown” while still resuming reliably:
	•	User edits markdown → API parses/validates into model (or edits JSON directly) → regenerate markdown → resume.

⸻

Step-by-step implementation plan

Phase 0 — “Strip unnecessary code” (2 passes: delete, then simplify)

Pass 1: Identify what’s not needed for the refactor demo
Based on current state, the prototype includes production-ish infra (Terraform, email templates, storage providers, JWT refresh rotation, etc.)  ￼. For the refactor, decide what stays “in demo path” vs “kept but ignored”.

Recommended keep (minimal demo path):
	•	Web: XToDemoStudio, auth (or simple dev auth), SSE progress, artefact viewer/editor.
	•	API: x-to-demo run endpoint, SSE, artefact persistence, OpenAI client wrapper, settings.
	•	DB: optional. If you already need it for users/runs, keep; otherwise you can run artefacts on disk and store minimal run index.

Recommended de-emphasize / fence off:
	•	Email flows/templates
	•	Multiple cloud storage providers
	•	Terraform modules
	•	Heavy auth complexity if not needed for demo

Pass 2: Consolidate configuration
Settings currently include many X_TO_DEMO knobs  ￼. Collapse to:
	•	OPENAI_API_KEY
	•	X_TO_DEMO_MODEL
	•	X_TO_DEMO_OUTPUT_DIR
	•	(optional) X_TO_DEMO_MAX_INPUT_CHARS

Everything else can be “advanced” later.

Deliverable: a short “supported” subset and delete dead code paths.

⸻

Phase 1 — Introduce Pydantic schemas as the source of truth

1. Create schema module
Add something like:
	•	apps/api/app/x_to_demo/schemas/
	•	feature_spec.py
	•	demo_spec.py
	•	code_spec.py
	•	common.py (Version/Status, citations, etc.)

Keep models small but explicit.

2. Make markdown rendering deterministic
Implement render_markdown(model: BaseModel) -> str per artefact type.
	•	Prefer a single renderer per model so section order is stable.
	•	This replaces “required headings checks” and “banned pattern checks”  ￼ because the renderer controls the format.

3. Structured Outputs in OpenAI calls
Replace your current “prompt → markdown with embedded JSON → parse → warnings/normalise” with:
	•	OpenAI Responses API call that returns structured JSON matching the Pydantic schema.
	•	Parse/validate via Pydantic only.
	•	Save model_dump().

Result: no “warning routines”; validation becomes “Pydantic or fail”.

⸻

Phase 2 — Modular pipeline + partial execution

1. Create a phase interface
Example shape (conceptually):
	•	Phase[I, O]
	•	key: str
	•	input_model: type[I]
	•	output_model: type[O]
	•	run(ctx, input: I) -> O

2. Orchestrator supports stop_after
Update POST /x-to-demo/runs request to include:
	•	stop_after_phase: "feature_spec" | "demo_spec" | "code_spec" (or numeric)
	•	Or phases: ["feature_spec", "demo_spec"]

3. Persist outputs after each phase
You already write per-phase markdown and a manifest  ￼; extend manifest to record:
	•	phase_key
	•	status
	•	input_artifact_ref (what it consumed)
	•	output_json_path
	•	output_md_path
	•	hash (content hash for resume sanity)

4. Resume semantics
Add endpoint:
	•	POST /x-to-demo/runs/{run_id}/resume
Body:
	•	from_phase (defaults to next incomplete)
	•	stop_after_phase
	•	use_edited_artifacts: true

Or: allow POST /runs to accept base_run_id + “start at phase N”.

⸻

Phase 3 — Frontend: markdown inspection + edit + download

1. Artefact viewer/editor
In the run results page:
	•	Tabs per phase artefact.
	•	Render markdown (read-only) + toggle to edit.
	•	On save: PUT /runs/{run_id}/artifacts/{phase_key} with markdown payload.

2. Server-side parse + validate
On save:
	•	Parse markdown back into the Pydantic model.
	•	Easiest: don’t parse arbitrary markdown; instead render markdown with a hidden JSON block or frontmatter that is the real data.
	•	Recommended format:
	•	Markdown is mostly human-friendly.
	•	At bottom: an HTML comment or fenced block containing canonical JSON:
	•




	•	{ …canonical schema… }
	•




	•	On edit, you can either:
	•	Allow editing only markdown sections but keep JSON block read-only, or
	•	Treat JSON as canonical and let the editor expose a JSON panel.

Given “Pydantic single source of truth”, the cleanest: edit the JSON (form or JSON editor), regenerate markdown instantly.

3. Download
Add:
	•	Download a single artefact: /runs/{run_id}/artifacts/{phase_key}.md
	•	Download all artefacts: /runs/{run_id}/artifacts.zip (md + json + manifest)

4. “Export to Google AI Studio” button (mock)
For the final artefact (code_spec):
	•	Button copies the final markdown to clipboard and shows a modal:
	•	“Paste into Google AI Studio” + optional fields
	•	Or button downloads a .txt/.md named ai-studio-prompt.md
	•	Keep it mock: no OAuth.

⸻

Prompt generation “from Pydantic models”

To make prompts “read from models” without being gimmicky:
	1.	Each model has:
	•	Field descriptions (Field(description="..."))
	•	Optional examples
	2.	Prompt builder uses:
	•	Model name + high-level instructions
	•	JSON schema excerpt (or a compact field list)
	•	A “return JSON only matching this schema” rule

This keeps the schema authoritative and avoids drift.

⸻

Concrete API surface changes

Existing (today)
	•	POST /api/v1/x-to-demo/runs runs full pipeline, returns artefacts, SSE progress  ￼

Add / change
	1.	POST /api/v1/x-to-demo/runs
	•	add stop_after_phase (or phases)
	2.	GET /api/v1/x-to-demo/runs/{run_id}
	•	returns manifest + artefact metadata + current statuses
	3.	GET /api/v1/x-to-demo/runs/{run_id}/artifacts/{phase_key}
	•	returns markdown + json (or references)
	4.	PUT /api/v1/x-to-demo/runs/{run_id}/artifacts/{phase_key}
	•	accepts edited markdown/json, validates via Pydantic, regenerates derived markdown
	5.	POST /api/v1/x-to-demo/runs/{run_id}/resume
	•	resumes from next incomplete or specified phase
	6.	GET /api/v1/x-to-demo/runs/{run_id}/download
	•	zip of all artefacts

⸻

SSE adjustments

You already emit run/phase started/completed/failed events  ￼. Extend payload to include:
	•	artifact_version (hash)
	•	artifact_paths (md/json)
	•	is_resume: bool
	•	source_edit: { phase_key, edited_at } | null

This will let the UI show “resumed after edits”.

⸻

Suggested delivery milestones (so it stays shippable)
	1.	M1 — Schema + Structured Outputs
	•	Pydantic models for all phases
	•	OpenAI calls return validated model JSON
	•	Render markdown from model
	2.	M2 — Modular orchestrator + stop-after
	•	Partial runs
	•	Manifest updated
	3.	M3 — Edit + resume
	•	UI editor for artefacts
	•	PUT artefact + validate + resume
	4.	M4 — Downloads + mock export button
	•	Download single/all
	•	AI Studio mock export UX
