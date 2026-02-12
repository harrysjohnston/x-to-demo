"""Artifact persistence and loading utilities for X-to-Demo pipeline phases."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.x_to_demo.renderers import render_markdown

from .models import PIPELINE_PHASES, PhaseKey, PipelineArtifact, PipelinePhaseDefinition

if TYPE_CHECKING:
    from pydantic import BaseModel


class PipelineArtifactManager:
    """Handles serialization and retrieval of per-phase outputs."""

    def __init__(self, phases: tuple[PipelinePhaseDefinition, ...] = PIPELINE_PHASES) -> None:
        self._phases = phases

    def persist_phase_output(
        self,
        *,
        run_dir: Path,
        phase: PipelinePhaseDefinition,
        output_model: BaseModel,
    ) -> PipelineArtifact:
        json_content = output_model.model_dump(mode="json")
        json_text = json.dumps(json_content, indent=2, sort_keys=True)
        markdown = render_markdown(output_model)
        content_hash = hashlib.sha256(json_text.encode("utf-8")).hexdigest()

        json_path = run_dir / f"{phase.key}.json"
        md_path = run_dir / f"{phase.key}.md"
        json_path.write_text(json_text + "\n", encoding="utf-8")
        md_path.write_text(markdown, encoding="utf-8")

        return PipelineArtifact(
            phase_key=phase.key,
            title=phase.title,
            markdown=markdown,
            saved_path=self.relative_or_absolute(md_path),
            json_path=self.relative_or_absolute(json_path),
            json_content=json_content,
            content_hash=content_hash,
        )

    @staticmethod
    def read_json_payload(run_dir: Path, phase_key: PhaseKey, json_path: str) -> dict[str, Any]:
        path = Path(json_path)
        if not path.is_absolute():
            path = run_dir / path.name
        if not path.exists():
            fallback = run_dir / f"{phase_key}.json"
            if fallback.exists():
                path = fallback
        if not path.exists():
            raise FileNotFoundError(f"JSON artifact not found for phase '{phase_key}'")

        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError(f"JSON artifact for phase '{phase_key}' must be an object")
        return payload

    def load_artifacts(self, *, run_dir: Path, manifest: dict[str, Any]) -> list[PipelineArtifact]:
        artifacts: list[PipelineArtifact] = []
        for phase in self._phases:
            record = self._phase_record(manifest, phase.key)
            status = str(record.get("status") or "pending")
            if status not in {"completed", "stale"}:
                continue

            output_json_path = record.get("output_json_path")
            output_md_path = record.get("output_md_path")
            if not isinstance(output_json_path, str) or not isinstance(output_md_path, str):
                continue

            json_payload = self.read_json_payload(run_dir, phase.key, output_json_path)

            md_path = Path(output_md_path)
            if not md_path.is_absolute():
                md_path = run_dir / md_path.name
            if not md_path.exists():
                fallback = run_dir / f"{phase.key}.md"
                if fallback.exists():
                    md_path = fallback
            if not md_path.exists():
                continue

            markdown = md_path.read_text(encoding="utf-8")
            content_hash = str(
                record.get("content_hash")
                or hashlib.sha256(
                    json.dumps(json_payload, sort_keys=True).encode("utf-8")
                ).hexdigest()
            )
            artifacts.append(
                PipelineArtifact(
                    phase_key=phase.key,
                    title=phase.title,
                    markdown=markdown,
                    saved_path=self.relative_or_absolute(md_path),
                    json_path=self.relative_or_absolute(
                        Path(output_json_path)
                        if Path(output_json_path).is_absolute()
                        else run_dir / Path(output_json_path).name
                    ),
                    json_content=json_payload,
                    content_hash=content_hash,
                )
            )
        return artifacts

    @staticmethod
    def relative_or_absolute(path: Path) -> str:
        cwd = Path.cwd()
        try:
            return str(path.relative_to(cwd))
        except ValueError:
            return str(path)

    @staticmethod
    def _phase_record(manifest: dict[str, Any], phase_key: PhaseKey) -> dict[str, Any]:
        phases = manifest.get("phases", [])
        for record in phases:
            if isinstance(record, dict) and record.get("phase_key") == phase_key:
                return record
        raise RuntimeError(f"Manifest missing phase record for '{phase_key}'")
