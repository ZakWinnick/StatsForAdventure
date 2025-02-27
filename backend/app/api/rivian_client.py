import aiohttp
import asyncio
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class RivianClient:
    """Simplified client for the Rivian API."""
    
    BASE_URL = "https://rivian.com/api/gql/gateway/graphql"
    
    def __init__(self):
        self._access_token = None
        self._refresh_token = None
        self._user_session_token = None
        self._session = None
        self._otp_needed = False
        
    async def create_session(self):
        """Create an HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
        
    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate with Rivian API."""
        session = await self.create_session()
        headers = {
            "content-type": "application/json"
        }
        
        mutation = """
        mutation appLogin($input: LoginInput!) {
            login(input: $input) {
                __typename
                ... on LoginSuccess {
                    accessToken
                    refreshToken
                    userSessionToken
                }
                ... on LoginOTPRequired {
                    otpSettings {
                        otpReference
                        maskedEmail
                        maskedPhone
                    }
                }
                ... on LoginFailure {
                    message
                }
            }
        }
        """
        
        variables = {
            "input": {
                "username": username,
                "password": password
            }
        }
        
        payload = {
            "operationName": "appLogin",
            "variables": variables,
            "query": mutation
        }
        
        try:
            async with session.post(self.BASE_URL, json=payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Authentication failed: {response.status}")
                    
                data = await response.json()
                login_result = data.get("data", {}).get("login", {})
                
                typename = login_result.get("__typename")
                
                if typename == "LoginOTPRequired":
                    self._otp_needed = True
                    return {"status": "otp_required", "data": login_result.get("otpSettings", {})}
                    
                elif typename == "LoginSuccess":
                    self._access_token = login_result.get("accessToken")
                    self._refresh_token = login_result.get("refreshToken")
                    self._user_session_token = login_result.get("userSessionToken")
                    self._otp_needed = False
                    return {"status": "success", "data": login_result}
                    
                elif typename == "LoginFailure":
                    return {"status": "failure", "message": login_result.get("message")}
                    
                raise Exception(f"Unknown login response: {login_result}")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {"status": "failure", "message": str(e)}
            
    async def validate_otp(self, username: str, otp: str) -> Dict[str, Any]:
        """Validate OTP code."""
        session = await self.create_session()
        headers = {
            "content-type": "application/json"
        }
        
        mutation = """
        mutation validateOTP($input: ValidateOTPInput!) {
            validateOTP(input: $input) {
                __typename
                ... on ValidateOTPSuccess {
                    accessToken
                    refreshToken
                    userSessionToken
                }
                ... on ValidateOTPFailure {
                    errors {
                        message
                        extensions {
                            reason
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "input": {
                "username": username,
                "otpCode": otp
            }
        }
        
        payload = {
            "operationName": "validateOTP",
            "variables": variables,
            "query": mutation
        }
        
        try:
            async with session.post(self.BASE_URL, json=payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"OTP validation failed: {response.status}")
                    
                data = await response.json()
                result = data.get("data", {}).get("validateOTP", {})
                
                typename = result.get("__typename")
                
                if typename == "ValidateOTPSuccess":
                    self._access_token = result.get("accessToken")
                    self._refresh_token = result.get("refreshToken")
                    self._user_session_token = result.get("userSessionToken")
                    self._otp_needed = False
                    return {"status": "success", "data": result}
                    
                elif typename == "ValidateOTPFailure":
                    errors = result.get("errors", [])
                    message = errors[0].get("message") if errors else "OTP validation failed"
                    reason = errors[0].get("extensions", {}).get("reason") if errors else None
                    return {"status": "failure", "message": message, "reason": reason}
                    
                raise Exception(f"Unknown OTP validation response: {result}")
        except Exception as e:
            logger.error(f"OTP validation error: {str(e)}")
            return {"status": "failure", "message": str(e)}
            
    async def get_user_information(self, include_phones: bool = False) -> Dict[str, Any]:
        """Get user information including vehicles."""
        if not self._access_token:
            return {"error": "Not authenticated"}
            
        session = await self.create_session()
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "content-type": "application/json"
        }
        
        query = """
        query currentUser {
            currentUser {
                id
                firstName
                lastName
                email
                vehicles {
                    id
                    name
                    vehicle {
                        vin
                        id
                        model
                    }
                }
            }
        }
        """
        
        payload = {
            "operationName": "currentUser",
            "query": query
        }
        
        try:
            async with session.post(self.BASE_URL, json=payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to get user information: {response.status}")
                    
                data = await response.json()
                return data.get("data", {}).get("currentUser", {})
        except Exception as e:
            logger.error(f"Get user info error: {str(e)}")
            return {"error": str(e)}
            
    async def get_vehicle_state(self, vin: str, properties: list) -> Dict[str, Any]:
        """Get vehicle state (simplified mock version)."""
        # This is a simplified mock that returns example data
        # In a real implementation, this would connect to Rivian's API
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
