"""Vehicle command API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Body

from ..dependencies import require_rivian_auth
from ..schemas.session import SessionData
from ..schemas.vehicle import VehicleCommandRequest, VehicleCommandResponse
from ..services.rivian_client import rivian_service


router = APIRouter(prefix="/api/commands", tags=["commands"])


@router.post("", response_model=VehicleCommandResponse)
async def send_command(
    command_request: VehicleCommandRequest,
    session_data: SessionData = Depends(require_rivian_auth),
):
    """Send a command to the selected vehicle."""
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
    
    # For this demo, we'll need to provide dummy values for the command authentication
    # In a real app, these would need to be properly set up through Rivian's phone enrollment process
    
    # The following are placeholders - in a real implementation, these would need to be
    # properly obtained by enrolling a phone with Rivian
    phone_id = "dummy-phone-id"
    identity_id = "dummy-identity-id"
    vehicle_key = selected_vehicle.vehicle_public_key  # This is real
    
    # Private key would be generated and stored securely during phone enrollment
    private_key = "dummy-private-key"
    
    # Send the command
    success, command_id, message = await rivian_service.send_vehicle_command(
        tokens=session_data.rivian_tokens,
        vehicle_id=selected_vehicle.id,
        command_request=command_request,
        vas_vehicle_id=selected_vehicle.vas_vehicle_id,
        phone_id=phone_id,
        identity_id=identity_id,
        vehicle_key=vehicle_key,
        private_key=private_key
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
    
    return VehicleCommandResponse(
        success=True,
        message=message,
        command_id=command_id
    )


@router.get("/supported")
async def get_supported_commands(session_data: SessionData = Depends(require_rivian_auth)):
    """Get list of supported commands for the selected vehicle."""
    # This endpoint would ideally query Rivian for supported commands based on the vehicle
    # For now, we'll return a static list based on known commands
    from rivian import VehicleCommand
    
    # Convert enum members to a list of strings
    command_list = [str(command) for command in VehicleCommand]
    
    return {
        "commands": command_list,
        "command_details": {
            # Add details for commands that require parameters
            "CHARGING_LIMITS": {
                "parameters": {
                    "SOC_limit": {
                        "type": "integer",
                        "description": "Battery charge limit percentage (50-100)",
                        "min": 50,
                        "max": 100
                    }
                }
            },
            "CABIN_HVAC_DEFROST_DEFOG": {
                "parameters": {
                    "level": {
                        "type": "integer",
                        "description": "Defrost level (0-4 where 0=off)",
                        "min": 0,
                        "max": 4
                    }
                }
            },
            "CABIN_PRECONDITIONING_SET_TEMP": {
                "parameters": {
                    "HVAC_set_temp": {
                        "type": "number",
                        "description": "Temperature in Celsius (16-29, or 0 for LO, 63.5 for HI)",
                        "allowed_values": [0, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 63.5]
                    }
                }
            }
        }
    }