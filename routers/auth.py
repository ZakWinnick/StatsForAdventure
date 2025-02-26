from fastapi import APIRouter, HTTPException, Form, Cookie, Response
from pydantic import BaseModel
from typing import Optional
import aiohttp
from rivian import Rivian

router = APIRouter(prefix="/api/auth", tags=["authentication"])

class TokenResponse(BaseModel):
    csrf_token: str
    app_session_token: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user_session_token: Optional[str] = None
    otp_needed: bool = False
    otp_token: Optional[str] = None

@router.post("/login", response_model=TokenResponse)
async def login(username: str = Form(...), password: str = Form(...)):
    """Log in to Rivian API"""
    try:
        async with aiohttp.ClientSession() as session:
            rivian = Rivian(session=session)
            await rivian.create_csrf_token()
            await rivian.authenticate(username, password)
            
            response = TokenResponse(
                csrf_token=rivian._csrf_token,
                app_session_token=rivian._app_session_token,
                access_token=rivian._access_token,
                refresh_token=rivian._refresh_token,
                user_session_token=rivian._user_session_token,
                otp_needed=rivian._otp_needed,
                otp_token=rivian._otp_token
            )
            return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/validate-otp", response_model=TokenResponse)
async def validate_otp(
    username: str = Form(...), 
    otp_code: str = Form(...), 
    otp_token: str = Form(...),
    csrf_token: str = Form(...),
    app_session_token: str = Form(...)
):
    """Validate OTP for Rivian login"""
    try:
        async with aiohttp.ClientSession() as session:
            rivian = Rivian(
                session=session,
                csrf_token=csrf_token,
                app_session_token=app_session_token
            )
            rivian._otp_token = otp_token
            await rivian.validate_otp(username, otp_code)
            
            response = TokenResponse(
                csrf_token=rivian._csrf_token,
                app_session_token=rivian._app_session_token,
                access_token=rivian._access_token,
                refresh_token=rivian._refresh_token,
                user_session_token=rivian._user_session_token,
                otp_needed=False
            )
            return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
