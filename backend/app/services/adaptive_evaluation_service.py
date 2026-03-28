import re
from typing import Any

from app.models.schemas import AISource
from app.services.llm_service import LLMRateLimitError, LLMServiceError, call_llm


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", value.lower())).strip()


def _heuristic_correct(expected_answer: str, learner_answer: str) -> bool:
    expected = _normalize_text(expected_answer)
    learner = _normalize_text(learner_answer)

    if not expected or not learner:
        return False

    if learner == expected:
        return True

    if learner in expected and len(learner) >= max(3, int(len(expected) * 0.5)):
        return True

    expected_tokens = {token for token in expected.split(" ") if token}
    learner_tokens = {token for token in learner.split(" ") if token}
    if not expected_tokens or not learner_tokens:
        return False

    overlap = len(expected_tokens & learner_tokens) / max(1, len(expected_tokens))
    return overlap >= 0.55


async def evaluate_adaptive_answer(
    *,
    topic: str,
    question_prompt: str,
    expected_answer: str,
    learner_answer: str,
) -> tuple[bool, str, AISource]:
    prompt = f"""
You are an expert evaluator for adaptive learning.

Topic: {topic}
Question: {question_prompt}
Reference Expected Answer: {expected_answer}
Student Answer: {learner_answer}

Tasks:
1. Decide if student answer is correct for the asked question.
2. Use semantic correctness (not exact wording match).
3. Keep the explanation concise and specific.

Return STRICT JSON:
{{
  "is_correct": true,
  "feedback_reason": "..."
}}
""".strip()

    try:
        raw = await call_llm(prompt)
        if not isinstance(raw, dict):
            raise ValueError("LLM evaluation payload is not an object")

        is_correct_raw: Any = raw.get("is_correct", False)
        is_correct = bool(is_correct_raw)

        feedback_reason = str(raw.get("feedback_reason", "")).strip()
        if not feedback_reason:
            feedback_reason = "AI evaluation completed based on answer quality and concept alignment."

        return is_correct, feedback_reason, AISource.LIVE
    except (LLMRateLimitError, LLMServiceError, ValueError, TypeError, KeyError):
        heuristic = _heuristic_correct(expected_answer=expected_answer, learner_answer=learner_answer)
        reason = (
            "Fallback evaluator marked answer as correct based on semantic overlap with expected answer."
            if heuristic
            else "Fallback evaluator marked answer as incorrect based on insufficient semantic overlap with expected answer."
        )
        return heuristic, reason, AISource.FALLBACK
