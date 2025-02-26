"""Vehicle data API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status, Path, Query

from ..dependencies import require_rivian_auth, require_session
from ..schemas.session import SessionData, VehicleBasicInfo
from ..schemas.vehicle import VehicleState, ChargingSessionData
from ..services.rivian_client import rivian_service
from ..utils.security import create_session_token


router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


@router.get("/list", response_model=List[VehicleBasicInfo])
async def list_vehicles(session_data: SessionData = Depends(require_rivian_auth)):
    """Get list of user's vehicles."""
    if not session_data.vehicles:
        # Try to fetch vehicles if not in session
        if not session_data.rivian_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated with Rivian",
            )
        
        success, vehicles, message = await rivian_service.get_vehicles(session_data.rivian_tokens)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message,
            )
        
        session_data.vehicles = vehicles
    
    return session_data.vehicles


@router.post("/select/{vehicle_id}")
async def select_vehicle(
    response: Response,
    vehicle_id: str = Path(...),
    session_data: SessionData = Depends(require_rivian_auth),
):
    """Select a vehicle as the active one."""
    # Verify vehicle exists in user's account
    vehicle_exists = False
    for vehicle in session_data.vehicles:
        if vehicle.id == vehicle_id:
            vehicle_exists = True
            break
    
    if not vehicle_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    
    # Update session
    session_data.selected_vehicle_id = vehicle_id
    
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
    
    return {"success": True, "message": "Vehicle selected successfully"}


@router.get("/state", response_model=VehicleState)
async def get_vehicle_state(session_data: SessionData = Depends(require_rivian_auth)):
    """Get current state of the selected vehicle."""
    if not session_data.selected_vehicle_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No vehicle selected",
        )
    
    # Find the vehicle in the session
    selected_vehicle = None
    for vehicle in session_data.vehicles:
        if vehicle.id == session_data.selected_vehicle_id:
            selected_vehicle = vehicle
            break
    
    if not selected_vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected vehicle not found",
        )
    
    # Fetch vehicle state
    success, state, message = await rivian_service.get_vehicle_state(
        session_data.rivian_tokens, selected_vehicle.vin
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
    
    return state


@router.get("/charging", response_model=Optional[ChargingSessionData])
async def get_charging_session(session_data: SessionData = Depends(require_rivian_auth)):
    """Get current charging session of the selected vehicle if active."""
    if not session_data.selected_vehicle_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No vehicle selected",
        )
    
    # Find the vehicle in the session
    selected_vehicle = None
    for vehicle in session_data.vehicles:
        if vehicle.id == session_data.selected_vehicle_id:
            selected_vehicle = vehicle
            break
    
    if not selected_vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected vehicle not found",
        )
    
    # Fetch charging session
    success, charging_data, message = await rivian_service.get_charging_session(
        session_data.rivian_tokens, selected_vehicle.vin
    )
    
    if not success:
        # This might just mean there's no active charging session
        return None
    
    return charging_data