from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import aiohttp
import logging
from rivian import Rivian

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])
logger = logging.getLogger(__name__)

class TokenData(BaseModel):
    csrf_token: str
    app_session_token: str
    user_session_token: str

async def get_rivian_client(
    x_csrf_token: str = Header(...),
    x_app_session_token: str = Header(...),
    x_user_session_token: str = Header(...),
    request: Request = None
):
    logger.info(f"Headers received: CSRF={x_csrf_token[:10]}..., App={x_app_session_token[:10]}..., User={x_user_session_token[:10]}...")
    
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

@router.get("/user-info")
async def get_user_info(rivian: Rivian = Depends(get_rivian_client)):
    """Get user information including vehicles"""
    try:
        logger.info("Fetching user information from Rivian API")
        response = await rivian.get_user_information()
        data = await response.json()
        logger.info(f"User info response status: {response.status}")
        
        if response.status != 200:
            logger.error(f"Error response from Rivian API: {data}")
            raise HTTPException(status_code=response.status, detail="Error from Rivian API")
            
        return data
    except Exception as e:
        logger.exception(f"Error fetching user info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{vin}/state")
async def get_vehicle_state(vin: str, rivian: Rivian = Depends(get_rivian_client)):
    """Get vehicle state"""
    try:
        response = await rivian.get_vehicle_state(vin)
        return await response.json()
    except Exception as e:
        logger.exception(f"Error fetching vehicle state: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{vin}/charging")
async def get_charging_session(vin: str, rivian: Rivian = Depends(get_rivian_client)):
    """Get live charging session data"""
    try:
        response = await rivian.get_live_charging_session(vin)
        return await response.json()
    except Exception as e:
        logger.exception(f"Error fetching charging session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
