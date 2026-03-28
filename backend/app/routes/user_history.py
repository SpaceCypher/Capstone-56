from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    UserProgressRequest,
    UserProgressResponse,
    UserTopicDetailsResponse,
    UserTopicsResponse,
)
from app.services.user_history_service import (
    delete_topic_progress,
    get_topic_details,
    get_user_topics,
    save_or_update_progress,
)

router = APIRouter(prefix="/api/user", tags=["user-history"])


@router.post("/progress", response_model=UserProgressResponse)
async def save_user_progress(payload: UserProgressRequest) -> UserProgressResponse:
    try:
        result = await save_or_update_progress(
            user_id=payload.user_id,
            topic=payload.topic,
            evaluation=payload.evaluation,
            learning_plan=payload.learning_plan,
            questions=payload.questions,
            responses=payload.responses,
        )
        return UserProgressResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to save user progress") from exc


@router.get("/topics/{user_id}", response_model=UserTopicsResponse)
async def list_user_topics(user_id: str) -> UserTopicsResponse:
    try:
        topics = await get_user_topics(user_id)
        return UserTopicsResponse(topics=topics)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch user topics") from exc


@router.get("/topic/{user_id}/{topic}", response_model=UserTopicDetailsResponse)
async def get_user_topic(user_id: str, topic: str) -> UserTopicDetailsResponse:
    try:
        topic_details = await get_topic_details(user_id, topic)
        if topic_details is None:
            raise HTTPException(status_code=404, detail="Topic history not found")
        return topic_details
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch topic details") from exc


@router.delete("/topic/{user_id}/{topic}")
async def delete_user_topic(user_id: str, topic: str) -> dict[str, str]:
    try:
        deleted = await delete_topic_progress(user_id, topic)
        if not deleted:
            raise HTTPException(status_code=404, detail="Topic history not found")
        return {
            "message": "Topic history removed",
            "topic": topic,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to delete topic history") from exc
