from datetime import UTC, datetime
from typing import Any

from app.db.mongo import get_database
from app.models.schemas import EvaluationResult, LearningPlanResult, UserTopicDetailsResponse


def calculate_progress(evaluation: EvaluationResult) -> float:
    mapping = {
        "beginner": 0.3,
        "intermediate": 0.6,
        "advanced": 0.9,
    }
    return float(mapping.get(evaluation.level.value, 0.3))


async def init_user_history_indexes() -> None:
    collection = get_database()["user_learning_history"]
    await collection.create_index([("user_id", 1)], unique=True)
    await collection.create_index([("user_id", 1), ("topics.topic", 1)])


async def save_or_update_progress(
    user_id: str,
    topic: str,
    evaluation: EvaluationResult,
    learning_plan: LearningPlanResult,
    questions: list[dict[str, Any]] | None = None,
    responses: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    collection = get_database()["user_learning_history"]

    now = datetime.now(UTC)
    normalized_topic = topic.strip()
    progress = calculate_progress(evaluation)

    history_item = {
        "questions": questions or [],
        "responses": responses or [],
        "evaluation": evaluation.model_dump(mode="json"),
        "timestamp": now,
    }

    update_existing_result = await collection.update_one(
        {
            "user_id": user_id,
            "topics.topic": normalized_topic,
        },
        {
            "$set": {
                "topics.$.level": evaluation.level.value,
                "topics.$.strengths": evaluation.strengths,
                "topics.$.weaknesses": evaluation.weaknesses,
                "topics.$.misconceptions": evaluation.misconceptions,
                "topics.$.progress": progress,
                "topics.$.last_updated": now,
                "topics.$.learning_plan": learning_plan.model_dump(mode="json"),
            },
            "$push": {
                "topics.$.diagnostic_history": history_item,
            },
        },
    )

    if update_existing_result.matched_count == 0:
        topic_entry = {
            "topic": normalized_topic,
            "level": evaluation.level.value,
            "strengths": evaluation.strengths,
            "weaknesses": evaluation.weaknesses,
            "misconceptions": evaluation.misconceptions,
            "progress": progress,
            "last_updated": now,
            "learning_plan": learning_plan.model_dump(mode="json"),
            "diagnostic_history": [history_item],
        }

        await collection.update_one(
            {
                "user_id": user_id,
                "topics.topic": {"$ne": normalized_topic},
            },
            {
                "$setOnInsert": {"user_id": user_id},
                "$push": {"topics": topic_entry},
            },
            upsert=True,
        )

    return {
        "user_id": user_id,
        "topic": normalized_topic,
        "progress": progress,
        "level": evaluation.level,
        "last_updated": now.isoformat(),
        "message": "Topic progress saved",
    }


async def get_user_topics(user_id: str) -> list[dict[str, Any]]:
    collection = get_database()["user_learning_history"]
    doc = await collection.find_one(
        {"user_id": user_id},
        {
            "_id": 0,
            "topics.topic": 1,
            "topics.level": 1,
            "topics.progress": 1,
            "topics.weaknesses": 1,
            "topics.last_updated": 1,
        },
    )
    if not doc:
        return []

    topics = doc.get("topics", [])
    topics_sorted = sorted(topics, key=lambda item: item.get("last_updated", datetime.fromtimestamp(0, tz=UTC)), reverse=True)

    output: list[dict[str, Any]] = []
    for item in topics_sorted:
        last_updated = item.get("last_updated")
        output.append(
            {
                "topic": item.get("topic", ""),
                "level": item.get("level", "beginner"),
                "progress": float(item.get("progress", 0.0)),
                "weaknesses": list(item.get("weaknesses", []))[:3],
                "last_updated": last_updated.isoformat() if isinstance(last_updated, datetime) else str(last_updated),
            }
        )
    return output


async def get_topic_details(user_id: str, topic: str) -> UserTopicDetailsResponse | None:
    collection = get_database()["user_learning_history"]
    normalized_topic = topic.strip()

    doc = await collection.find_one(
        {"user_id": user_id, "topics.topic": normalized_topic},
        {"_id": 0, "topics.$": 1},
    )
    if not doc or not doc.get("topics"):
        return None

    topic_item = doc["topics"][0]
    last_updated = topic_item.get("last_updated")
    last_updated_iso = last_updated.isoformat() if isinstance(last_updated, datetime) else str(last_updated)
    weaknesses = list(topic_item.get("weaknesses", []))

    learning_plan_raw = topic_item.get("learning_plan", {})
    try:
        learning_plan = LearningPlanResult.model_validate(learning_plan_raw)
    except Exception:
        learning_plan = LearningPlanResult.model_validate(
            {
                "explanations": ["Resume by reviewing prior notes and weak areas."],
                "learning_steps": ["Revisit fundamentals", "Practice focused weak-area exercises"],
                "practice_questions": ["Solve one easy variant", "Solve one medium variant"],
                "analogy": "Think of learning as iterating toward fewer mistakes each pass.",
                "next_action": "Start with one focused practice block on your weakest concept.",
            }
        )

    if weaknesses:
        resume_message = f"You previously struggled with: {', '.join(weaknesses[:3])}"
    else:
        resume_message = "Welcome back. Continue from your previous learning plan."

    return UserTopicDetailsResponse(
        topic=topic_item.get("topic", normalized_topic),
        level=topic_item.get("level", "beginner"),
        strengths=topic_item.get("strengths", []),
        weaknesses=weaknesses,
        misconceptions=topic_item.get("misconceptions", []),
        progress=float(topic_item.get("progress", 0.0)),
        last_updated=last_updated_iso,
        learning_plan=learning_plan,
        resume_message=resume_message,
    )


async def delete_topic_progress(user_id: str, topic: str) -> bool:
    collection = get_database()["user_learning_history"]
    normalized_topic = topic.strip()

    result = await collection.update_one(
        {"user_id": user_id},
        {"$pull": {"topics": {"topic": normalized_topic}}},
    )

    # Clean up empty user history records after topic removal.
    await collection.delete_one({"user_id": user_id, "topics": {"$size": 0}})
    return result.modified_count > 0
