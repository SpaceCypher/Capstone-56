import json
import logging
import re
import uuid
from typing import Any

from app.services.llm_service import LLMRateLimitError, LLMServiceError, call_llm

logger = logging.getLogger(__name__)


def _slugify_topic(topic: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", topic.strip().lower())
    cleaned = cleaned.strip("-")
    return cleaned or "general"


def _slot_focus_label(slot_index: int, easier: bool) -> str:
    if easier:
        mapping = {
            1: "conceptual definition",
            2: "practical use-case",
            3: "common mistake and correction",
        }
    else:
        mapping = {
            1: "concept/mechanism understanding",
            2: "application scenario",
            3: "debugging or edge-case reasoning",
        }
    return mapping.get(slot_index, "conceptual understanding")


def _prompt_prefix_key(prompt: str) -> str:
    words = re.sub(r"\s+", " ", prompt.strip().lower()).split(" ")
    return " ".join(words[:5])


def _matches_slot_style(prompt: str, slot_index: int) -> bool:
    text = prompt.lower()
    if slot_index == 1:
        return any(token in text for token in ("what is", "define", "explain", "how does", "concept"))
    if slot_index == 2:
        return any(token in text for token in ("when", "scenario", "apply", "use-case", "where would"))
    if slot_index == 3:
        return any(token in text for token in ("debug", "edge", "bug", "incorrect", "fails", "fix"))
    return True


def _fallback_question(topic: str, concept_id: str, easier: bool, variant: int = 1) -> dict[str, Any]:
    easy_prompts = [
        f"In one line, define {topic} and give one tiny example.",
        f"Give one everyday scenario where {topic} is useful and why.",
        f"Name one beginner mistake in {topic} and one way to fix it.",
    ]
    easy_answers = [
        f"A short definition of {topic} plus one simple example.",
        f"One practical scenario with a brief reason {topic} helps.",
        f"One beginner mistake in {topic} with one concrete correction.",
    ]

    medium_prompts = [
        f"What is one common mistake in {topic}, and how do you avoid it?",
        f"When should you apply {topic}, and what result should you expect?",
        f"An edge case breaks a {topic} solution. What is your first debugging step?",
    ]
    medium_answers = [
        f"A clear mistake plus one concrete prevention step in {topic}.",
        f"A clear scenario for applying {topic} and expected outcome.",
        f"One focused debugging step for diagnosing {topic} edge-case failure.",
    ]

    prompts = easy_prompts if easier else medium_prompts
    answers = easy_answers if easier else medium_answers
    slot = (max(1, variant) - 1) % len(prompts)

    prompt = prompts[slot]
    expected_answer = answers[slot]
    difficulty = 1 if easier else 2

    if variant > len(prompts):
        prompt = f"{prompt} (Variation {variant})"

    return {
        "question_id": f"q-{concept_id}-{uuid.uuid4().hex[:8]}",
        "concept_id": concept_id,
        "topic": topic,
        "prompt": prompt,
        "expected_answer": expected_answer,
        "difficulty": difficulty,
    }


def _adaptive_question_prompt(
    topic: str,
    easier: bool,
    variant_index: int = 1,
    avoid_prompts: list[str] | None = None,
) -> str:
    difficulty_hint = "easy" if easier else "medium"
    avoid_prompts = avoid_prompts or []
    avoid_block = "\n".join(f"- {item}" for item in avoid_prompts[:5]) or "- none"

    focus_hint = _slot_focus_label(variant_index, easier)

    return f"""
You are an expert tutor.

Generate ONE short adaptive practice question to test knowledge properly.

Topic: {topic}
Target difficulty: {difficulty_hint}
Question slot in 3-question set: {variant_index}
Required focus for this slot: {focus_hint}

Previously accepted questions (do not repeat or rephrase):
{avoid_block}

Rules:
- Keep the question concise (max 20 words)
- The question must test conceptual understanding, not trivia
- Avoid multiple-choice format
- This question must be meaningfully different from previously accepted questions
- Do not use same wording or same sub-skill as earlier questions
- Strictly follow this slot focus: {focus_hint}
- Keep expected_answer concise (max 25 words)
- Return STRICT JSON only

Return JSON:
{{
  "prompt": "...",
  "expected_answer": "...",
  "difficulty": 1
}}
""".strip()


def _normalize_output(raw: dict[str, Any], topic: str, concept_id: str, easier: bool) -> dict[str, Any]:
    prompt = str(raw.get("prompt") or raw.get("question") or "").strip()
    expected_answer = str(raw.get("expected_answer") or raw.get("answer") or "").strip()

    try:
        difficulty = int(raw.get("difficulty", 1 if easier else 2))
    except (TypeError, ValueError):
        difficulty = 1 if easier else 2
    difficulty = max(1, min(3, difficulty))

    if not prompt or not expected_answer:
        return _fallback_question(topic, concept_id, easier)

    return {
        "question_id": f"q-{concept_id}-{uuid.uuid4().hex[:8]}",
        "concept_id": concept_id,
        "topic": topic,
        "prompt": prompt,
        "expected_answer": expected_answer,
        "difficulty": difficulty,
    }


async def generate_adaptive_question(
    topic: str,
    concept_id: str | None = None,
    easier: bool = False,
    *,
    variant_index: int = 1,
    avoid_prompts: list[str] | None = None,
) -> dict[str, Any]:
    selected_topic = topic.strip() or "General"
    selected_concept = (concept_id or _slugify_topic(selected_topic)).strip() or "general"

    try:
        raw = await call_llm(
            _adaptive_question_prompt(
                selected_topic,
                easier,
                variant_index=variant_index,
                avoid_prompts=avoid_prompts,
            )
        )
        if not isinstance(raw, dict):
            return _fallback_question(selected_topic, selected_concept, easier, variant=variant_index)
        return _normalize_output(raw, selected_topic, selected_concept, easier)
    except (LLMRateLimitError, LLMServiceError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        logger.warning("Adaptive question generation failed; using fallback question. %s", exc)
        return _fallback_question(selected_topic, selected_concept, easier, variant=variant_index)


async def generate_adaptive_question_set(
    topic: str,
    concept_id: str | None = None,
    easier: bool = False,
    count: int = 3,
) -> list[dict[str, Any]]:
    selected_topic = topic.strip() or "General"
    selected_concept = (concept_id or _slugify_topic(selected_topic)).strip() or "general"
    target_count = max(1, min(5, int(count)))

    questions: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    seen_prefixes: set[str] = set()

    for slot_index in range(1, target_count + 1):
        slot_question: dict[str, Any] | None = None

        for _ in range(4):
            candidate = await generate_adaptive_question(
                topic=selected_topic,
                concept_id=selected_concept,
                easier=easier,
                variant_index=slot_index,
                avoid_prompts=[item["prompt"] for item in questions if item.get("prompt")],
            )
            prompt_key = re.sub(r"\s+", " ", str(candidate.get("prompt") or "").strip().lower())
            prefix_key = _prompt_prefix_key(prompt_key)
            if not prompt_key or prompt_key in seen_keys or prefix_key in seen_prefixes:
                continue
            if not _matches_slot_style(prompt_key, slot_index):
                continue

            seen_keys.add(prompt_key)
            seen_prefixes.add(prefix_key)
            slot_question = candidate
            break

        if slot_question is None:
            fallback = _fallback_question(selected_topic, selected_concept, easier, variant=slot_index)
            fallback_key = re.sub(r"\s+", " ", str(fallback.get("prompt") or "").strip().lower())
            if fallback_key in seen_keys:
                fallback = _fallback_question(selected_topic, selected_concept, easier, variant=slot_index + target_count)
                fallback_key = re.sub(r"\s+", " ", str(fallback.get("prompt") or "").strip().lower())
            seen_keys.add(fallback_key)
            seen_prefixes.add(_prompt_prefix_key(fallback_key))
            slot_question = fallback

        questions.append(slot_question)

    while len(questions) < target_count:
        variant = len(questions) + 1
        questions.append(_fallback_question(selected_topic, selected_concept, easier, variant=variant))

    return questions
