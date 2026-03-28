from app.models.schemas import LearningState


def classify_learning_state(
    is_correct: bool,
    recent_correct_rate: float,
    correctness_reason: str | None = None,
) -> tuple[LearningState, str]:
    reason_suffix = f" AI check: {correctness_reason}" if correctness_reason else ""

    if not is_correct and recent_correct_rate < 0.35:
        return (
            LearningState.STRUGGLING,
            "Incorrect answer with weak recent trend indicates conceptual friction." + reason_suffix,
        )

    if not is_correct:
        return (
            LearningState.GUESSING,
            "Incorrect answer suggests partial understanding or unstable reasoning." + reason_suffix,
        )

    if is_correct and recent_correct_rate >= 0.7:
        return (
            LearningState.MASTERY,
            "Correct answer with strong recent trend indicates mastery." + reason_suffix,
        )

    if is_correct:
        return (
            LearningState.IMPROVING,
            "Correct answer indicates improving concept understanding." + reason_suffix,
        )

    return (LearningState.NEUTRAL, "Insufficient behavior signal for a stronger classification." + reason_suffix)
