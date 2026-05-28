"""
Authentication endpoints for SophiaAI.

Executive Brief:
    POST /auth/register — create a new user, return a JWT.
    POST /auth/login    — verify credentials, return a JWT.
    No session cookies, no OAuth flows — pure token exchange.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from sophia.app.dependencies import get_db_session
from sophia.app.schemas import LoginRequest, RegisterRequest, TokenResponse
from sophia.auth.security import create_access_token, hash_password, verify_password
from sophia.db.service import create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(
    body: RegisterRequest,
    request: Request,
    session: Session = Depends(get_db_session),
) -> TokenResponse:
    """
    Executive Brief:
        Register a new user. Hash the password, store in DB,
        return a JWT so the user is immediately logged in.
    """
    existing_user = get_user_by_email(session, body.email)
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed = hash_password(body.password)
    user = create_user(session, body.email, hashed)

    jwt_secret = request.app.state.jwt_secret
    token = create_access_token(subject=user.email, secret_key=jwt_secret)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    request: Request,
    session: Session = Depends(get_db_session),
) -> TokenResponse:
    """
    Executive Brief:
        Authenticate an existing user. Verify password against the
        stored hash, return a JWT on success.
    """
    user = get_user_by_email(session, body.email)
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    jwt_secret = request.app.state.jwt_secret
    token = create_access_token(subject=user.email, secret_key=jwt_secret)
    return TokenResponse(access_token=token)
