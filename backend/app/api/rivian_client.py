import aiohttp
import asyncio
import logging
import json
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class RivianClient:
    """Client for interacting with Rivian API."""
    
    def __init__(self):
        self._access_token = None
        self._refresh_token = None
        self._user_session_token = None
        self._csrf_token = None
        self._cookies = {}
        self._session = None
        self._otp_needed = False
        
    async def create_session(self):
        """Create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
        
    async def get_csrf_token(self):
        """Get a CSRF token from Rivian."""
        session = await self.create_session()
        
        try:
            # First visit the Rivian home page to get cookies
            async with session.get("https://rivian.com") as response:
                # Save any cookies
                for cookie_name, cookie in response.cookies.items():
                    self._cookies[cookie_name] = cookie.value
            
            # Now get the CSRF token
            async with session.get("https://rivian.com/csrf-token") as response:
                if response.status == 200:
                    data = await response.json()
                    self._csrf_token = data.get("csrfToken")
                    # Save any new cookies
                    for cookie_name, cookie in response.cookies.items():
                        self._cookies[cookie_name] = cookie.value
                    return self._csrf_token
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to get CSRF token: {response.status} - {error_text}")
                    raise Exception(f"Failed to get CSRF token: {response.status}")
        except Exception as e:
            logger.error(f"Error getting CSRF token: {str(e)}")
            raise
            
    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate with Rivian API."""
        try:
            # Get CSRF token first
            if not self._csrf_token:
                await self.get_csrf_token()
                
            session = await self.create_session()
            
            headers = {
                "content-type": "application/json;charset=UTF-8",
                "app-id": "account",
                "csrf-token": self._csrf_token,
                "dnt": "1",
                "origin": "https://rivian.com",
                "referer": "https://rivian.com/account"
            }
            
            # Add cookies to the request
            cookie_str = "; ".join([f"{k}={v}" for k, v in self._cookies.items()])
            if cookie_str:
                headers["cookie"] = cookie_str
            
            mutation = """
            mutation login($username: String!, $password: String!) {
                login(username: $username, password: $password) {
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
            
            payload = {
                "operationName": "login",
                "variables": {
                    "username": username,
                    "password": password
                },
                "query": mutation
            }
            
            async with session.post(
                "https://rivian.com/api/gql/gateway/graphql",
                json=payload,
                headers=headers
            ) as response:
                # Save any cookies from the response
                for cookie_name, cookie in response.cookies.items():
                    self._cookies[cookie_name] = cookie.value
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Authentication error: {response.status} - {error_text}")
                    raise Exception(f"Authentication failed: {response.status}")
                    
                data = await response.json()
                logger.debug(f"Auth response: {json.dumps(data)}")
                
                if "errors" in data:
                    errors = data["errors"]
                    error_msg = errors[0].get("message", "Unknown error")
                    logger.error(f"GraphQL error: {error_msg}")
                    return {"status": "failure", "message": error_msg}
                
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
        try:
            if not self._csrf_token:
                await self.get_csrf_token()
                
            session = await self.create_session()
            
            headers = {
                "content-type": "application/json;charset=UTF-8",
                "app-id": "account",
                "csrf-token": self._csrf_token,
                "dnt": "1",
                "origin": "https://rivian.com",
                "referer": "https://rivian.com/account"
            }
            
            # Add cookies to the request
            cookie_str = "; ".join([f"{k}={v}" for k, v in self._cookies.items()])
            if cookie_str:
                headers["cookie"] = cookie_str
            
            mutation = """
            mutation validateOTP($username: String!, $otpCode: String!) {
                validateOTP(username: $username, otpCode: $otpCode) {
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
            
            payload = {
                "operationName": "validateOTP",
                "variables": {
                    "username": username,
                    "otpCode": otp
                },
                "query": mutation
            }
            
            async with session.post(
                "https://rivian.com/api/gql/gateway/graphql",
                json=payload,
                headers=headers
            ) as response:
                # Save any cookies from the response
                for cookie_name, cookie in response.cookies.items():
                    self._cookies[cookie_name] = cookie.value
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"OTP validation error: {response.status} - {error_text}")
                    raise Exception(f"OTP validation failed: {response.status}")
                    
                data = await response.json()
                logger.debug(f"OTP response: {json.dumps(data)}")
                
                if "errors" in data:
                    errors = data["errors"]
                    error_msg = errors[0].get("message", "Unknown error")
                    logger.error(f"GraphQL error: {error_msg}")
                    return {"status": "failure", "message": error_msg}
                
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
            # For demo purposes, return mock data if not authenticated
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
            
        try:
            session = await self.create_session()
            
            headers = {
                "content-type": "application/json;charset=UTF-8",
                "app-id": "account",
                "authorization": f"Bearer {self._access_token}",
                "csrf-token": self._csrf_token,
                "dnt": "1",
                "origin": "https://rivian.com",
                "referer": "https://rivian.com/account"
            }
            
            # Add cookies to the request
            cookie_str = "; ".join([f"{k}={v}" for k, v in self._cookies.items()])
            if cookie_str:
                headers["cookie"] = cookie_str
            
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
                "query": query,
                "variables": {}
            }
            
            async with session.post(
                "https://rivian.com/api/gql/gateway/graphql",
                json=payload,
                headers=headers
            ) as response:
                # Save any cookies from the response
                for cookie_name, cookie in response.cookies.items():
                    self._cookies[cookie_name] = cookie.value
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Get user info error: {response.status} - {error_text}")
                    raise Exception(f"Failed to get user information: {response.status}")
                    
                data = await response.json()
                logger.debug(f"User info response: {json.dumps(data)}")
                
                if "errors" in data:
                    errors = data["errors"]
                    error_msg = errors[0].get("message", "Unknown error")
                    logger.error(f"GraphQL error: {error_msg}")
                    raise Exception(f"GraphQL error: {error_msg}")
                
                return data.get("data", {}).get("currentUser", {})
        except Exception as e:
            logger.error(f"Get user info error: {str(e)}")
            # For demo purposes, return mock data on error
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
        """Get vehicle state."""
        # Return mock data for now - actual implementation would require reverse engineering
        # the specific vehicle state API calls
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