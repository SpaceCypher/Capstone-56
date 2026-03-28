from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class LearningState(str, Enum):
    STRUGGLING = "struggling"
    GUESSING = "guessing"
    MASTERY = "mastery"
    IMPROVING = "improving"
    NEUTRAL = "neutral"


class AttemptPayload(BaseModel):
    user_id: str = Field(..., min_length=1)
    concept_id: str = Field(..., min_length=1)
    question_id: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    question_prompt: str = Field(..., min_length=5)
    expected_answer: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)


class AdaptiveContent(BaseModel):
    state: LearningState
    reason: str
    explanation: str
    easier_question: str
    next_step: str


class QuestionResponse(BaseModel):
    question_id: str
    concept_id: str
    topic: str
    prompt: str
    expected_answer: str
    difficulty: int


class QuestionSetResponse(BaseModel):
    questions: list[QuestionResponse] = Field(..., min_length=3, max_length=3)


class AttemptResponse(BaseModel):
    adaptive: AdaptiveContent
    next_question: QuestionResponse


class DashboardResponse(BaseModel):
    user_id: str
    total_interactions: int
    state_breakdown: dict[str, int]
    weak_concepts: list[str]


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LearnerLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearnerBehavior(str, Enum):
    STRUGGLING = "struggling"
    GUESSING = "guessing"
    CONFIDENT = "confident"
    INCONSISTENT = "inconsistent"


class AISource(str, Enum):
    LIVE = "live"
    FALLBACK = "fallback"


class DiagnosticGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    user_id: Optional[str] = None


class DiagnosticQuestion(BaseModel):
    id: int = Field(..., ge=1)
    type: str = Field(..., min_length=2)
    question: str = Field(..., min_length=5)


class DiagnosticGenerateResponse(BaseModel):
    questions: list[DiagnosticQuestion] = Field(..., min_length=3, max_length=3)
    ai_source: AISource = AISource.LIVE


class DiagnosticResponseItem(BaseModel):
    question_id: int = Field(..., ge=1)
    question: str = Field(..., min_length=5)
    answer: str = Field(default="", max_length=5000)
    doesnt_know: bool = False
    confidence: ConfidenceLevel
    correct: Optional[bool] = None
    attempts: Optional[int] = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_answer_or_doesnt_know(self) -> "DiagnosticResponseItem":
        if not self.doesnt_know and not self.answer.strip():
            raise ValueError("answer is required unless doesnt_know is true")
        return self


class DiagnosticAnalyzeRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    responses: list[DiagnosticResponseItem] = Field(..., min_length=1)
    user_id: Optional[str] = None


class EvaluationResult(BaseModel):
    level: LearnerLevel
    behavior: LearnerBehavior
    strengths: list[str]
    weaknesses: list[str]
    misconceptions: list[str]
    confidence_gaps: list[str]
    recommended_focus_areas: list[str]
    evaluation_confidence: float = Field(..., ge=0.0, le=1.0)


class LearningPlanResult(BaseModel):
    explanations: list[str] = Field(..., min_length=1)
    learning_steps: list[str] = Field(..., min_length=1)
    practice_questions: list[str] = Field(..., min_length=2, max_length=2)
    analogy: str = Field(..., min_length=5)
    next_action: str = Field(..., min_length=5)


class DiagnosticAnalyzeResponse(BaseModel):
    evaluation: EvaluationResult
    learning_plan: LearningPlanResult
    ai_source: AISource = AISource.LIVE
    stage_sources: dict[str, AISource] = Field(default_factory=dict)
    stage_reasons: dict[str, str] = Field(default_factory=dict)


class TopicDiagnosticHistoryItem(BaseModel):
    questions: list[dict] = Field(default_factory=list)
    responses: list[dict] = Field(default_factory=list)
    evaluation: dict = Field(default_factory=dict)
    timestamp: str


class UserTopicHistory(BaseModel):
    topic: str = Field(..., min_length=2)
    level: LearnerLevel
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)
    progress: float = Field(..., ge=0.0, le=1.0)
    last_updated: str
    learning_plan: dict = Field(default_factory=dict)
    diagnostic_history: list[TopicDiagnosticHistoryItem] = Field(default_factory=list)


class UserProgressRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=2)
    evaluation: EvaluationResult
    learning_plan: LearningPlanResult
    questions: list[dict] = Field(default_factory=list)
    responses: list[dict] = Field(default_factory=list)


class UserProgressResponse(BaseModel):
    user_id: str
    topic: str
    progress: float
    level: LearnerLevel
    last_updated: str
    message: str


class UserTopicSummary(BaseModel):
    topic: str
    level: LearnerLevel
    progress: float
    weaknesses: list[str] = Field(default_factory=list)
    last_updated: str


class UserTopicsResponse(BaseModel):
    topics: list[UserTopicSummary] = Field(default_factory=list)


class UserTopicDetailsResponse(BaseModel):
    topic: str
    level: LearnerLevel
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)
    progress: float
    last_updated: str
    learning_plan: LearningPlanResult
    resume_message: str


class AuthSignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=200)


class AuthLoginRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=120)
    password: str = Field(..., min_length=1, max_length=200)


class AuthUser(BaseModel):
    user_id: str
    name: str
    email: str


class AuthResponse(BaseModel):
    user: AuthUser
    message: str
