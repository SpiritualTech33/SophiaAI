"""
FastAPI dependency injection functions for SophiaAI.

Executive Brief:
    Two dependencies that thread through every protected endpoint:
    get_db_session yields a SQLAlchemy session per request (auto-closed),
    get_authenticated_user extracts + validates the JWT and returns the User.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from sophia.auth.dependencies import get_current_user as _get_current_user
from sophia.db.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db_session(request: Request):
    """
    Executive Brief:
        Yield a SQLAlchemy session from the app-level session factory.
        The session is closed after the request completes, whether
        it succeeded or raised.
    """
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_authenticated_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db_session),
) -> User:
    """
    Executive Brief:
        Extract the Bearer token from the Authorization header,
        decode the JWT, look up the user in the database, and return
        the User ORM instance. Raises HTTP 401 on any failure.
    """
    jwt_secret = request.app.state.jwt_secret
    try:
        return _get_current_user(token, jwt_secret, session)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error))
