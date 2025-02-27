import aiohttp
import asyncio
import logging
import json
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class RivianClient:
    """Mock client for Rivian API."""
    
    def __init__(self):
        self._access_token = None
        self._refresh_token = None
        self._user_session_token = None
        self._session = None
        self._otp_needed = False
        self._authenticated = False
        
    async def create_session(self):
        """Create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
            
    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate with Rivian API (mock)."""
        logger.info(f"Mock authentication for user: {username}")
        # For demo purposes, always require OTP
        self._otp_needed = True
        return {
            "status": "otp_required", 
            "data": {
                "maskedEmail": username.replace(username[3:6], "***"),
                "maskedPhone": "+1******1234"
            }
        }
            
    async def validate_otp(self, username: str, otp: str) -> Dict[str, Any]:
        """Validate OTP code (mock)."""
        logger.info(f"Mock OTP validation for user: {username}, code: {otp}")
        # Any OTP is considered valid for the demo
        self._authenticated = True
        return {
            "status": "success",
            "data": {
                "accessToken": "mock-access-token",
                "refreshToken": "mock-refresh-token",
                "userSessionToken": "mock-session-token"
            }
        }
            
    async def get_user_information(self, include_phones: bool = False) -> Dict[str, Any]:
        """Get user information including vehicles (mock)."""
        if not self._authenticated:
            logger.warning("Attempted to get user info when not authenticated")
            return {"error": "Not authenticated"}
            
        # Return mock user data
        return {
            "id": "user123",
            "firstName": "Demo",
            "lastName": "User",
            "email": "demo@example.com",
            "vehicles": [
                {
                    "id": "vehicle1",
                    "name": "My Rivian R1T",
                    "vehicle": {
                        "vin": "1R9VA1A13MC000001",
                        "id": "vehicleId1",
                        "model": "R1T"
                    }
                },
                {
                    "id": "vehicle2",
                    "name": "My Rivian R1S",
                    "vehicle": {
                        "vin": "1R9VA2A13MC000002",
                        "id": "vehicleId2",
                        "model": "R1S"
                    }
                }
            ]
        }
            
    async def get_vehicle_state(self, vin: str, properties: list) -> Dict[str, Any]:
        """Get vehicle state (mock)."""
        if not self._authenticated:
            logger.warning("Attempted to get vehicle state when not authenticated")
            return {"error": "Not authenticated"}
            
        # Return mock vehicle data
        return {
            "vin": vin,
            "properties": {
                "batteryLevel": {
                    "value": 85,
                    "timeStamp": "2025-02-27T12:30:00Z"
                },
                "distanceToEmpty": {
                    "value": 280,
                    "timeStamp": "2025-02-27T12:30:00Z"
                },
                "vehicleMileage": {
                    "value": 12500,
                    "timeStamp": "2025-02-27T12:30:00Z"
                },
                "powerState": {
                    "value": "ready",
                    "timeStamp": "2025-02-27T12:30:00Z"
                },
                "chargerStatus": {
                    "value": "chrgr_sts_not_connected",
                    "timeStamp": "2025-02-27T12:30:00Z"
                },
                "chargerState": {
                    "value": "not_charging",
                    "timeStamp": "2025-02-27T12:30:00Z"
                },
                "cabinClimateInteriorTemperature": {
                    "value": 22,
                    "timeStamp": "2025-02-27T12:30:00Z"
                },
                "timeToEndOfCharge": {
                    "value": 0,
                    "timeStamp": "2025-02-27T12:30:00Z"
                }
            }
        }
            
    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()