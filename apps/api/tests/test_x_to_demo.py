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

    def run(
        self,
        *,
        x_input: str,
        additional_context: str | None,
        feature_name_hint: str | None,
        user_id: int,
        model: str | None = None,
        reasoning_effort: str | None = None,
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
            }
        )
        artifacts = [
            PipelineArtifact(
                phase_key="phase-1-input-to-feature-spec",
                title="Phase 1",
                markdown="# Phase 1",
                saved_path="artifacts/x-to-demo/run-1/01-phase-1-input-to-feature-spec.md",
            ),
            PipelineArtifact(
                phase_key="phase-3-demo-spec-to-code-spec",
                title="Phase 3",
                markdown="# Final code spec",
                saved_path="artifacts/x-to-demo/run-1/03-phase-3-demo-spec-to-code-spec.md",
            ),
        ]
        return PipelineRunResult(
            run_id="run-1",
            created_at=datetime(2026, 2, 10, tzinfo=UTC),
            model=model or "gpt-5.1",
            reasoning_effort=reasoning_effort or "low",
            artifacts=artifacts,
            final_code_spec=artifacts[-1].markdown,
            final_code_spec_path=artifacts[-1].saved_path,
            usage_totals={"input_tokens": 42, "output_tokens": 13, "total_tokens": 55},
            cost_totals={"total_cost": 0.000123},
        )


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
        },
    )
    assert response.status_code == 201

    envelope = response.json()
    data = envelope["data"]
    assert data["run_id"] == "run-1"
    assert data["model"] == "gpt-5.2"
    assert data["reasoning_effort"] == "xhigh"
    assert (
        data["final_code_spec_path"]
        == "artifacts/x-to-demo/run-1/03-phase-3-demo-spec-to-code-spec.md"
    )
    assert len(data["artifacts"]) == 2
    assert fake_pipeline_service.calls
    assert fake_pipeline_service.calls[0]["feature_name_hint"] == "Meeting Notes to Demo"
    assert fake_pipeline_service.calls[0]["model"] == "gpt-5.2"
    assert fake_pipeline_service.calls[0]["reasoning_effort"] == "xhigh"


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
