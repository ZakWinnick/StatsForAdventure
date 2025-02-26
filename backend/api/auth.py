"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse

from ..dependencies import get_session_data
from ..schemas.auth import RivianAuthRequest, OTPVerificationRequest, AuthResponse
from ..schemas.session import SessionData, RivianTokens
from ..services.rivian_client import rivian_service
from ..utils.security import create_session_token


router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=AuthResponse)
async def login(
    auth_request: RivianAuthRequest,
    response: Response,
    session_data: SessionData = Depends(get_session_data),
):
    """Authenticate with Rivian."""
    # Try to authenticate with Rivian
    success, tokens, message = await rivian_service.authenticate(
        auth_request.email, auth_request.password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )
    
    # Update session data
    if session_data is None:
        session_data = SessionData()
    
    # Check if OTP is needed
    if tokens.otp_needed:
        session_data.otp_pending = True
        session_data.rivian_tokens = tokens
        
        # Create session token
        session_token = create_session_token(session_data)
        
        # Set cookie
        response.set_cookie(
            key="session",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=1800,  # 30 minutes
        )
        
        return AuthResponse(
            success=True,
            message="OTP verification required",
            requires_otp=True,
        )
    
    # Successfully authenticated
    session_data.rivian_authenticated = True
    session_data.rivian_tokens = tokens
    
    # Fetch vehicles
    vehicles_success, vehicles, vehicles_message = await rivian_service.get_vehicles(tokens)
    if vehicles_success and vehicles:
        session_data.vehicles = vehicles
        if vehicles:
            session_data.selected_vehicle_id = vehicles[0].id
    
    # Create session token
    session_token = create_session_token(session_data)
    
    # Set cookie
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=1800,  # 30 minutes
    )
    
    return AuthResponse(
        success=True,
        message="Authentication successful",
        requires_otp=False,
    )


@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp(
    otp_request: OTPVerificationRequest,
    response: Response,
    session_data: SessionData = Depends(get_session_data),
):
    """Verify OTP code."""
    if not session_data or not session_data.otp_pending or not session_data.rivian_tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP verification pending",
        )
    
    # Extract authentication data from session
    tokens = session_data.rivian_tokens
    
    # Try to validate OTP
    success, updated_tokens, message = await rivian_service.validate_otp(
        "", otp_request.otp_code, tokens
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )
    
    # Update session data
    session_data.otp_pending = False
    session_data.rivian_authenticated = True
    session_data.rivian_tokens = updated_tokens
    
    # Fetch vehicles
    vehicles_success, vehicles, vehicles_message = await rivian_service.get_vehicles(updated_tokens)
    if vehicles_success and vehicles:
        session_data.vehicles = vehicles
        if vehicles:
            session_data.selected_vehicle_id = vehicles[0].id
    
    # Create session token
    session_token = create_session_token(session_data)
    
    # Set cookie
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=1800,  # 30 minutes
    )
    
    return AuthResponse(
        success=True,
        message="OTP verification successful",
        requires_otp=False,
    )


@router.post("/logout")
async def logout(response: Response):
    """Log out by clearing session."""
    response.delete_cookie(key="session")
    return {"success": True, "message": "Logged out successfully"}


@router.get("/session-status")
async def session_status(session_data: SessionData = Depends(get_session_data)):
    """Check current session status."""
    if not session_data:
        return {
            "authenticated": False,
            "otp_pending": False,
            "message": "No active session",
        }
    
    return {
        "authenticated": session_data.rivian_authenticated,
        "otp_pending": session_data.otp_pending,
        "message": "Session active",
        "vehicle_count": len(session_data.vehicles),
        "selected_vehicle": session_data.selected_vehicle_id,
    }