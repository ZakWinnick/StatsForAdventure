"""Rivian API client service."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

import aiohttp
from rivian import Rivian
from rivian.exceptions import RivianApiException, RivianInvalidOTP

from ..schemas.session import RivianTokens, VehicleBasicInfo
from ..schemas.vehicle import VehicleState, ChargingSessionData, VehicleCommandRequest


class RivianClientService:
    """Service for interacting with the Rivian API."""
    
    def __init__(self):
        """Initialize the service."""
        self.client_session = None
        
    async def get_client_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp client session."""
        if self.client_session is None or self.client_session.closed:
            self.client_session = aiohttp.ClientSession()
        return self.client_session
    
    async def close(self):
        """Close the client session."""
        if self.client_session and not self.client_session.closed:
            await self.client_session.close()
    
    async def authenticate(self, email: str, password: str) -> Tuple[bool, Optional[RivianTokens], str]:
        """
        Authenticate with Rivian.
        
        Returns:
            Tuple containing:
            - Success flag
            - RivianTokens if successful, or None
            - Error message or success message
        """
        try:
            session = await self.get_client_session()
            rivian = Rivian(session=session)
            
            # Create CSRF token
            await rivian.create_csrf_token()
            
            # Authenticate
            await rivian.authenticate(email, password)
            
            # Check if OTP is needed
            if rivian._otp_needed:
                tokens = RivianTokens(
                    access_token="",
                    refresh_token="",
                    csrf_token=rivian._csrf_token,
                    app_session_token=rivian._app_session_token,
                    user_session_token="",
                    otp_needed=True,
                    otp_token=rivian._otp_token
                )
                return True, tokens, "OTP verification required"
            
            # Authentication successful
            tokens = RivianTokens(
                access_token=rivian._access_token,
                refresh_token=rivian._refresh_token,
                csrf_token=rivian._csrf_token,
                app_session_token=rivian._app_session_token,
                user_session_token=rivian._user_session_token,
                otp_needed=False
            )
            return True, tokens, "Authentication successful"
            
        except RivianApiException as e:
            return False, None, f"Authentication failed: {str(e)}"
        except Exception as e:
            return False, None, f"Unexpected error: {str(e)}"
    
    async def validate_otp(
        self, email: str, otp_code: str, tokens: RivianTokens
    ) -> Tuple[bool, Optional[RivianTokens], str]:
        """
        Validate OTP with Rivian.
        
        Returns:
            Tuple containing:
            - Success flag
            - Updated RivianTokens if successful, or None
            - Error message or success message
        """
        try:
            session = await self.get_client_session()
            rivian = Rivian(
                session=session,
                csrf_token=tokens.csrf_token,
                app_session_token=tokens.app_session_token
            )
            rivian._otp_token = tokens.otp_token
            
            # Validate OTP
            await rivian.validate_otp(email, otp_code)
            
            # Update tokens
            updated_tokens = RivianTokens(
                access_token=rivian._access_token,
                refresh_token=rivian._refresh_token,
                csrf_token=rivian._csrf_token,
                app_session_token=rivian._app_session_token,
                user_session_token=rivian._user_session_token,
                otp_needed=False
            )
            return True, updated_tokens, "OTP validation successful"
            
        except RivianInvalidOTP:
            return False, None, "Invalid OTP code"
        except RivianApiException as e:
            return False, None, f"OTP validation failed: {str(e)}"
        except Exception as e:
            return False, None, f"Unexpected error: {str(e)}"
    
    async def get_vehicles(self, tokens: RivianTokens) -> Tuple[bool, Optional[List[VehicleBasicInfo]], str]:
        """
        Get list of user's vehicles.
        
        Returns:
            Tuple containing:
            - Success flag
            - List of VehicleBasicInfo if successful, or None
            - Error message or success message
        """
        try:
            session = await self.get_client_session()
            rivian = Rivian(
                session=session,
                csrf_token=tokens.csrf_token,
                app_session_token=tokens.app_session_token,
                user_session_token=tokens.user_session_token
            )
            
            # Get user information (includes vehicles)
            response = await rivian.get_user_information()
            data = await response.json()
            
            vehicles = []
            if "data" in data and "currentUser" in data["data"]:
                user_data = data["data"]["currentUser"]
                if "vehicles" in user_data:
                    for vehicle in user_data["vehicles"]:
                        vehicles.append(VehicleBasicInfo(
                            id=vehicle["id"],
                            vin=vehicle["vin"],
                            name=vehicle["name"],
                            model=vehicle["vehicle"]["model"],
                            model_year=vehicle["vehicle"].get("modelYear"),
                            vas_vehicle_id=vehicle["vas"]["vasVehicleId"],
                            vehicle_public_key=vehicle["vas"]["vehiclePublicKey"]
                        ))
            
            return True, vehicles, "Retrieved vehicles successfully"
            
        except RivianApiException as e:
            return False, None, f"Failed to get vehicles: {str(e)}"
        except Exception as e:
            return False, None, f"Unexpected error: {str(e)}"
    
    async def get_vehicle_state(
        self, tokens: RivianTokens, vin: str
    ) -> Tuple[bool, Optional[VehicleState], str]:
        """
        Get vehicle state.
        
        Returns:
            Tuple containing:
            - Success flag
            - VehicleState if successful, or None
            - Error message or success message
        """
        try:
            session = await self.get_client_session()
            rivian = Rivian(
                session=session,
                csrf_token=tokens.csrf_token,
                app_session_token=tokens.app_session_token,
                user_session_token=tokens.user_session_token
            )
            
            # Get vehicle state
            response = await rivian.get_vehicle_state(vin)
            data = await response.json()
            
            if "data" in data and "vehicleState" in data["data"]:
                vehicle_data = data["data"]["vehicleState"]
                
                # Extract values with timestamps
                def extract_value(field):
                    if field in vehicle_data and vehicle_data[field] and "value" in vehicle_data[field]:
                        return vehicle_data[field]["value"]
                    return None
                
                # Process online status
                is_online = False
                if "cloudConnection" in vehicle_data and vehicle_data["cloudConnection"]:
                    is_online = vehicle_data["cloudConnection"].get("lastSync") is not None
                
                # Process location
                latitude = None
                longitude = None
                if "gnssLocation" in vehicle_data and vehicle_data["gnssLocation"]:
                    latitude = vehicle_data["gnssLocation"].get("latitude")
                    longitude = vehicle_data["gnssLocation"].get("longitude")
                
                # Handle door locks aggregation
                doors_locked = True
                if extract_value("doorFrontLeftLocked") != "locked" or \
                   extract_value("doorFrontRightLocked") != "locked" or \
                   extract_value("doorRearLeftLocked") != "locked" or \
                   extract_value("doorRearRightLocked") != "locked":
                    doors_locked = False
                
                # Handle door closed aggregation
                doors_closed = True
                if extract_value("doorFrontLeftClosed") != "closed" or \
                   extract_value("doorFrontRightClosed") != "closed" or \
                   extract_value("doorRearLeftClosed") != "closed" or \
                   extract_value("doorRearRightClosed") != "closed":
                    doors_closed = False
                
                # Handle windows closed aggregation
                windows_closed = True
                if extract_value("windowFrontLeftClosed") != "closed" or \
                   extract_value("windowFrontRightClosed") != "closed" or \
                   extract_value("windowRearLeftClosed") != "closed" or \
                   extract_value("windowRearRightClosed") != "closed":
                    windows_closed = False
                
                # Create vehicle state
                state = VehicleState(
                    battery_level=extract_value("batteryLevel"),
                    battery_limit=extract_value("batteryLimit"),
                    distance_to_empty=extract_value("distanceToEmpty"),
                    is_online=is_online,
                    power_state=extract_value("powerState"),
                    gear_status=extract_value("gearStatus"),
                    vehicle_mileage=extract_value("vehicleMileage"),
                    latitude=latitude,
                    longitude=longitude,
                    charger_state=extract_value("chargerState"),
                    time_to_end_of_charge=extract_value("timeToEndOfCharge"),
                    doors_locked=doors_locked,
                    doors_closed=doors_closed,
                    frunk_locked=extract_value("closureFrunkLocked") == "locked",
                    frunk_closed=extract_value("closureFrunkClosed") == "closed",
                    gear_guard_locked=extract_value("gearGuardLocked") == "locked",
                    windows_closed=windows_closed,
                    cabin_climate_interior_temp=extract_value("cabinClimateInteriorTemperature"),
                    cabin_preconditioning_status=extract_value("cabinPreconditioningStatus"),
                    last_updated=datetime.utcnow()
                )
                
                return True, state, "Retrieved vehicle state successfully"
            
            return False, None, "Failed to parse vehicle state data"
            
        except RivianApiException as e:
            return False, None, f"Failed to get vehicle state: {str(e)}"
        except Exception as e:
            return False, None, f"Unexpected error: {str(e)}"
    
    async def get_charging_session(
        self, tokens: RivianTokens, vin: str
    ) -> Tuple[bool, Optional[ChargingSessionData], str]:
        """
        Get live charging session data.
        
        Returns:
            Tuple containing:
            - Success flag
            - ChargingSessionData if successful, or None
            - Error message or success message
        """
        try:
            session = await self.get_client_session()
            rivian = Rivian(
                session=session,
                csrf_token=tokens.csrf_token,
                app_session_token=tokens.app_session_token,
                user_session_token=tokens.user_session_token
            )
            
            # Get charging session data
            response = await rivian.get_live_charging_session(vin)
            data = await response.json()
            
            if "data" in data and "getLiveSessionData" in data["data"]:
                charging_data = data["data"]["getLiveSessionData"]
                
                # Extract values from records
                def extract_record_value(field):
                    if field in charging_data and charging_data[field] and "value" in charging_data[field]:
                        return charging_data[field]["value"]
                    return None
                
                # Create charging session data
                session_data = ChargingSessionData(
                    charging_status=extract_record_value("vehicleChargerState"),
                    power=extract_record_value("power"),
                    current=extract_record_value("current"),
                    range_added=extract_record_value("rangeAddedThisSession"),
                    soc=extract_record_value("soc"),
                    time_remaining=extract_record_value("timeRemaining"),
                    total_energy=extract_record_value("totalChargedEnergy"),
                    is_rivian_charger=charging_data.get("isRivianCharger"),
                    last_updated=datetime.utcnow()
                )
                
                return True, session_data, "Retrieved charging session data successfully"
            
            return False, None, "No active charging session or failed to parse data"
            
        except RivianApiException as e:
            return False, None, f"Failed to get charging session: {str(e)}"
        except Exception as e:
            return False, None, f"Unexpected error: {str(e)}"
    
    async def send_vehicle_command(
        self, tokens: RivianTokens, vehicle_id: str, command_request: VehicleCommandRequest,
        vas_vehicle_id: str, phone_id: str, identity_id: str, vehicle_key: str, private_key: str
    ) -> Tuple[bool, Optional[str], str]:
        """
        Send a command to a vehicle.
        
        Returns:
            Tuple containing:
            - Success flag
            - Command ID if successful, or None
            - Error message or success message
        """
        try:
            session = await self.get_client_session()
            rivian = Rivian(
                session=session,
                csrf_token=tokens.csrf_token,
                app_session_token=tokens.app_session_token,
                user_session_token=tokens.user_session_token
            )
            
            # Send command
            command_id = await rivian.send_vehicle_command(
                command=command_request.command,
                vehicle_id=vehicle_id,
                phone_id=phone_id,
                identity_id=identity_id,
                vehicle_key=vehicle_key,
                private_key=private_key,
                params=command_request.params
            )
            
            if command_id:
                return True, command_id, f"Command {command_request.command} sent successfully"
            
            return False, None, f"Failed to send command {command_request.command}"
            
        except RivianApiException as e:
            return False, None, f"Failed to send command: {str(e)}"
        except Exception as e:
            return False, None, f"Unexpected error: {str(e)}"


# Create a singleton instance
rivian_service = RivianClientService()