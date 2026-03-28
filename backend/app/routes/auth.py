from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    AuthLoginRequest,
    AuthResponse,
    AuthSignupRequest,
    AuthUser,
)
from app.services.user_auth_service import login_user, signup_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
async def signup(payload: AuthSignupRequest):
    try:
        user = await signup_user(payload.name, payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return AuthResponse(
        message="Signup successful",
        user=AuthUser(**user),
    )


@router.post("/login", response_model=AuthResponse)
async def login(payload: AuthLoginRequest):
    try:
        user = await login_user(payload.email, payload.password)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return AuthResponse(
        message="Login successful",
        user=AuthUser(**user),
    )
