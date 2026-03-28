from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    DiagnosticAnalyzeRequest,
    DiagnosticAnalyzeResponse,
    DiagnosticGenerateRequest,
    DiagnosticGenerateResponse,
)
from app.services.diagnostic_service import (
    LLMRateLimitError,
    LLMServiceError,
    generate_questions,
    orchestrate_full_flow,
)
from app.services.user_history_service import save_or_update_progress

router = APIRouter(prefix="/api/diagnostic", tags=["diagnostic"])


def _looks_like_rate_limit(message: str) -> bool:
    lowered = message.lower()
    return "429" in lowered or "too many requests" in lowered or "rate limit" in lowered


@router.post("/generate", response_model=DiagnosticGenerateResponse)
async def generate_diagnostic_questions(payload: DiagnosticGenerateRequest) -> DiagnosticGenerateResponse:
    try:
        return await generate_questions(payload.topic)
    except LLMRateLimitError as exc:
        headers: dict[str, str] | None = None
        if exc.retry_after is not None:
            headers = {"Retry-After": str(max(1, int(exc.retry_after)))}
        raise HTTPException(status_code=429, detail=str(exc), headers=headers) from exc
    except LLMServiceError as exc:
        if _looks_like_rate_limit(str(exc)):
            raise HTTPException(status_code=429, detail="AI provider is rate-limiting requests. Please retry shortly.") from exc
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to generate diagnostic questions") from exc


@router.post("/analyze", response_model=DiagnosticAnalyzeResponse)
async def analyze_diagnostic_responses(payload: DiagnosticAnalyzeRequest) -> DiagnosticAnalyzeResponse:
    try:
        user_id = payload.user_id or "anonymous"
        evaluation, learning_plan, _record_id, stage_sources, stage_reasons, ai_source = await orchestrate_full_flow(
            topic=payload.topic,
            responses=payload.responses,
            user_id=user_id,
        )
        await save_or_update_progress(
            user_id=user_id,
            topic=payload.topic,
            evaluation=evaluation,
            learning_plan=learning_plan,
            questions=[
                {
                    "id": item.question_id,
                    "type": "submitted",
                    "question": item.question,
                }
                for item in payload.responses
            ],
            responses=[item.model_dump(mode="json") for item in payload.responses],
        )
        return DiagnosticAnalyzeResponse(
            evaluation=evaluation,
            learning_plan=learning_plan,
            ai_source=ai_source,
            stage_sources=stage_sources,
            stage_reasons=stage_reasons,
        )
    except LLMRateLimitError as exc:
        headers: dict[str, str] | None = None
        if exc.retry_after is not None:
            headers = {"Retry-After": str(max(1, int(exc.retry_after)))}
        raise HTTPException(status_code=429, detail=str(exc), headers=headers) from exc
    except LLMServiceError as exc:
        if _looks_like_rate_limit(str(exc)):
            raise HTTPException(status_code=429, detail="AI provider is rate-limiting requests. Please retry shortly.") from exc
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to analyze diagnostic responses") from exc
