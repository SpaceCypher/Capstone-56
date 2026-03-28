import json
import logging
import os
import re
from typing import Any

from app.db.mongo import save_diagnostic_record
from app.models.schemas import (
    AISource,
    DiagnosticGenerateResponse,
    DiagnosticResponseItem,
    EvaluationResult,
    LearningPlanResult,
)
from pydantic import ValidationError
from app.services.llm_service import LLMRateLimitError, LLMServiceError, call_llm
from app.services.user_history_service import get_topic_details

logger = logging.getLogger(__name__)


def _env_enabled(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _allow_rate_limit_fallback() -> bool:
    app_env = os.getenv("APP_ENV", "development").strip().lower()
    default = app_env != "production"
    return _env_enabled("LLM_FALLBACK_ON_RATE_LIMIT", default)


def _fallback_generate_questions(topic: str) -> DiagnosticGenerateResponse:
    return DiagnosticGenerateResponse.model_validate(
        {
            "questions": [
                {
                    "id": 1,
                    "type": "conceptual",
                    "question": f"In your own words, explain the core idea behind {topic} and why it is useful.",
                },
                {
                    "id": 2,
                    "type": "application",
                    "question": f"Describe a practical scenario where {topic} should be applied and what result you expect.",
                },
                {
                    "id": 3,
                    "type": "reasoning",
                    "question": f"A solution using {topic} gives incorrect output on edge cases. How would you reason through debugging it systematically?",
                },
            ]
        }
    )


def _confidence_to_score(value: str) -> float:
    mapping = {"low": 0.2, "medium": 0.6, "high": 0.9}
    return mapping.get(value, 0.6)


def _fallback_evaluate_responses(topic: str, responses: list[DiagnosticResponseItem]) -> EvaluationResult:
    answer_lengths = [len(item.answer.strip()) for item in responses if not item.doesnt_know]
    unknown_count = sum(1 for item in responses if item.doesnt_know)
    avg_length = sum(answer_lengths) / max(1, len(answer_lengths))

    confidence_scores = [_confidence_to_score(item.confidence.value) for item in responses]
    avg_confidence = sum(confidence_scores) / max(1, len(confidence_scores))
    confidence_spread = max(confidence_scores) - min(confidence_scores) if confidence_scores else 0.0
    attempts_values = [item.attempts for item in responses if item.attempts is not None]
    avg_attempts = sum(attempts_values) / max(1, len(attempts_values)) if attempts_values else 1.0

    high_confidence_weak_answer = sum(
        1
        for item in responses
        if not item.doesnt_know and item.confidence.value == "high" and len(item.answer.strip()) < 85
    )
    low_confidence_reasonable_answer = sum(
        1
        for item in responses
        if item.confidence.value == "low" and len(item.answer.strip()) >= 120
    )

    if unknown_count >= 2:
        level = "beginner"
    elif avg_length < 80:
        level = "beginner"
    elif avg_length < 180:
        level = "intermediate"
    else:
        level = "advanced"

    if unknown_count >= 2 and avg_confidence <= 0.6:
        behavior = "struggling"
    elif high_confidence_weak_answer >= 1:
        behavior = "guessing"
    elif avg_confidence < 0.45 and avg_length < 120:
        behavior = "struggling"
    elif low_confidence_reasonable_answer >= 1 or confidence_spread > 0.45:
        behavior = "inconsistent"
    else:
        behavior = "confident"

    strengths: list[str] = []
    if avg_length >= 120:
        strengths.append("Provides reasonably detailed explanations")
    if avg_confidence >= 0.6:
        strengths.append("Shows steady confidence across responses")
    if unknown_count == 0:
        strengths.append("Attempts every question without skipping")
    if not strengths:
        strengths.append("Has baseline awareness of core concepts")

    weaknesses: list[str] = []
    if avg_length < 100:
        weaknesses.append("Answers are brief and miss deeper reasoning")
    if avg_confidence < 0.5:
        weaknesses.append("Low confidence suggests conceptual uncertainty")
    if unknown_count >= 1:
        weaknesses.append("Skipped one or more questions due to uncertainty")
    if avg_attempts >= 2.5:
        weaknesses.append("Higher retries suggest fragile understanding under pressure")
    if confidence_spread > 0.45:
        weaknesses.append("Confidence varies significantly between question types")
    if not weaknesses:
        weaknesses.append("Needs stronger rigor in edge-case handling")

    misconceptions: list[str] = []
    if high_confidence_weak_answer >= 1:
        misconceptions.append("High confidence paired with weak answers indicates likely misconception risk")
    if unknown_count >= 1:
        misconceptions.append("Gaps in recall suggest missing mental models for some subtopics")
    misconceptions.append(
        f"May be treating {topic} as a memorization topic instead of a transferable problem-solving skill"
    )

    confidence_gaps: list[str] = ["Confidence level does not always match answer depth"]
    if low_confidence_reasonable_answer >= 1:
        confidence_gaps.append("Low confidence on reasonable answers indicates weak self-trust")
    if unknown_count >= 1 and avg_confidence >= 0.6:
        confidence_gaps.append("Marked uncertainty despite moderate/high confidence on other questions")

    recommended_focus_areas = [
        f"Build stronger foundational intuition for {topic}",
        "Practice structured reasoning before final answers",
        "Use debugging checklists for self-verification",
    ]

    return EvaluationResult.model_validate(
        {
            "level": level,
            "behavior": behavior,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "misconceptions": misconceptions,
            "confidence_gaps": confidence_gaps,
            "recommended_focus_areas": recommended_focus_areas,
            "evaluation_confidence": 0.65,
        }
    )


def _fallback_generate_learning_plan(
    topic: str,
    evaluation: EvaluationResult,
    prior_weaknesses: list[str] | None = None,
) -> LearningPlanResult:
    prior_focus = (prior_weaknesses or [None])[0]
    focus = prior_focus or (evaluation.recommended_focus_areas[0] if evaluation.recommended_focus_areas else f"core {topic} concepts")

    return LearningPlanResult.model_validate(
        {
            "explanations": [
                f"Start by reframing {topic} as a sequence of small decisions instead of one big answer.",
                "When solving tasks, first describe the approach in plain language, then execute.",
            ],
            "learning_steps": [
                f"Review fundamentals of {topic} with one concise resource.",
                "Solve 3 easy examples and explain each step aloud.",
                f"Tackle 2 medium exercises focused on: {focus}.",
                "Perform a short reflection: what worked, what failed, and why.",
            ],
            "practice_questions": [
                f"Explain how you would apply {topic} to a simple real-world scenario.",
                f"Given a broken solution involving {topic}, identify the bug and propose a fix.",
            ],
            "analogy": f"Think of {topic} like a GPS route: you choose checkpoints first, then follow turn-by-turn logic.",
            "next_action": "Complete one focused 25-minute practice session and summarize your mistakes in 3 bullets.",
        }
    )


def _question_prompt(topic: str) -> str:
    return f"""
You are an expert tutor and assessment designer.

Topic: {topic}

Requirements:
- Generate EXACTLY 3 questions:
    1. Conceptual understanding
    2. Practical application
    3. Reasoning/debugging/edge case
- No multiple choice
- Include coding question if applicable
- No answers

Return STRICT JSON:
{{
  "questions": [
    {{ "id": 1, "type": "conceptual", "question": "..." }},
    {{ "id": 2, "type": "application", "question": "..." }},
        {{ "id": 3, "type": "reasoning", "question": "..." }}
  ]
}}
""".strip()


def _coerce_three_question_payload(raw: dict[str, Any]) -> dict[str, Any]:
    questions = raw.get("questions")
    if not isinstance(questions, list):
        return raw

    normalized: list[dict[str, Any]] = []
    for index, question in enumerate(questions[:3], start=1):
        if not isinstance(question, dict):
            continue
        normalized.append(
            {
                "id": index,
                "type": str(question.get("type", "conceptual" if index == 1 else "application" if index == 2 else "reasoning")),
                "question": str(question.get("question", "")).strip(),
            }
        )

    if len(normalized) == 3:
        return {"questions": normalized}
    return raw


def _normalize_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("text", "description", "reason", "message", "item", "content", "value"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        for candidate in value.values():
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, list):
        parts = [_normalize_text(item) for item in value]
        return "; ".join(part for part in parts if part)
    return str(value).strip()


def _normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text.lower())).strip()


def _answer_based_strengths_weaknesses(topic: str, responses: list[DiagnosticResponseItem]) -> tuple[list[str], list[str]]:
    non_unknown = [item for item in responses if not item.doesnt_know]
    unknown_count = len(responses) - len(non_unknown)

    answer_lengths = [len(item.answer.strip()) for item in non_unknown]
    avg_length = sum(answer_lengths) / max(1, len(answer_lengths))
    high_confidence_count = sum(1 for item in responses if item.confidence.value == "high")
    low_confidence_count = sum(1 for item in responses if item.confidence.value == "low")

    reasoning_markers = ("because", "therefore", "if", "else", "edge", "example")
    reasoning_count = sum(
        1
        for item in non_unknown
        if any(marker in item.answer.strip().lower() for marker in reasoning_markers)
    )

    high_confidence_short = sum(
        1
        for item in non_unknown
        if item.confidence.value == "high" and len(item.answer.strip()) < 85
    )

    strengths: list[str] = []
    if avg_length >= 110:
        strengths.append("Gives detailed explanations instead of one-line answers")
    if reasoning_count >= 1:
        strengths.append("Uses reasoning language to justify answers")
    if unknown_count == 0:
        strengths.append("Attempts all questions without skipping")
    if high_confidence_count >= 2 and high_confidence_short == 0:
        strengths.append("Confidence is mostly aligned with response quality")
    if not strengths:
        strengths.append(f"Shows baseline familiarity with {topic}")

    weaknesses: list[str] = []
    if avg_length < 90:
        weaknesses.append("Answers are too brief and miss conceptual depth")
    if unknown_count >= 1:
        weaknesses.append("Marked uncertainty on one or more answers")
    if low_confidence_count >= 2:
        weaknesses.append("Low confidence appears repeatedly across responses")
    if high_confidence_short >= 1:
        weaknesses.append("High confidence appears on weak or shallow responses")
    if reasoning_count == 0:
        weaknesses.append("Responses rarely explain why the answer is correct")
    if not weaknesses:
        weaknesses.append(f"Needs stronger edge-case and debugging rigor in {topic}")

    return strengths, weaknesses


def _sanitize_insights(
    values: Any,
    fallback: list[str],
    question_texts: set[str],
    min_items: int = 1,
    max_items: int = 4,
) -> list[str]:
    candidates = _normalize_string_list(values, fallback, min_items=1)
    sanitized: list[str] = []
    seen: set[str] = set()

    for item in candidates:
        normalized = _normalize_for_match(item)
        if not normalized or len(normalized) < 12:
            continue
        if normalized in seen:
            continue
        if normalized.startswith("question "):
            continue
        if normalized.endswith("?"):
            continue
        if any(normalized == q or normalized in q or q in normalized for q in question_texts):
            continue
        seen.add(normalized)
        sanitized.append(item)

    fallback_index = 0
    while len(sanitized) < min_items and fallback_index < len(fallback):
        candidate = fallback[fallback_index]
        fallback_index += 1
        normalized = _normalize_for_match(candidate)
        if normalized and normalized not in seen:
            seen.add(normalized)
            sanitized.append(candidate)

    return sanitized[:max_items]


def _normalize_string_list(value: Any, fallback: list[str], min_items: int = 1, max_items: int | None = None) -> list[str]:
    items: list[str] = []
    if isinstance(value, list):
        items = [_normalize_text(item) for item in value]
    elif value is not None:
        text = _normalize_text(value)
        if text:
            items = [text]

    items = [item for item in items if item]
    if not items:
        items = list(fallback)

    while len(items) < min_items and fallback:
        items.append(fallback[(len(items)) % len(fallback)])

    if max_items is not None:
        items = items[:max_items]
    return items


def _coerce_evaluation_payload(
    raw: dict[str, Any],
    topic: str,
    responses: list[DiagnosticResponseItem] | None = None,
) -> dict[str, Any]:
    level_raw = _normalize_text(raw.get("level", "beginner")).lower()
    behavior_raw = _normalize_text(raw.get("behavior", "inconsistent")).lower()

    level_map = {
        "beginner": "beginner",
        "novice": "beginner",
        "intermediate": "intermediate",
        "advanced": "advanced",
        "expert": "advanced",
    }
    behavior_map = {
        "struggling": "struggling",
        "guessing": "guessing",
        "confident": "confident",
        "inconsistent": "inconsistent",
        "neutral": "inconsistent",
        "mastery": "confident",
    }

    confidence_raw = raw.get("evaluation_confidence", 0.65)
    try:
        confidence = float(confidence_raw)
    except (TypeError, ValueError):
        confidence = 0.65
    confidence = min(1.0, max(0.0, confidence))

    fallback_strengths, fallback_weaknesses = _answer_based_strengths_weaknesses(topic, responses or [])
    question_texts = {
        _normalize_for_match(item.question)
        for item in (responses or [])
        if isinstance(item.question, str) and item.question.strip()
    }

    strengths = _sanitize_insights(
        raw.get("strengths"),
        fallback_strengths,
        question_texts,
        min_items=1,
    )
    weaknesses = _sanitize_insights(
        raw.get("weaknesses"),
        fallback_weaknesses,
        question_texts,
        min_items=1,
    )

    return {
        "level": level_map.get(level_raw, "beginner"),
        "behavior": behavior_map.get(behavior_raw, "inconsistent"),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "misconceptions": _normalize_string_list(
            raw.get("misconceptions"),
            [f"May need clearer mental models for {topic}"],
            min_items=1,
        ),
        "confidence_gaps": _normalize_string_list(
            raw.get("confidence_gaps"),
            ["Confidence may not always match answer quality"],
            min_items=1,
        ),
        "recommended_focus_areas": _normalize_string_list(
            raw.get("recommended_focus_areas"),
            [f"Core {topic} fundamentals", "Step-by-step problem solving"],
            min_items=1,
        ),
        "evaluation_confidence": confidence,
    }


def _coerce_learning_plan_payload(raw: dict[str, Any], topic: str) -> dict[str, Any]:
    return {
        "explanations": _normalize_string_list(
            raw.get("explanations"),
            [f"Break {topic} into smaller concepts and review each one clearly."],
            min_items=1,
        ),
        "learning_steps": _normalize_string_list(
            raw.get("learning_steps"),
            [f"Review one concise concept in {topic} and solve one example."],
            min_items=1,
        ),
        "practice_questions": _normalize_string_list(
            raw.get("practice_questions"),
            [
                f"Explain one practical use-case of {topic}.",
                f"Debug one incorrect solution that uses {topic}.",
            ],
            min_items=2,
            max_items=2,
        ),
        "analogy": _normalize_text(raw.get("analogy"))
        or f"Think of {topic} as a guided process with checkpoints and feedback.",
        "next_action": _normalize_text(raw.get("next_action"))
        or "Do one focused practice cycle and note your top two mistakes.",
    }


def _evaluation_prompt(topic: str, responses: list[DiagnosticResponseItem]) -> str:
    response_json = json.dumps([item.model_dump(exclude_none=True) for item in responses], ensure_ascii=True)
    answer_evidence = json.dumps(
        [
            {
                "question_id": item.question_id,
                "answer": item.answer,
                "doesnt_know": item.doesnt_know,
                "confidence": item.confidence.value,
                "attempts": item.attempts,
            }
            for item in responses
        ],
        ensure_ascii=True,
    )
    confidence_data = ", ".join(item.confidence.value for item in responses)
    doesnt_know_count = sum(1 for item in responses if item.doesnt_know)
    attempts_data = ", ".join(
        str(item.attempts) if item.attempts is not None else "n/a"
        for item in responses
    )

    return f"""
You are an expert tutor and learning analyst.

Topic: {topic}

Student Responses:
{response_json}

Answer Evidence (primary source for strengths/weaknesses):
{answer_evidence}

Additional Context:
- Confidence: {confidence_data}
- Marked "doesn't know": {doesnt_know_count}
- Attempts (optional): {attempts_data}

Tasks:
1. Determine level (beginner/intermediate/advanced)
2. Identify strengths from answer quality, completeness, and reasoning
3. Identify weaknesses from answer quality gaps, uncertainty, and missing logic
4. Detect misconceptions with emphasis on high-confidence weak answers
5. Detect confidence gaps with emphasis on low-confidence but reasonable answers
6. Classify behavior (struggling/guessing/confident/inconsistent)
7. Recommend focus areas
8. Provide evaluation confidence (0-1)

Important:
- Do NOT use time-based signals.
- Base analysis primarily on answer quality + confidence.
- Treat items with "doesnt_know=true" as explicit knowledge gaps.
- If correctness/attempts are present in the payload, use them as secondary signals.
- For strengths and weaknesses, use concrete observations from student answers.
- Do NOT copy, restate, or paraphrase the question prompts.
- Every strength/weakness item must be an insight about learner performance, not a question text.

Return STRICT JSON:
{{
  "level": "...",
  "behavior": "...",
  "strengths": [],
  "weaknesses": [],
  "misconceptions": [],
  "confidence_gaps": [],
  "recommended_focus_areas": [],
  "evaluation_confidence": 0.0
}}
""".strip()


def _learning_plan_prompt(topic: str, evaluation: EvaluationResult, prior_weaknesses: list[str] | None = None) -> str:
    eval_json = json.dumps(evaluation.model_dump(), ensure_ascii=True)
    prior_weaknesses_block = json.dumps(prior_weaknesses or [], ensure_ascii=True)
    return f"""
You are an expert tutor.

Topic: {topic}

Student Profile:
{eval_json}

Previous Topic Weaknesses (if returning user):
{prior_weaknesses_block}

Tasks:
1. Explain weak concepts simply
2. Provide step-by-step learning path
3. Generate 2 practice questions (easy -> medium)
4. Provide 1 analogy
5. Suggest next action

Return STRICT JSON:
{{
  "explanations": [],
  "learning_steps": [],
  "practice_questions": [],
  "analogy": "...",
  "next_action": "..."
}}
""".strip()


async def generate_questions(topic: str) -> DiagnosticGenerateResponse:
    try:
        raw = await call_llm(_question_prompt(topic))
        parsed = DiagnosticGenerateResponse.model_validate(_coerce_three_question_payload(raw))
        return DiagnosticGenerateResponse(questions=parsed.questions, ai_source=AISource.LIVE)
    except LLMRateLimitError:
        if not _allow_rate_limit_fallback():
            raise
        logger.warning("LLM rate-limited during question generation; using fallback questions")
        parsed = _fallback_generate_questions(topic)
        return DiagnosticGenerateResponse(questions=parsed.questions, ai_source=AISource.FALLBACK)


async def evaluate_responses(topic: str, responses: list[DiagnosticResponseItem]) -> tuple[EvaluationResult, AISource, str | None]:
    try:
        raw = await call_llm(_evaluation_prompt(topic, responses))
        return EvaluationResult.model_validate(_coerce_evaluation_payload(raw, topic, responses)), AISource.LIVE, None
    except LLMRateLimitError as exc:
        if not _allow_rate_limit_fallback():
            raise
        logger.warning("LLM rate-limited during evaluation; using fallback evaluation. %s", exc)
        return _fallback_evaluate_responses(topic, responses), AISource.FALLBACK, str(exc)
    except (LLMServiceError, ValidationError, ValueError, TypeError, KeyError) as exc:
        logger.warning("LLM evaluation payload invalid; using fallback evaluation. %s", exc)
        return (
            _fallback_evaluate_responses(topic, responses),
            AISource.FALLBACK,
            f"LLM evaluation payload invalid: {str(exc)[:240]}",
        )


async def generate_learning_plan(
    topic: str,
    evaluation: EvaluationResult,
    prior_weaknesses: list[str] | None = None,
) -> tuple[LearningPlanResult, AISource, str | None]:
    try:
        raw = await call_llm(_learning_plan_prompt(topic, evaluation, prior_weaknesses=prior_weaknesses))
        return LearningPlanResult.model_validate(_coerce_learning_plan_payload(raw, topic)), AISource.LIVE, None
    except LLMRateLimitError as exc:
        if not _allow_rate_limit_fallback():
            raise
        logger.warning("LLM rate-limited during learning plan generation; using fallback plan. %s", exc)
        return _fallback_generate_learning_plan(topic, evaluation, prior_weaknesses=prior_weaknesses), AISource.FALLBACK, str(exc)
    except (LLMServiceError, ValidationError, ValueError, TypeError, KeyError) as exc:
        logger.warning("LLM learning-plan payload invalid; using fallback plan. %s", exc)
        return (
            _fallback_generate_learning_plan(topic, evaluation, prior_weaknesses=prior_weaknesses),
            AISource.FALLBACK,
            f"LLM learning-plan payload invalid: {str(exc)[:240]}",
        )


async def orchestrate_full_flow(
    topic: str,
    responses: list[DiagnosticResponseItem],
    user_id: str,
) -> tuple[EvaluationResult, LearningPlanResult, str, dict[str, AISource], dict[str, str], AISource]:
    prior_topic_details = await get_topic_details(user_id=user_id, topic=topic)
    prior_weaknesses = prior_topic_details.weaknesses if prior_topic_details else []

    evaluation, evaluation_source, evaluation_reason = await evaluate_responses(topic, responses)
    learning_plan, learning_plan_source, learning_plan_reason = await generate_learning_plan(
        topic,
        evaluation,
        prior_weaknesses=prior_weaknesses,
    )
    stage_sources: dict[str, AISource] = {
        "evaluation": evaluation_source,
        "learning_plan": learning_plan_source,
    }
    stage_reasons: dict[str, str] = {}
    if evaluation_reason:
        stage_reasons["evaluation"] = evaluation_reason
    if learning_plan_reason:
        stage_reasons["learning_plan"] = learning_plan_reason
    ai_source = AISource.FALLBACK if AISource.FALLBACK in stage_sources.values() else AISource.LIVE

    record_id = await save_diagnostic_record(
        {
            "user_id": user_id,
            "topic": topic,
            "questions": [
                {
                    "id": item.question_id,
                    "type": "submitted",
                    "question": item.question,
                }
                for item in responses
            ],
            "responses": [item.model_dump(mode="json") for item in responses],
            "evaluation": evaluation.model_dump(mode="json"),
            "learning_plan": learning_plan.model_dump(mode="json"),
            "ai_source": ai_source.value,
            "stage_sources": {key: value.value for key, value in stage_sources.items()},
            "stage_reasons": stage_reasons,
        }
    )
    return evaluation, learning_plan, record_id, stage_sources, stage_reasons, ai_source


__all__ = [
    "LLMRateLimitError",
    "LLMServiceError",
    "generate_questions",
    "evaluate_responses",
    "generate_learning_plan",
    "orchestrate_full_flow",
]
