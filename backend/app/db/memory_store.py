import os
from collections import defaultdict
from datetime import datetime, UTC
from typing import Any

from app.models.schemas import AttemptPayload, LearningState
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.errors import PyMongoError


QUESTIONS: list[dict[str, Any]] = [
    {
        "question_id": "q-loops-1",
        "concept_id": "loops",
        "topic": "Loops",
        "prompt": "What is the output of: for i in range(3): print(i)",
        "expected_answer": "0 1 2",
        "difficulty": 1,
    },
    {
        "question_id": "q-loops-2",
        "concept_id": "loops",
        "topic": "Loops",
        "prompt": "How many times does while x < 5 run if x starts at 2 and increments by 1?",
        "expected_answer": "3",
        "difficulty": 1,
    },
    {
        "question_id": "q-loops-3",
        "concept_id": "loops",
        "topic": "Loops",
        "prompt": "Find the bug: loop never updates counter. What should be changed?",
        "expected_answer": "increment counter",
        "difficulty": 2,
    },
    {
        "question_id": "q-arrays-1",
        "concept_id": "arrays",
        "topic": "Arrays",
        "prompt": "What is the index of the first element in an array?",
        "expected_answer": "0",
        "difficulty": 1,
    },
    {
        "question_id": "q-arrays-2",
        "concept_id": "arrays",
        "topic": "Arrays",
        "prompt": "What is array length of [10, 20, 30, 40]?",
        "expected_answer": "4",
        "difficulty": 1,
    },
]


class MemoryStore:
    def __init__(self) -> None:
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGODB_DB", "adaptive_learning")
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[db_name]
        self.questions = self.db["questions"]
        self.interactions = self.db["interactions"]
        self.learning_states = self.db["learning_states"]
        self.cursors = self.db["question_cursors"]
        self._initialized = False

    def _execute(self, operation):
        try:
            self._ensure_initialized()
            return operation()
        except PyMongoError as exc:
            raise RuntimeError(
                "MongoDB operation failed. Ensure MongoDB is running and MONGODB_URI is correct."
            ) from exc

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return

        self.questions.create_index([("question_id", ASCENDING)], unique=True)
        self.interactions.create_index([("user_id", ASCENDING), ("concept_id", ASCENDING), ("timestamp", DESCENDING)])
        self.learning_states.create_index([("user_id", ASCENDING), ("concept_id", ASCENDING)], unique=True)

        for question in QUESTIONS:
            self.questions.update_one(
                {"question_id": question["question_id"]},
                {"$setOnInsert": question},
                upsert=True,
            )

        self._initialized = True

    def get_recent_attempts(self, user_id: str, concept_id: str, limit: int = 5) -> list[dict[str, Any]]:
        def _op() -> list[dict[str, Any]]:
            cursor = self.interactions.find(
                {"user_id": user_id, "concept_id": concept_id},
                {"_id": 0, "correct": 1},
            ).sort("timestamp", DESCENDING).limit(limit)
            return list(cursor)

        return self._execute(_op)

    def save_attempt(self, payload: AttemptPayload, state: LearningState, correct: bool) -> None:
        def _op() -> None:
            now = datetime.now(UTC)
            self.interactions.insert_one(
                {
                    "user_id": payload.user_id,
                    "concept_id": payload.concept_id,
                    "question_id": payload.question_id,
                    "correct": correct,
                    "state": state.value,
                    "timestamp": now,
                }
            )

            current = self.learning_states.find_one(
                {"user_id": payload.user_id, "concept_id": payload.concept_id},
                {"_id": 0, "mastery_level": 1},
            )
            current_mastery = 0.5 if not current else float(current.get("mastery_level", 0.5))

            if state == LearningState.MASTERY:
                current_mastery = min(1.0, current_mastery + 0.1)
            elif state == LearningState.STRUGGLING:
                current_mastery = max(0.0, current_mastery - 0.1)

            self.learning_states.update_one(
                {"user_id": payload.user_id, "concept_id": payload.concept_id},
                {
                    "$set": {
                        "mastery_level": current_mastery,
                        "last_updated": now,
                    }
                },
                upsert=True,
            )

        self._execute(_op)

    def _next_cursor_index(self, cursor_key: str) -> int:
        cursor_doc = self.cursors.find_one_and_update(
            {"_id": cursor_key},
            {"$inc": {"value": 1}},
            upsert=True,
            return_document=ReturnDocument.BEFORE,
        )
        if cursor_doc is None:
            return 0
        return int(cursor_doc.get("value", 0))

    def get_next_question(self, concept_id: str, easier: bool = False) -> dict[str, Any]:
        def _op() -> dict[str, Any]:
            query: dict[str, Any] = {"concept_id": concept_id}
            if easier:
                query["difficulty"] = 1

            pool = list(
                self.questions.find(query, {"_id": 0}).sort(
                    [("difficulty", ASCENDING), ("question_id", ASCENDING)]
                )
            )

            if not pool:
                fallback_query: dict[str, Any] = {"difficulty": 1} if easier else {}
                pool = list(
                    self.questions.find(fallback_query, {"_id": 0}).sort(
                        [("difficulty", ASCENDING), ("question_id", ASCENDING)]
                    )
                )

            if not pool:
                raise RuntimeError("No questions found in MongoDB. Seed data is missing.")

            cursor_key = f"{concept_id}:{'easy' if easier else 'normal'}"
            idx = self._next_cursor_index(cursor_key) % len(pool)
            return pool[idx]

        return self._execute(_op)

    def get_dashboard(self, user_id: str) -> dict[str, Any]:
        def _op() -> dict[str, Any]:
            rows = list(
                self.interactions.find(
                    {"user_id": user_id},
                    {"_id": 0, "state": 1, "concept_id": 1},
                )
            )
            state_breakdown: dict[str, int] = defaultdict(int)
            concept_state: dict[str, list[str]] = defaultdict(list)

            for row in rows:
                state_breakdown[row["state"]] += 1
                concept_state[row["concept_id"]].append(row["state"])

            weak_concepts: list[str] = []
            for concept_id, states in concept_state.items():
                struggles = sum(1 for s in states if s in {"struggling", "guessing"})
                if struggles >= 2:
                    weak_concepts.append(concept_id)

            return {
                "user_id": user_id,
                "total_interactions": len(rows),
                "state_breakdown": dict(state_breakdown),
                "weak_concepts": weak_concepts,
            }

        return self._execute(_op)


store = MemoryStore()
