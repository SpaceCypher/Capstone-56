import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime

from app.db.mongo import get_database


_PASSWORD_ITERATIONS = 120_000


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _PASSWORD_ITERATIONS,
    )
    return salt, digest.hex()


def _verify_password(password: str, salt: str, password_hash: str) -> bool:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _PASSWORD_ITERATIONS,
    )
    return hmac.compare_digest(digest.hex(), password_hash)


async def init_auth_indexes() -> None:
    users = get_database()["users"]
    await users.create_index([("email", 1)], unique=True)
    await users.create_index([("user_id", 1)], unique=True)


async def signup_user(name: str, email: str, password: str) -> dict:
    users = get_database()["users"]
    normalized_email = _normalize_email(email)

    existing = await users.find_one({"email": normalized_email}, {"_id": 1})
    if existing:
        raise ValueError("Email already registered")

    salt, password_hash = _hash_password(password)
    now = datetime.now(UTC)
    user_id = str(uuid.uuid4())

    await users.insert_one(
        {
            "user_id": user_id,
            "name": name.strip(),
            "email": normalized_email,
            "password_salt": salt,
            "password_hash": password_hash,
            "created_at": now,
            "updated_at": now,
        }
    )

    return {
        "user_id": user_id,
        "name": name.strip(),
        "email": normalized_email,
    }


async def login_user(email: str, password: str) -> dict:
    users = get_database()["users"]
    normalized_email = _normalize_email(email)

    user = await users.find_one({"email": normalized_email})
    if not user:
        raise PermissionError("Invalid email or password")

    salt = str(user.get("password_salt", ""))
    password_hash = str(user.get("password_hash", ""))
    if not salt or not password_hash or not _verify_password(password, salt, password_hash):
        raise PermissionError("Invalid email or password")

    return {
        "user_id": str(user.get("user_id", "")),
        "name": str(user.get("name", "")),
        "email": str(user.get("email", normalized_email)),
    }
