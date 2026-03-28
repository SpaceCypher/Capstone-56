from fastapi import APIRouter

from app.db.memory_store import store
from app.models.schemas import AttemptPayload, AttemptResponse, DashboardResponse, QuestionResponse, QuestionSetResponse
from app.services.adaptive_evaluation_service import evaluate_adaptive_answer
from app.services.adaptive_question_service import generate_adaptive_question, generate_adaptive_question_set
from app.services.behavior_engine import classify_learning_state
from app.services.genai_service import generate_adaptive_content

router = APIRouter(prefix="/api/learning", tags=["learning"])


def _recent_correct_rate(user_id: str, concept_id: str) -> float:
    recent = store.get_recent_attempts(user_id=user_id, concept_id=concept_id, limit=5)
    if not recent:
        return 0.0
    correct = sum(1 for row in recent if row["correct"])
    return correct / len(recent)


@router.get("/question", response_model=QuestionResponse)
async def get_question(concept_id: str = "loops", topic: str | None = None) -> QuestionResponse:
    selected_topic = (topic or concept_id or "General").strip() or "General"
    selected_concept_id = (concept_id or selected_topic).strip().lower() or "general"
    question = await generate_adaptive_question(
        topic=selected_topic,
        concept_id=selected_concept_id,
        easier=False,
    )
    return QuestionResponse(**question)


@router.get("/questions", response_model=QuestionSetResponse)
async def get_questions(concept_id: str = "loops", topic: str | None = None, count: int = 3) -> QuestionSetResponse:
    selected_topic = (topic or concept_id or "General").strip() or "General"
    selected_concept_id = (concept_id or selected_topic).strip().lower() or "general"
    questions = await generate_adaptive_question_set(
        topic=selected_topic,
        concept_id=selected_concept_id,
        easier=False,
        count=3,
    )
    return QuestionSetResponse(questions=[QuestionResponse(**item) for item in questions])


@router.post("/attempt", response_model=AttemptResponse)
async def submit_attempt(payload: AttemptPayload) -> AttemptResponse:
    is_correct, correctness_reason, _ = await evaluate_adaptive_answer(
        topic=payload.topic,
        question_prompt=payload.question_prompt,
        expected_answer=payload.expected_answer,
        learner_answer=payload.answer,
    )

    correct_rate = _recent_correct_rate(payload.user_id, payload.concept_id)
    state, reason = classify_learning_state(
        is_correct=is_correct,
        recent_correct_rate=correct_rate,
        correctness_reason=correctness_reason,
    )
    adaptive = generate_adaptive_content(
        payload=payload,
        state=state,
        reason=reason,
        is_correct=is_correct,
        correctness_reason=correctness_reason,
    )
    store.save_attempt(payload=payload, state=state, correct=is_correct)

    next_question = await generate_adaptive_question(
        topic=payload.topic,
        concept_id=payload.concept_id,
        easier=state.value in {"struggling", "guessing"},
    )

    return AttemptResponse(adaptive=adaptive, next_question=QuestionResponse(**next_question))


@router.get("/dashboard/{user_id}", response_model=DashboardResponse)
def get_dashboard(user_id: str) -> DashboardResponse:
    return DashboardResponse(**store.get_dashboard(user_id))
