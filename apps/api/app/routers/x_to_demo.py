"""X-to-Demo pipeline endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.models import User
from app.schemas import ResponseEnvelope, XToDemoArtifact, XToDemoRunRequest, XToDemoRunResponse
from app.services.x_to_demo_pipeline import XToDemoPipelineService, get_x_to_demo_pipeline_service

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
    """Run the 3-phase X-to-Demo pipeline and return generated artifacts."""
    try:
        result = pipeline_service.run(
            x_input=request.x_input,
            additional_context=request.additional_context,
            feature_name_hint=request.feature_name_hint,
            user_id=current_user.id or 0,
            model=request.model,
            reasoning_effort=request.reasoning_effort,
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

    response_payload = XToDemoRunResponse(
        run_id=result.run_id,
        created_at=result.created_at,
        model=result.model,
        reasoning_effort=result.reasoning_effort,
        artifacts=[
            XToDemoArtifact(
                phase_key=artifact.phase_key,
                title=artifact.title,
                markdown=artifact.markdown,
                saved_path=artifact.saved_path,
            )
            for artifact in result.artifacts
        ],
        final_code_spec=result.final_code_spec,
        final_code_spec_path=result.final_code_spec_path,
    )

    return ResponseEnvelope(data=response_payload)
