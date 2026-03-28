from pathlib import Path
import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware

from app.db.mongo import init_diagnostics_indexes
from app.routes.auth import router as auth_router
from app.routes.diagnostic import router as diagnostic_router
from app.routes.health import router as health_router
from app.routes.learning import router as learning_router
from app.routes.user_history import router as user_history_router
from app.services.user_auth_service import init_auth_indexes
from app.services.user_history_service import init_user_history_indexes

load_dotenv()
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="Behavior-Driven Adaptive Learning API", version="0.1.0")
logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.exception("Unhandled server error: %s", exc)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ErrorHandlingMiddleware)


@app.on_event("startup")
async def startup() -> None:
    await init_diagnostics_indexes()
    await init_auth_indexes()
    await init_user_history_indexes()

app.include_router(health_router)
app.include_router(learning_router)
app.include_router(diagnostic_router)
app.include_router(auth_router)
app.include_router(user_history_router)
