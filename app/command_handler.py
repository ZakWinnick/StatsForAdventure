"""
Vehicle command handler.
"""
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

from rivian import VehicleCommand
from .rivian_client import RivianClient

logger = logging.getLogger(__name__)

class CommandStatus(Enum):
    """Command status enum."""
    PENDING = 0
    EXECUTING = 1
    FAILED = 2
    COMPLETED = 3
    UNKNOWN = 4

class CommandHandler:
    """Handler for vehicle commands."""
    
    def __init__(self, rivian_client: RivianClient):
        """Initialize the command handler with a Rivian client."""
        self.client = rivian_client
        self.command_cache = {}
        
    async def execute_command(self, 
                             command: str, 
                             vehicle_id: str, 
                             phone_id: str,
                             identity_id: str,
                             vehicle_key: str,
                             private_key: str,
                             params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a vehicle command."""
        try:
            # Validate the command
            try:
                vehicle_command = VehicleCommand(command)
            except ValueError:
                logger.error(f"Invalid command: {command}")
                return {
                    'status': 'error',
                    'message': f"Invalid command: {command}"
                }
                
            # Send the command
            command_id = await self.client.send_vehicle_command(
                command=vehicle_command,
                vehicle_id=vehicle_id,
                phone_id=phone_id,
                identity_id=identity_id,
                vehicle_key=vehicle_key,
                private_key=private_key,
                params=params
            )
            
            if not command_id:
                logger.error("Failed to send command")
                return {
                    'status': 'error',
                    'message': "Failed to send command"
                }
                
            # Store command in cache
            self.command_cache[command_id] = {
                'command': command,
                'vehicle_id': vehicle_id,
                'status': CommandStatus.PENDING.value,
                'timestamp': datetime.now().isoformat(),
                'result': None
            }
            
            return {
                'status': 'success',
                'command_id': command_id,
                'message': f"Command {command} sent successfully"
            }
            
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                'status': 'error',
                'message': f"Error executing command: {str(e)}"
            }
    
    async def get_command_status(self, command_id: str) -> Dict[str, Any]:
        """Get the status of a command."""
        try:
            # Check cache first
            if command_id in self.command_cache:
                cached = self.command_cache[command_id]
                
                # If command is still pending, check for updates
                if cached['status'] in [CommandStatus.PENDING.value, CommandStatus.EXECUTING.value]:
                    status_data = await self.client.get_command_status(command_id)
                    
                    # Update cache with new status
                    if status_data:
                        status = status_data.get('state', CommandStatus.UNKNOWN.value)
                        cached['status'] = status
                        cached['result'] = status_data
                        self.command_cache[command_id] = cached
                
                return {
                    'status': 'success',
                    'command_id': command_id,
                    'command_status': cached['status'],
                    'command': cached['command'],
                    'timestamp': cached['timestamp'],
                    'result': cached['result']
                }
            else:
                # Not in cache, try to get from API
                status_data = await self.client.get_command_status(command_id)
                
                if status_data:
                    status = status_data.get('state', CommandStatus.UNKNOWN.value)
                    
                    # Add to cache
                    self.command_cache[command_id] = {
                        'command': status_data.get('command', 'unknown'),
                        'vehicle_id': status_data.get('vehicleId'),
                        'status': status,
                        'timestamp': status_data.get('createdAt', datetime.now().isoformat()),
                        'result': status_data
                    }
                    
                    return {
                        'status': 'success',
                        'command_id': command_id,
                        'command_status': status,
                        'command': status_data.get('command', 'unknown'),
                        'timestamp': status_data.get('createdAt'),
                        'result': status_data
                    }
                else:
                    logger.error(f"Command ID not found: {command_id}")
                    return {
                        'status': 'error',
                        'message': f"Command ID not found: {command_id}"
                    }
                    
        except Exception as e:
            logger.error(f"Error getting command status: {e}")
            return {
                'status': 'error',
                'message': f"Error getting command status: {str(e)}"
            }
    
    def clean_command_cache(self, max_age_hours: int = 24):
        """Clean up old commands from the cache."""
        now = datetime.now()
        to_remove = []
        
        for command_id, data in self.command_cache.items():
            timestamp = datetime.fromisoformat(data['timestamp'])
            age = now - timestamp
            
            # Remove if older than max age or completed/failed
            if (age.total_seconds() > max_age_hours * 3600 or 
                data['status'] in [CommandStatus.COMPLETED.value, CommandStatus.FAILED.value]):
                to_remove.append(command_id)
                
        for command_id in to_remove:
            self.command_cache.pop(command_id, None)
            
        logger.debug(f"Cleaned up {len(to_remove)} commands from cache")