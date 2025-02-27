from fastapi import APIRouter, HTTPException, Depends, Request, Response, status, Body
from typing import Dict, List, Optional, Any
from ..api.rivian_client import RivianClient
import logging
import json
from pydantic import BaseModel

router = APIRouter()
client = RivianClient()

class LoginRequest(BaseModel):
    username: str
    password: str

class OTPRequest(BaseModel):
    username: str
    otp: str

@router.post("/login")
async def login(request: LoginRequest):
    try:
        result = await client.authenticate(request.username, request.password)
        return result
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-otp")
async def validate_otp(request: OTPRequest):
    try:
        result = await client.validate_otp(request.username, request.otp)
        return result
    except Exception as e:
        logging.error(f"OTP validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user")
async def get_user_info():
    try:
        result = await client.get_user_information()
        return result
    except Exception as e:
        logging.error(f"Get user info error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Define the properties for vehicle state that we're interested in
VEHICLE_STATE_PROPERTIES = [
    "batteryLevel", 
    "distanceToEmpty", 
    "gnssLocation", 
    "gnssSpeed", 
    "powerState",
    "vehicleMileage",
    "chargerStatus",
    "chargerState",
    "timeToEndOfCharge",
    "cabinClimateInteriorTemperature",
    "cabinPreconditioningStatus",
    "defrostDefogStatus",
    "petModeStatus",
    "driveMode"
]

@router.get("/vehicle/{vin}")
async def get_vehicle_state(vin: str):
    try:
        result = await client.get_vehicle_state(vin, VEHICLE_STATE_PROPERTIES)
        return result
    except Exception as e:
        logging.error(f"Get vehicle state error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout")
async def logout():
    """Log out the user."""
    # Reset the client's tokens
    client._access_token = None
    client._refresh_token = None
    client._user_session_token = None
    client._csrf_token = None
    client._cookies = {}
    return {"status": "success"}