"""Tests for X-to-Demo pipeline endpoints."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import x_to_demo
from app.services.x_to_demo_pipeline import PipelineArtifact, PipelineRunResult


class FakePipelineService:
    """Deterministic pipeline fake for API router tests."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.resume_calls: list[dict[str, object]] = []
        self.update_calls: list[dict[str, object]] = []

    @staticmethod
    def _artifacts() -> list[PipelineArtifact]:
        return [
            PipelineArtifact(
                phase_key="feature_spec",
                title="Phase 1",
                markdown="# Phase 1",
                saved_path="artifacts/x-to-demo/run-1/feature_spec.md",
                json_path="artifacts/x-to-demo/run-1/feature_spec.json",
                json_content={"feature_name": "Feature", "phase": 1},
                content_hash="abc123",
            ),
            PipelineArtifact(
                phase_key="code_spec",
                title="Phase 3",
                markdown="# Final code spec",
                saved_path="artifacts/x-to-demo/run-1/code_spec.md",
                json_path="artifacts/x-to-demo/run-1/code_spec.json",
                json_content={"feature_name": "Feature", "phase": 3},
                content_hash="def456",
            ),
        ]

    def _result(
        self,
        *,
        model: str = "gpt-5.1",
        reasoning_effort: str = "low",
        stop_after_phase: str = "code_spec",
        next_phase_key: str | None = None,
    ) -> PipelineRunResult:
        artifacts = self._artifacts()
        return PipelineRunResult(
            run_id="run-1",
            created_at=datetime(2026, 2, 10, tzinfo=UTC),
            model=model,
            reasoning_effort=reasoning_effort,
            stop_after_phase=stop_after_phase,  # type: ignore[arg-type]
            next_phase_key=next_phase_key,  # type: ignore[arg-type]
            artifacts=artifacts,
            final_code_spec=artifacts[-1].markdown,
            final_code_spec_path=artifacts[-1].saved_path,
            usage_totals={"input_tokens": 42, "output_tokens": 13, "total_tokens": 55},
            cost_totals={"total_cost": 0.000123},
        )

    def run(
        self,
        *,
        x_input: str,
        additional_context: str | None,
        feature_name_hint: str | None,
        user_id: int,
        model: str | None = None,
        reasoning_effort: str | None = None,
        stop_after_phase: str | None = None,
    ) -> PipelineRunResult:
        if not x_input.strip():
            raise ValueError("Input X cannot be empty")

        self.calls.append(
            {
                "x_input": x_input,
                "additional_context": additional_context,
                "feature_name_hint": feature_name_hint,
                "user_id": user_id,
                "model": model,
                "reasoning_effort": reasoning_effort,
                "stop_after_phase": stop_after_phase,
            }
        )

        return self._result(
            model=model or "gpt-5.1",
            reasoning_effort=reasoning_effort or "low",
            stop_after_phase=stop_after_phase or "code_spec",
        )

    def get_run_manifest(self, *, run_id: str) -> dict[str, object]:
        if run_id != "run-1":
            raise FileNotFoundError("Run not found")
        return {
            "run_id": "run-1",
            "created_at": "2026-02-10T00:00:00+00:00",
            "updated_at": "2026-02-10T00:10:00+00:00",
            "phases": [
                {
                    "phase_key": "feature_spec",
                    "title": "Phase 1",
                    "status": "completed",
                    "input_artifact_ref": None,
                    "output_json_path": "artifacts/x-to-demo/run-1/feature_spec.json",
                    "output_md_path": "artifacts/x-to-demo/run-1/feature_spec.md",
                    "content_hash": "abc123",
                    "error": None,
                },
                {
                    "phase_key": "demo_spec",
                    "title": "Phase 2",
                    "status": "pending",
                    "input_artifact_ref": "feature_spec",
                    "output_json_path": None,
                    "output_md_path": None,
                    "content_hash": None,
                    "error": None,
                },
                {
                    "phase_key": "code_spec",
                    "title": "Phase 3",
                    "status": "pending",
                    "input_artifact_ref": "demo_spec",
                    "output_json_path": None,
                    "output_md_path": None,
                    "content_hash": None,
                    "error": None,
                },
            ],
        }

    def get_run_result(self, *, run_id: str) -> PipelineRunResult:
        if run_id != "run-1":
            raise FileNotFoundError("Run not found")
        return self._result(next_phase_key="demo_spec", stop_after_phase="feature_spec")

    def get_artifact(self, *, run_id: str, phase_key: str) -> PipelineArtifact:
        if run_id != "run-1":
            raise FileNotFoundError("Run not found")
        for artifact in self._artifacts():
            if artifact.phase_key == phase_key:
                return artifact
        raise FileNotFoundError("Artifact not found")

    def update_artifact(
        self,
        *,
        run_id: str,
        phase_key: str,
        markdown: str | None,
        json_content: dict[str, object] | None,
    ) -> PipelineArtifact:
        if run_id != "run-1":
            raise FileNotFoundError("Run not found")
        self.update_calls.append(
            {
                "run_id": run_id,
                "phase_key": phase_key,
                "markdown": markdown,
                "json_content": json_content,
            }
        )
        artifact = self.get_artifact(run_id=run_id, phase_key=phase_key)
        return PipelineArtifact(
            phase_key=artifact.phase_key,
            title=artifact.title,
            markdown=artifact.markdown,
            saved_path=artifact.saved_path,
            json_path=artifact.json_path,
            json_content=json_content or artifact.json_content,
            content_hash="updated-hash",
        )

    def resume(
        self,
        *,
        run_id: str,
        user_id: int,
        from_phase: str | None = None,
        stop_after_phase: str | None = None,
        use_edited_artifacts: bool = True,
    ) -> PipelineRunResult:
        if run_id != "run-1":
            raise FileNotFoundError("Run not found")
        self.resume_calls.append(
            {
                "run_id": run_id,
                "user_id": user_id,
                "from_phase": from_phase,
                "stop_after_phase": stop_after_phase,
                "use_edited_artifacts": use_edited_artifacts,
            }
        )
        return self._result(stop_after_phase=stop_after_phase or "code_spec", next_phase_key=None)

    def build_run_download_archive(self, *, run_id: str) -> bytes:
        if run_id != "run-1":
            raise FileNotFoundError("Run not found")
        return b"PK-test-zip"


@pytest.fixture(name="fake_pipeline_service")
def fake_pipeline_service_fixture() -> FakePipelineService:
    return FakePipelineService()


@pytest.fixture(name="client_with_fake_pipeline")
def client_with_fake_pipeline_fixture(
    client: TestClient, fake_pipeline_service: FakePipelineService
) -> TestClient:
    app.dependency_overrides[x_to_demo.get_pipeline_service] = lambda: fake_pipeline_service
    yield client
    app.dependency_overrides.pop(x_to_demo.get_pipeline_service, None)


def test_x_to_demo_run_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/api/v1/x-to-demo/runs",
        json={"x_input": "This input has enough content to satisfy validation."},
    )
    assert response.status_code == 401


def test_x_to_demo_run_success(
    client_with_fake_pipeline: TestClient,
    auth_headers: dict[str, str],
    fake_pipeline_service: FakePipelineService,
) -> None:
    response = client_with_fake_pipeline.post(
        "/api/v1/x-to-demo/runs",
        headers=auth_headers,
        json={
            "x_input": (
                "Team discussed that users lose track of follow-ups after meetings, "
                "and they need a faster way to turn notes into executable demo specs."
            ),
            "additional_context": "Prototype must stay frontend-only.",
            "feature_name_hint": "Meeting Notes to Demo",
            "model": "gpt-5.2",
            "reasoning_effort": "xhigh",
            "stop_after_phase": "code_spec",
        },
    )
    assert response.status_code == 201

    envelope = response.json()
    data = envelope["data"]
    assert data["run_id"] == "run-1"
    assert data["model"] == "gpt-5.2"
    assert data["reasoning_effort"] == "xhigh"
    assert data["final_code_spec_path"] == "artifacts/x-to-demo/run-1/code_spec.md"
    assert len(data["artifacts"]) == 2
    assert fake_pipeline_service.calls
    assert fake_pipeline_service.calls[0]["feature_name_hint"] == "Meeting Notes to Demo"
    assert fake_pipeline_service.calls[0]["model"] == "gpt-5.2"
    assert fake_pipeline_service.calls[0]["reasoning_effort"] == "xhigh"
    assert fake_pipeline_service.calls[0]["stop_after_phase"] == "code_spec"


def test_x_to_demo_run_rejects_blank_input(
    client_with_fake_pipeline: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client_with_fake_pipeline.post(
        "/api/v1/x-to-demo/runs",
        headers=auth_headers,
        json={"x_input": " " * 24},
    )
    assert response.status_code == 400
    assert response.json()["error"]["message"] == "Input X cannot be empty"


def test_x_to_demo_get_run_detail_success(
    client_with_fake_pipeline: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client_with_fake_pipeline.get("/api/v1/x-to-demo/runs/run-1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["run_id"] == "run-1"
    assert data["next_phase_key"] == "demo_spec"
    assert len(data["phases"]) == 3


def test_x_to_demo_update_artifact_success(
    client_with_fake_pipeline: TestClient,
    auth_headers: dict[str, str],
    fake_pipeline_service: FakePipelineService,
) -> None:
    response = client_with_fake_pipeline.put(
        "/api/v1/x-to-demo/runs/run-1/artifacts/feature_spec",
        headers=auth_headers,
        json={"json_content": {"feature_name": "Edited Feature"}},
    )
    assert response.status_code == 200
    assert fake_pipeline_service.update_calls
    assert fake_pipeline_service.update_calls[0]["phase_key"] == "feature_spec"


def test_x_to_demo_resume_success(
    client_with_fake_pipeline: TestClient,
    auth_headers: dict[str, str],
    fake_pipeline_service: FakePipelineService,
) -> None:
    response = client_with_fake_pipeline.post(
        "/api/v1/x-to-demo/runs/run-1/resume",
        headers=auth_headers,
        json={"from_phase": "demo_spec", "stop_after_phase": "code_spec"},
    )
    assert response.status_code == 200
    assert fake_pipeline_service.resume_calls
    assert fake_pipeline_service.resume_calls[0]["from_phase"] == "demo_spec"


def test_x_to_demo_download_artifact_and_bundle(
    client_with_fake_pipeline: TestClient,
    auth_headers: dict[str, str],
) -> None:
    artifact_response = client_with_fake_pipeline.get(
        "/api/v1/x-to-demo/runs/run-1/artifacts/feature_spec/download",
        headers=auth_headers,
    )
    assert artifact_response.status_code == 200
    assert artifact_response.headers["content-type"].startswith("text/markdown")

    bundle_response = client_with_fake_pipeline.get(
        "/api/v1/x-to-demo/runs/run-1/download",
        headers=auth_headers,
    )
    assert bundle_response.status_code == 200
    assert bundle_response.headers["content-type"].startswith("application/zip")
