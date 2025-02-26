"""Authentication schemas."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator


class RivianAuthRequest(BaseModel):
    """Rivian authentication request."""
    
    email: EmailStr
    password: str


class OTPVerificationRequest(BaseModel):
    """OTP verification request."""
    
    otp_code: str = Field(..., min_length=6, max_length=8)


class AuthResponse(BaseModel):
    """Authentication response."""
    
    success: bool
    message: str
    requires_otp: bool = False