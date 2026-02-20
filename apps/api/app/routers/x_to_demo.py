"""X-to-Demo pipeline endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth import get_current_user
from app.schemas import (
    ResponseEnvelope,
    XToDemoArtifact,
    XToDemoArtifactResponse,
    XToDemoResumeRequest,
    XToDemoRunDetailResponse,
    XToDemoRunRequest,
    XToDemoRunResponse,
    XToDemoUpdateArtifactRequest,
)
from app.services.x_to_demo_pipeline import (
    PhaseKey,
    PipelineArtifact,
    PipelineRunResult,
    XToDemoPipelineService,
    get_x_to_demo_pipeline_service,
)

if TYPE_CHECKING:
    from app.models import User

router = APIRouter(prefix="/x-to-demo", tags=["x-to-demo"])


def get_pipeline_service() -> XToDemoPipelineService:
    """Resolve pipeline service and expose dependency errors as 503s."""
    try:
        return get_x_to_demo_pipeline_service()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


def _validate_phase_key(phase_key: str) -> PhaseKey:
    if phase_key not in {"feature_spec", "demo_spec", "code_spec"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported phase key. Use one of: feature_spec, demo_spec, code_spec",
        )
    return phase_key  # type: ignore[return-value]


def _artifact_to_schema(artifact: PipelineArtifact) -> XToDemoArtifact:
    return XToDemoArtifact(
        phase_key=artifact.phase_key,
        title=artifact.title,
        markdown=artifact.markdown,
        saved_path=artifact.saved_path,
        json_path=artifact.json_path,
        xml_path=artifact.xml_path,
        json_content=artifact.json_content,
        content_hash=artifact.content_hash,
    )


def _run_result_to_schema(result: PipelineRunResult) -> XToDemoRunResponse:
    return XToDemoRunResponse(
        run_id=result.run_id,
        created_at=result.created_at,
        model=result.model,
        reasoning_effort=result.reasoning_effort,
        artifacts=[_artifact_to_schema(artifact) for artifact in result.artifacts],
        final_code_spec=result.final_code_spec,
        final_code_spec_path=result.final_code_spec_path,
        stop_after_phase=result.stop_after_phase,
        next_phase_key=result.next_phase_key,
        usage_totals=result.usage_totals,
        cost_totals=result.cost_totals,
    )


@router.post(
    "/runs",
    response_model=ResponseEnvelope[XToDemoRunResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_x_to_demo_run(
    request: XToDemoRunRequest,
    current_user: User = Depends(get_current_user),
    pipeline_service: XToDemoPipelineService = Depends(get_pipeline_service),
) -> ResponseEnvelope[XToDemoRunResponse]:
    """Run the X-to-Demo pipeline and return generated artifacts."""
    try:
        result = pipeline_service.run(
            x_input=request.x_input,
            additional_context=request.additional_context,
            feature_name_hint=request.feature_name_hint,
            user_id=current_user.id or 0,
            model=request.model,
            reasoning_effort=request.reasoning_effort,
            stop_after_phase=request.stop_after_phase,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Pipeline execution failed: {exc}",
        ) from exc

    return ResponseEnvelope(data=_run_result_to_schema(result))


@router.get(
    "/runs/{run_id}",
    response_model=ResponseEnvelope[XToDemoRunDetailResponse],
)
def get_x_to_demo_run(
    run_id: str,
    _current_user: User = Depends(get_current_user),
    pipeline_service: XToDemoPipelineService = Depends(get_pipeline_service),
) -> ResponseEnvelope[XToDemoRunDetailResponse]:
    """Fetch run manifest and current artifact status."""
    try:
        manifest = pipeline_service.get_run_manifest(run_id=run_id)
        result = pipeline_service.get_run_result(run_id=run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    phases = manifest.get("phases")
    if not isinstance(phases, list):
        phases = []

    updated_at_raw = manifest.get("updated_at")
    updated_at = result.created_at
    if isinstance(updated_at_raw, str):
        updated_at = datetime.fromisoformat(updated_at_raw.replace("Z", "+00:00"))

    detail = XToDemoRunDetailResponse(
        run_id=result.run_id,
        created_at=result.created_at,
        updated_at=updated_at,
        model=result.model,
        reasoning_effort=result.reasoning_effort,
        stop_after_phase=result.stop_after_phase,
        next_phase_key=result.next_phase_key,
        phases=[
            {
                "phase_key": phase.get("phase_key"),
                "title": phase.get("title"),
                "status": phase.get("status"),
                "input_artifact_ref": phase.get("input_artifact_ref"),
                "output_json_path": phase.get("output_json_path"),
                "output_xml_path": phase.get("output_xml_path"),
                "output_md_path": phase.get("output_md_path"),
                "content_hash": phase.get("content_hash"),
                "error": phase.get("error"),
            }
            for phase in phases
            if isinstance(phase, dict)
        ],
        artifacts=[_artifact_to_schema(artifact) for artifact in result.artifacts],
        usage_totals=result.usage_totals,
        cost_totals=result.cost_totals,
    )
    return ResponseEnvelope(data=detail)


@router.get(
    "/runs/{run_id}/artifacts/{phase_key}",
    response_model=ResponseEnvelope[XToDemoArtifactResponse],
)
def get_x_to_demo_artifact(
    run_id: str,
    phase_key: str,
    _current_user: User = Depends(get_current_user),
    pipeline_service: XToDemoPipelineService = Depends(get_pipeline_service),
) -> ResponseEnvelope[XToDemoArtifactResponse]:
    """Fetch a single phase artifact in markdown + canonical JSON form."""
    resolved_phase = _validate_phase_key(phase_key)
    try:
        artifact = pipeline_service.get_artifact(run_id=run_id, phase_key=resolved_phase)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ResponseEnvelope(
        data=XToDemoArtifactResponse(
            run_id=run_id,
            artifact=_artifact_to_schema(artifact),
        )
    )


@router.put(
    "/runs/{run_id}/artifacts/{phase_key}",
    response_model=ResponseEnvelope[XToDemoArtifactResponse],
)
def update_x_to_demo_artifact(
    run_id: str,
    phase_key: str,
    request: XToDemoUpdateArtifactRequest,
    _current_user: User = Depends(get_current_user),
    pipeline_service: XToDemoPipelineService = Depends(get_pipeline_service),
) -> ResponseEnvelope[XToDemoArtifactResponse]:
    """Validate and persist edited artifact content."""
    resolved_phase = _validate_phase_key(phase_key)
    try:
        artifact = pipeline_service.update_artifact(
            run_id=run_id,
            phase_key=resolved_phase,
            markdown=request.markdown,
            json_content=request.json_content,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ResponseEnvelope(
        data=XToDemoArtifactResponse(
            run_id=run_id,
            artifact=_artifact_to_schema(artifact),
        )
    )


@router.post(
    "/runs/{run_id}/resume",
    response_model=ResponseEnvelope[XToDemoRunResponse],
)
def resume_x_to_demo_run(
    run_id: str,
    request: XToDemoResumeRequest,
    current_user: User = Depends(get_current_user),
    pipeline_service: XToDemoPipelineService = Depends(get_pipeline_service),
) -> ResponseEnvelope[XToDemoRunResponse]:
    """Resume a run from next incomplete (or selected) phase."""
    try:
        result = pipeline_service.resume(
            run_id=run_id,
            user_id=current_user.id or 0,
            from_phase=request.from_phase,
            stop_after_phase=request.stop_after_phase,
            use_edited_artifacts=request.use_edited_artifacts,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Pipeline resume failed: {exc}",
        ) from exc

    return ResponseEnvelope(data=_run_result_to_schema(result))


@router.get("/runs/{run_id}/artifacts/{phase_key}/download")
def download_x_to_demo_artifact(
    run_id: str,
    phase_key: str,
    _current_user: User = Depends(get_current_user),
    pipeline_service: XToDemoPipelineService = Depends(get_pipeline_service),
) -> Response:
    """Download a single artifact markdown file."""
    resolved_phase = _validate_phase_key(phase_key)
    try:
        artifact = pipeline_service.get_artifact(run_id=run_id, phase_key=resolved_phase)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    filename = f"{run_id}-{resolved_phase}.md"
    return Response(
        content=artifact.markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/runs/{run_id}/download")
def download_x_to_demo_run(
    run_id: str,
    _current_user: User = Depends(get_current_user),
    pipeline_service: XToDemoPipelineService = Depends(get_pipeline_service),
) -> Response:
    """Download all artifacts + manifest for a run as zip."""
    try:
        archive_bytes = pipeline_service.build_run_download_archive(run_id=run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return Response(
        content=archive_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{run_id}-artifacts.zip"'},
    )
