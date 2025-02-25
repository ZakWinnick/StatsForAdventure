import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Awaitable

from rivian import Rivian, VehicleCommand
from rivian.exceptions import RivianApiException, RivianInvalidOTP

logger = logging.getLogger(__name__)

class RivianClient:
    """Wrapper around the Rivian Python Client library."""
    
    def __init__(self, timeout: int = 30):
        """Initialize the Rivian client."""
        self.timeout = timeout
        self.client = None
        self.vehicles = {}
        self.subscriptions = {}
        self.user_info = None
    
    async def initialize(self, 
                         access_token: str = "", 
                         refresh_token: str = "", 
                         csrf_token: str = "", 
                         app_session_token: str = "", 
                         user_session_token: str = ""):
        """Initialize the Rivian client with existing tokens."""
        if self.client:
            await self.client.close()
            
        self.client = Rivian(
            request_timeout=self.timeout,
            access_token=access_token,
            refresh_token=refresh_token,
            csrf_token=csrf_token,
            app_session_token=app_session_token,
            user_session_token=user_session_token
        )
        
        # If we have tokens, fetch user information
        if access_token and user_session_token:
            await self.get_user_info()
            
        return self.client
    
    async def authenticate(self, username: str, password: str) -> Dict[str, str]:
        """Authenticate with Rivian using email and password."""
        if not self.client:
            self.client = Rivian(request_timeout=self.timeout)
            
        # Create CSRF token first
        await self.client.create_csrf_token()
        
        # Try to login
        await self.client.authenticate(username, password)
        
        # Check if MFA/OTP is needed
        if self.client._otp_needed:
            return {
                'otp_needed': True,
                'otp_token': self.client._otp_token,
                'csrf_token': self.client._csrf_token,
                'app_session_token': self.client._app_session_token
            }
        else:
            # Authentication successful without OTP
            tokens = {
                'otp_needed': False,
                'access_token': self.client._access_token,
                'refresh_token': self.client._refresh_token,
                'user_session_token': self.client._user_session_token,
                'csrf_token': self.client._csrf_token,
                'app_session_token': self.client._app_session_token
            }
            
            # Fetch user information
            await self.get_user_info()
            
            return tokens
    
    async def validate_otp(self, username: str, otp_code: str) -> Dict[str, str]:
        """Validate OTP code for MFA."""
        if not self.client or not self.client._otp_needed:
            raise Exception("OTP validation called without proper setup")
            
        await self.client.validate_otp(username, otp_code)
        
        tokens = {
            'access_token': self.client._access_token,
            'refresh_token': self.client._refresh_token,
            'user_session_token': self.client._user_session_token,
            'csrf_token': self.client._csrf_token,
            'app_session_token': self.client._app_session_token
        }
        
        # Fetch user information
        await self.get_user_info()
        
        return tokens
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get user information including vehicles."""
        if not self.client:
            raise Exception("Client not initialized")
            
        response = await self.client.get_user_information(include_phones=True)
        data = await response.json()
        
        if "data" in data and "currentUser" in data["data"]:
            self.user_info = data["data"]["currentUser"]
            
            # Process vehicles
            self.vehicles = {}
            for vehicle in self.user_info.get("vehicles", []):
                vehicle_id = vehicle.get("id")
                if vehicle_id:
                    self.vehicles[vehicle_id] = vehicle
            
            return self.user_info
        else:
            logger.error(f"Failed to get user info: {data}")
            raise Exception("Failed to get user information")
    
    async def get_vehicle_state(self, vehicle_id: str) -> Dict[str, Any]:
        """Get the current state of a vehicle."""
        if not self.client:
            raise Exception("Client not initialized")
            
        response = await self.client.get_vehicle_state(vehicle_id)
        data = await response.json()
        
        if "data" in data and "vehicleState" in data["data"]:
            return data["data"]["vehicleState"]
        else:
            logger.error(f"Failed to get vehicle state: {data}")
            raise Exception("Failed to get vehicle state")
    
    async def get_live_charging_session(self, vehicle_id: str) -> Dict[str, Any]:
        """Get live charging session data if available."""
        if not self.client:
            raise Exception("Client not initialized")
            
        response = await self.client.get_live_charging_session(vehicle_id)
        data = await response.json()
        
        if "data" in data and "getLiveSessionData" in data["data"]:
            return data["data"]["getLiveSessionData"]
        else:
            logger.error(f"Failed to get charging data: {data}")
            return None  # No charging session active
    
    async def subscribe_to_vehicle_updates(self, 
                                          vehicle_id: str, 
                                          callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """Subscribe to vehicle update notifications."""
        if not self.client:
            raise Exception("Client not initialized")
            
        # If we already have a subscription for this vehicle, cancel it
        if vehicle_id in self.subscriptions:
            await self.unsubscribe_from_vehicle_updates(vehicle_id)
            
        # Create a new subscription
        unsubscribe = await self.client.subscribe_for_vehicle_updates(vehicle_id, callback)
        
        if unsubscribe:
            self.subscriptions[vehicle_id] = unsubscribe
            logger.info(f"Subscribed to updates for vehicle: {vehicle_id}")
        else:
            logger.error(f"Failed to subscribe to vehicle updates: {vehicle_id}")
    
    async def unsubscribe_from_vehicle_updates(self, vehicle_id: str) -> None:
        """Unsubscribe from vehicle updates."""
        if vehicle_id in self.subscriptions:
            unsubscribe_func = self.subscriptions[vehicle_id]
            await unsubscribe_func()
            del self.subscriptions[vehicle_id]
            logger.info(f"Unsubscribed from updates for vehicle: {vehicle_id}")
    
    async def send_vehicle_command(self, 
                                  command: VehicleCommand, 
                                  vehicle_id: str, 
                                  phone_id: str, 
                                  identity_id: str, 
                                  vehicle_key: str, 
                                  private_key: str, 
                                  params: Dict[str, Any] = None) -> str:
        """Send a command to the vehicle."""
        if not self.client:
            raise Exception("Client not initialized")
            
        command_id = await self.client.send_vehicle_command(
            command=command,
            vehicle_id=vehicle_id,
            phone_id=phone_id,
            identity_id=identity_id,
            vehicle_key=vehicle_key,
            private_key=private_key,
            params=params
        )
        
        return command_id
    
    async def get_command_status(self, command_id: str) -> Dict[str, Any]:
        """Get the status of a previously sent command."""
        if not self.client:
            raise Exception("Client not initialized")
            
        response = await self.client.get_vehicle_command_state(command_id)
        data = await response.json()
        
        if "data" in data and "getVehicleCommand" in data["data"]:
            return data["data"]["getVehicleCommand"]
        else:
            logger.error(f"Failed to get command status: {data}")
            raise Exception("Failed to get command status")
    
    async def close(self) -> None:
        """Close the Rivian client."""
        if self.client:
            # Unsubscribe from all vehicle updates
            for vehicle_id in list(self.subscriptions.keys()):
                await self.unsubscribe_from_vehicle_updates(vehicle_id)
                
            await self.client.close()
            self.client = None