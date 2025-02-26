from fastapi import APIRouter, HTTPException, Depends, Header, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any
import aiohttp
from rivian import Rivian, VehicleCommand

router = APIRouter(prefix="/api/commands", tags=["commands"])

class TokenData(BaseModel):
    csrf_token: str
    app_session_token: str
    user_session_token: str

async def get_rivian_client(
    x_csrf_token: str = Header(...),
    x_app_session_token: str = Header(...),
    x_user_session_token: str = Header(...)
):
    token_data = TokenData(
        csrf_token=x_csrf_token,
        app_session_token=x_app_session_token,
        user_session_token=x_user_session_token
    )
    async with aiohttp.ClientSession() as session:
        rivian = Rivian(
            session=session,
            csrf_token=token_data.csrf_token,
            app_session_token=token_data.app_session_token,
            user_session_token=token_data.user_session_token
        )
        return rivian

@router.post("/send")
async def send_command(
    vehicle_id: str = Form(...),
    command: str = Form(...),
    phone_id: str = Form(...),
    identity_id: str = Form(...),
    vehicle_key: str = Form(...),
    private_key: str = Form(...),
    params: Optional[str] = Form(None),
    rivian: Rivian = Depends(get_rivian_client)
):
    """Send a command to the vehicle"""
    try:
        # Parse params if provided
        params_dict = {}
        if params:
            import json
            params_dict = json.loads(params)
            
        # Send the command
        command_id = await rivian.send_vehicle_command(
            command=command,
            vehicle_id=vehicle_id,
            phone_id=phone_id,
            identity_id=identity_id,
            vehicle_key=vehicle_key,
            private_key=private_key,
            params=params_dict
        )
        
        return {"command_id": command_id, "status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status/{command_id}")
async def get_command_status(
    command_id: str, 
    rivian: Rivian = Depends(get_rivian_client)
):
    """Get the status of a sent command"""
    try:
        response = await rivian.get_vehicle_command_state(command_id)
        return await response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/available")
async def get_available_commands():
    """Get a list of available vehicle commands"""
    commands = [cmd.name for cmd in VehicleCommand]
    commands_info = {
        "WAKE_VEHICLE": {"description": "Wake up the vehicle", "params": {}},
        "HONK_AND_FLASH_LIGHTS": {"description": "Honk and flash lights", "params": {}},
        "CHARGING_LIMITS": {
            "description": "Set charging limit",
            "params": {"SOC_limit": "50-100 (percentage)"}
        },
        "START_CHARGING": {"description": "Start charging", "params": {}},
        "STOP_CHARGING": {"description": "Stop charging", "params": {}},
        # Add more commands with their descriptions and parameters
    }
    
    return {"commands": commands, "commands_info": commands_info}
