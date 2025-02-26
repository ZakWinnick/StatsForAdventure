"""Session data schemas."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RivianTokens(BaseModel):
    """Rivian authentication tokens."""
    
    access_token: str
    refresh_token: str
    csrf_token: str
    app_session_token: str
    user_session_token: str
    # For MFA
    otp_needed: bool = False
    otp_token: Optional[str] = None


class VehicleBasicInfo(BaseModel):
    """Basic vehicle information stored in session."""
    
    id: str
    vin: str
    name: str
    model: str
    model_year: Optional[int] = None
    vas_vehicle_id: str
    vehicle_public_key: str


class SessionData(BaseModel):
    """User session data."""
    
    rivian_authenticated: bool = False
    otp_pending: bool = False
    rivian_tokens: Optional[RivianTokens] = None
    selected_vehicle_id: Optional[str] = None
    vehicles: List[VehicleBasicInfo] = Field(default_factory=list)