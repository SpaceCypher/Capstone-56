import json
import logging
import os
from urllib import error, request

from app.models.schemas import AdaptiveContent, AttemptPayload, LearningState

logger = logging.getLogger(__name__)


def _build_explanation(topic: str, state: LearningState, correctness_reason: str | None) -> str:
    if state == LearningState.STRUGGLING:
        base = f"You are close, but {topic} needs one smaller step. Focus on the core rule before solving."
        if correctness_reason:
            return f"{base} {correctness_reason}"
        return base

    if state == LearningState.GUESSING:
        return (
            f"Take a pause on {topic}. Start by writing the approach in one line before answering; "
            "this reduces random attempts."
        )

    if state == LearningState.MASTERY:
        return f"Great work on {topic}. Your response pattern suggests strong conceptual clarity."

    if state == LearningState.IMPROVING:
        return f"Progress on {topic} is visible. Keep using the same method and increase difficulty gradually."

    return f"You are building understanding in {topic}. One more guided attempt will improve confidence."


def _build_easier_question(topic: str) -> str:
    return (
        f"Practice ({topic}): Write a minimal example and explain why each step is needed in simple words."
    )


def _build_next_step(state: LearningState) -> str:
    if state in (LearningState.STRUGGLING, LearningState.GUESSING):
        return "Review a worked example, solve one easier variant, then retry the original question."
    if state == LearningState.MASTERY:
        return "Move to a slightly harder question with one additional constraint."
    if state == LearningState.IMPROVING:
        return "Continue with one medium-difficulty problem and explain your reasoning after solving."
    return "Attempt one similar question and compare your approach with the model solution."


def _is_live_genai_enabled() -> bool:
    # Live AI generation is opt-in to keep local demos stable by default.
    flag = os.getenv("GENAI_USE_LIVE", "false").strip().lower()
    return flag in {"1", "true", "yes", "on"}


def _is_genai_debug_enabled() -> bool:
    flag = os.getenv("GENAI_DEBUG", "false").strip().lower()
    return flag in {"1", "true", "yes", "on"}


def _extract_json_object(text: str) -> dict[str, str] | None:
    cleaned = text.strip().removeprefix("```json").removesuffix("```").strip()
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        data = json.loads(cleaned[start : end + 1])
        if isinstance(data, dict):
            return data
    except Exception:
        return None

    return None


def _resolve_live_llm_config() -> tuple[str, str, str] | None:
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    llm_api_key = os.getenv("LLM_API_KEY", "").strip()
    google_api_key = os.getenv("GOOGLE_API_KEY", "").strip()

    api_key = groq_api_key or llm_api_key or google_api_key
    if not api_key:
        return None

    base_url = os.getenv("LLM_BASE_URL", "").strip()
    if not base_url:
        if groq_api_key:
            base_url = "https://api.groq.com/openai/v1"
        elif google_api_key:
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
        else:
            base_url = "https://api.openai.com/v1"

    llm_model = os.getenv("LLM_MODEL", "").strip()
    if groq_api_key:
        model = os.getenv("GROQ_MODEL", "").strip() or llm_model or "llama-3.1-8b-instant"
    elif google_api_key:
        model = os.getenv("GOOGLE_MODEL", "").strip() or llm_model or "gemini-1.5-flash"
    else:
        model = llm_model or "gpt-4o-mini"

    return api_key, base_url, model


def _generate_with_live_llm(
    payload: AttemptPayload,
    state: LearningState,
    reason: str,
    is_correct: bool,
    correctness_reason: str,
) -> dict[str, str] | None:
    if not _is_live_genai_enabled():
        return None

    config = _resolve_live_llm_config()
    if config is None:
        return None

    api_key, base_url, model = config
    endpoint = f"{base_url}/chat/completions"

    prompt = (
        "You are an expert adaptive tutor. Return strict JSON only with keys: "
        "explanation, easier_question, next_step. Keep text concise and actionable. "
        "Do not include markdown, code fences, or extra keys.\n\n"
        f"topic={payload.topic}\n"
        f"question={payload.question_prompt}\n"
        f"expected_answer={payload.expected_answer}\n"
        f"student_answer={payload.answer}\n"
        f"is_correct={str(is_correct).lower()}\n"
        f"correctness_reason={correctness_reason}\n"
        f"state={state.value}\n"
        f"reason={reason}\n"
    )

    body = {
        "model": model,
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "You are a precise tutoring assistant. Always return strict JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    debug_enabled = _is_genai_debug_enabled()
    safe_endpoint = endpoint

    try:
        req = request.Request(
            endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=20) as res:
            payload_json = json.loads(res.read().decode("utf-8"))

        if debug_enabled:
            logger.info("Live LLM call succeeded | model=%s | endpoint=%s", model, safe_endpoint)

        choices = payload_json.get("choices", [])
        if not choices:
            return None

        content = str(choices[0].get("message", {}).get("content", ""))
        if not content:
            return None

        parsed = _extract_json_object(content)
        if parsed is None:
            if debug_enabled:
                logger.warning("Live LLM response parse failed | model=%s | raw=%s", model, content[:300])
            return None

        explanation = str(parsed.get("explanation", "")).strip()
        easier_question = str(parsed.get("easier_question", "")).strip()
        next_step = str(parsed.get("next_step", "")).strip()

        if explanation and easier_question and next_step:
            return {
                "explanation": explanation,
                "easier_question": easier_question,
                "next_step": next_step,
            }
        if debug_enabled:
            logger.warning(
                "Live LLM response missing required fields | model=%s | parsed=%s",
                model,
                str(parsed)[:300],
            )
    except error.HTTPError as exc:
        details = ""
        try:
            details = exc.read().decode("utf-8")
        except Exception:
            details = "<unavailable>"

        if debug_enabled:
            logger.error(
                "Live LLM HTTP error | model=%s | status=%s | endpoint=%s | details=%s",
                model,
                exc.code,
                safe_endpoint,
                details[:500],
            )
        return None
    except (TimeoutError, ValueError, error.URLError, KeyError, IndexError, TypeError) as exc:
        if debug_enabled:
            logger.error(
                "Live LLM request error | model=%s | endpoint=%s | error=%s",
                model,
                safe_endpoint,
                str(exc),
            )
        return None

    return None


def generate_adaptive_content(
    payload: AttemptPayload,
    state: LearningState,
    reason: str,
    is_correct: bool,
    correctness_reason: str,
) -> AdaptiveContent:
    live = _generate_with_live_llm(
        payload=payload,
        state=state,
        reason=reason,
        is_correct=is_correct,
        correctness_reason=correctness_reason,
    )
    if live is not None:
        return AdaptiveContent(
            state=state,
            reason=reason,
            explanation=live["explanation"],
            easier_question=live["easier_question"],
            next_step=live["next_step"],
        )

    return AdaptiveContent(
        state=state,
        reason=reason,
        explanation=_build_explanation(payload.topic, state, correctness_reason),
        easier_question=_build_easier_question(payload.topic),
        next_step=_build_next_step(state),
    )
