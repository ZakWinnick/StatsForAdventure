"""
Socket.IO manager for real-time updates.
"""
import asyncio
import logging
import json
from typing import Dict, Any, Set
from flask import current_app

from .. import sio
from .auth import get_rivian_client

logger = logging.getLogger(__name__)

# Store active connections
connections = {}
# Track subscriptions per vehicle
vehicle_subscribers = {}
# Map sid to user_id
sid_to_user = {}


async def vehicle_update_callback(data: Dict[str, Any]):
    """Callback function for vehicle updates."""
    try:
        vehicle_id = data.get('vehicle_id')
        if not vehicle_id:
            return
            
        # Get subscribers for this vehicle
        sids = vehicle_subscribers.get(vehicle_id, set())
        if not sids:
            return
            
        # Emit update to all subscribers
        formatted_data = format_update_data(data)
        for sid in sids:
            await sio.emit('vehicle_update', formatted_data, room=sid)
            
        logger.debug(f"Sent update for vehicle {vehicle_id} to {len(sids)} subscribers")
        
    except Exception as e:
        logger.error(f"Error in vehicle update callback: {e}")


def format_update_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Format vehicle update data for the frontend."""
    # Format and sanitize data 
    # Extract only what we need to avoid sending sensitive information
    formatted = {}
    
    # Copy essential values and format them
    if 'vehicle_id' in data:
        formatted['vehicle_id'] = data['vehicle_id']
        
    if 'batteryLevel' in data:
        formatted['batteryLevel'] = {
            'value': data['batteryLevel'].get('value', 0),
            'unit': data['batteryLevel'].get('unit', '%')
        }
        
    if 'distanceToEmpty' in data:
        formatted['distanceToEmpty'] = {
            'value': data['distanceToEmpty'].get('value', 0),
            'unit': data['distanceToEmpty'].get('unit', 'mi')
        }
        
    if 'chargerState' in data:
        formatted['chargerState'] = {
            'value': data['chargerState'].get('value', 'unknown')
        }
        
    if 'powerState' in data:
        formatted['powerState'] = {
            'value': data['powerState'].get('value', 'unknown')
        }
        
    if 'gnssLocation' in data:
        formatted['gnssLocation'] = {
            'latitude': data['gnssLocation'].get('latitude', 0),
            'longitude': data['gnssLocation'].get('longitude', 0)
        }
    
    return formatted


@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    logger.info(f"Client connected: {sid}")
    connections[sid] = {
        'user_id': None,
        'vehicles': set()
    }


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {sid}")
    
    # Clean up subscriptions
    if sid in connections:
        for vehicle_id in connections[sid]['vehicles']:
            if vehicle_id in vehicle_subscribers:
                vehicle_subscribers[vehicle_id].discard(sid)
                
                # If no more subscribers, unsubscribe from Rivian API
                if not vehicle_subscribers[vehicle_id]:
                    try:
                        client = get_rivian_client()
                        await client.unsubscribe_from_vehicle_updates(vehicle_id)
                        logger.info(f"Unsubscribed from vehicle updates: {vehicle_id}")
                    except Exception as e:
                        logger.error(f"Error unsubscribing from vehicle updates: {e}")
        
        # Remove connection data
        del connections[sid]
    
    # Clean up user mapping
    if sid in sid_to_user:
        del sid_to_user[sid]


@sio.event
async def authenticate(sid, data):
    """Authenticate socket connection with user token."""
    try:
        user_id = data.get('user_id')
        access_token = data.get('access_token')
        
        if not user_id or not access_token:
            return {'error': 'Missing user_id or access_token'}
            
        # Store user_id
        connections[sid]['user_id'] = user_id
        sid_to_user[sid] = user_id
        
        return {'status': 'authenticated'}
        
    except Exception as e:
        logger.error(f"Socket authentication error: {e}")
        return {'error': str(e)}


@sio.event
async def subscribe_vehicle(sid, data):
    """Subscribe to vehicle updates."""
    try:
        vehicle_id = data.get('vehicle_id')
        if not vehicle_id:
            return {'error': 'Vehicle ID is required'}
            
        # Check if user is authenticated
        user_id = connections.get(sid, {}).get('user_id')
        if not user_id:
            return {'error': 'Authentication required'}
            
        # Add to subscribers
        if vehicle_id not in vehicle_subscribers:
            vehicle_subscribers[vehicle_id] = set()
            
        vehicle_subscribers[vehicle_id].add(sid)
        connections[sid]['vehicles'].add(vehicle_id)
        
        # Check if we need to create a subscription to Rivian API
        if len(vehicle_subscribers[vehicle_id]) == 1:
            # First subscriber, create subscription
            client = get_rivian_client()
            await client.subscribe_to_vehicle_updates(vehicle_id, vehicle_update_callback)
            logger.info(f"Subscribed to vehicle updates: {vehicle_id}")
            
        return {'status': 'subscribed'}
        
    except Exception as e:
        logger.error(f"Error subscribing to vehicle: {e}")
        return {'error': str(e)}


@sio.event
async def unsubscribe_vehicle(sid, data):
    """Unsubscribe from vehicle updates."""
    try:
        vehicle_id = data.get('vehicle_id')
        if not vehicle_id:
            return {'error': 'Vehicle ID is required'}
            
        # Remove from subscribers
        if vehicle_id in vehicle_subscribers:
            vehicle_subscribers[vehicle_id].discard(sid)
            
            # If no more subscribers, unsubscribe from Rivian API
            if not vehicle_subscribers[vehicle_id]:
                client = get_rivian_client()
                await client.unsubscribe_from_vehicle_updates(vehicle_id)
                logger.info(f"Unsubscribed from vehicle updates: {vehicle_id}")
                
        if sid in connections:
            connections[sid]['vehicles'].discard(vehicle_id)
            
        return {'status': 'unsubscribed'}
        
    except Exception as e:
        logger.error(f"Error unsubscribing from vehicle: {e}")
        return {'error': str(e)}