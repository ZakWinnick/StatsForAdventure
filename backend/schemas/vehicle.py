"""Vehicle data schemas."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class VehicleState(BaseModel):
    """Vehicle state data."""
    
    battery_level: Optional[float] = None
    battery_limit: Optional[int] = None
    distance_to_empty: Optional[int] = None
    is_online: Optional[bool] = None
    power_state: Optional[str] = None
    gear_status: Optional[str] = None
    vehicle_mileage: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    charger_state: Optional[str] = None
    time_to_end_of_charge: Optional[float] = None
    
    # Door and closure states
    doors_locked: Optional[bool] = None
    doors_closed: Optional[bool] = None
    frunk_locked: Optional[bool] = None
    frunk_closed: Optional[bool] = None
    gear_guard_locked: Optional[bool] = None
    windows_closed: Optional[bool] = None
    
    # Climate states
    cabin_climate_interior_temp: Optional[float] = None
    cabin_preconditioning_status: Optional[str] = None
    
    # Updated timestamp
    last_updated: Optional[datetime] = None


class VehicleCommandRequest(BaseModel):
    """Vehicle command request."""
    
    command: str
    params: Optional[Dict[str, Any]] = None


class VehicleCommandResponse(BaseModel):
    """Vehicle command response."""
    
    success: bool
    message: str
    command_id: Optional[str] = None


class ChargingSessionData(BaseModel):
    """Live charging session data."""
    
    charging_status: Optional[str] = None
    power: Optional[float] = None
    current: Optional[float] = None
    range_added: Optional[float] = None
    soc: Optional[float] = None
    time_remaining: Optional[int] = None
    total_energy: Optional[float] = None
    is_rivian_charger: Optional[bool] = None
    
    # Updated timestamp
    last_updated: Optional[datetime] = None