"""FastAPI dependencies."""

from typing import Optional
from fastapi import Depends, Cookie, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.requests import Request

from .utils.security import decrypt_session_data, verify_session_token
from .schemas.session import SessionData


# Session handling
async def get_session_data(request: Request) -> Optional[SessionData]:
    """Get the current session data."""
    session_token = request.cookies.get("session")
    if not session_token:
        return None
    
    is_valid = verify_session_token(session_token)
    if not is_valid:
        return None
    
    session_data = decrypt_session_data(session_token)
    return session_data


async def require_session(
    session_data: Optional[SessionData] = Depends(get_session_data)
) -> SessionData:
    """Require a valid session."""
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return session_data


# Rivian authentication check
async def require_rivian_auth(
    session_data: SessionData = Depends(require_session)
) -> SessionData:
    """Require a valid Rivian authentication."""
    if not session_data.rivian_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated with Rivian",
        )
    return session_data