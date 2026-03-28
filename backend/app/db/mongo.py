import os
from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        _client = AsyncIOMotorClient(mongo_uri)
    return _client


def get_database() -> AsyncIOMotorDatabase:
    global _db
    if _db is None:
        db_name = os.getenv("MONGODB_DB", "adaptive_learning")
        _db = get_mongo_client()[db_name]
    return _db


async def init_diagnostics_indexes() -> None:
    diagnostics = get_database()["diagnostics"]
    await diagnostics.create_index([("user_id", 1), ("topic", 1), ("created_at", -1)])


async def save_diagnostic_record(record: dict[str, Any]) -> str:
    diagnostics = get_database()["diagnostics"]
    payload = {**record, "created_at": datetime.now(UTC)}
    result = await diagnostics.insert_one(payload)
    return str(result.inserted_id)
