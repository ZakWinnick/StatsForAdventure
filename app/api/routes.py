"""
API routes for the application.
"""
import asyncio
from flask import (
    Blueprint, request, jsonify, current_app, g
)
from flask_login import login_required, current_user

from ..auth import get_rivian_client
from ..command_handler import CommandHandler
from ..security import csrf_protect

api = Blueprint('api', __name__, url_prefix='/api')

# Initialize command handler
command_handler = None

def get_command_handler():
    """Get or create the command handler instance."""
    global command_handler
    if command_handler is None:
        client = get_rivian_client()
        command_handler = CommandHandler(client)
    return command_handler

@api.route('/vehicle/<vehicle_id>/state')
@login_required
def vehicle_state(vehicle_id):
    """API endpoint for vehicle state."""
    client = get_rivian_client()
    
    # Initialize client with user tokens
    asyncio.run(client.initialize(
        access_token=current_user.rivian_tokens.get('access_token', ''),
        refresh_token=current_user.rivian_tokens.get('refresh_token', ''),
        csrf_token=current_user.rivian_tokens.get('csrf_token', ''),
        app_session_token=current_user.rivian_tokens.get('app_session_token', ''),
        user_session_token=current_user.rivian_tokens.get('user_session_token', '')
    ))
    
    try:
        # Get vehicle info
        if not client.vehicles:
            asyncio.run(client.get_user_info())
            
        vehicle = client.vehicles.get(vehicle_id)
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
            
        # Get vehicle state
        vehicle_state = asyncio.run(client.get_vehicle_state(vehicle.get('vin')))
        return jsonify(vehicle_state)
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving vehicle state: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/vehicle/<vehicle_id>/charging')
@login_required
def vehicle_charging(vehicle_id):
    """API endpoint for vehicle charging data."""
    client = get_rivian_client()
    
    # Initialize client with user tokens
    asyncio.run(client.initialize(
        access_token=current_user.rivian_tokens.get('access_token', ''),
        refresh_token=current_user.rivian_tokens.get('refresh_token', ''),
        csrf_token=current_user.rivian_tokens.get('csrf_token', ''),
        app_session_token=current_user.rivian_tokens.get('app_session_token', ''),
        user_session_token=current_user.rivian_tokens.get('user_session_token', '')
    ))
    
    try:
        # Get vehicle info
        if not client.vehicles:
            asyncio.run(client.get_user_info())
            
        vehicle = client.vehicles.get(vehicle_id)
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
            
        # Get charging data
        charging_data = asyncio.run(client.get_live_charging_session(vehicle.get('vin')))
        return jsonify(charging_data or {})
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving charging data: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/vehicle/<vehicle_id>/command', methods=['POST'])
@login_required
@csrf_protect
def vehicle_command(vehicle_id):
    """API endpoint to send vehicle commands."""
    client = get_rivian_client()
    handler = get_command_handler()
    
    # Initialize client with user tokens
    asyncio.run(client.initialize(
        access_token=current_user.rivian_tokens.get('access_token', ''),
        refresh_token=current_user.rivian_tokens.get('refresh_token', ''),
        csrf_token=current_user.rivian_tokens.get('csrf_token', ''),
        app_session_token=current_user.rivian_tokens.get('app_session_token', ''),
        user_session_token=current_user.rivian_tokens.get('user_session_token', '')
    ))
    
    try:
        # Get POST data
        data = request.json
        if not data:
            return jsonify({'error': 'Missing request data'}), 400
            
        command = data.get('command')
        if not command:
            return jsonify({'error': 'Command is required'}), 400
            
        # Get required parameters for sending commands
        phone_id = data.get('phone_id')
        identity_id = data.get('identity_id') 
        vehicle_key = data.get('vehicle_key')
        private_key = data.get('private_key')
        
        if not all([phone_id, identity_id, vehicle_key, private_key]):
            return jsonify({'error': 'Missing required parameters for command'}), 400
            
        # Get command params if any
        params = data.get('params')
        
        # Get vehicle info
        if not client.vehicles:
            asyncio.run(client.get_user_info())
            
        vehicle = client.vehicles.get(vehicle_id)
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
            
        # Execute command
        result = asyncio.run(handler.execute_command(
            command=command,
            vehicle_id=vehicle_id,
            phone_id=phone_id,
            identity_id=identity_id,
            vehicle_key=vehicle_key,
            private_key=private_key,
            params=params
        ))
        
        if result.get('status') == 'error':
            return jsonify({'error': result.get('message')}), 500
            
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error sending vehicle command: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/command/<command_id>')
@login_required
def command_status(command_id):
    """API endpoint to check command status."""
    client = get_rivian_client()
    handler = get_command_handler()
    
    # Initialize client with user tokens
    asyncio.run(client.initialize(
        access_token=current_user.rivian_tokens.get('access_token', ''),
        refresh_token=current_user.rivian_tokens.get('refresh_token', ''),
        csrf_token=current_user.rivian_tokens.get('csrf_token', ''),
        app_session_token=current_user.rivian_tokens.get('app_session_token', ''),
        user_session_token=current_user.rivian_tokens.get('user_session_token', '')
    ))
    
    try:
        # Get command status
        result = asyncio.run(handler.get_command_status(command_id))
        
        if result.get('status') == 'error':
            return jsonify({'error': result.get('message')}), 404
            
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error checking command status: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/vehicle/<vehicle_id>/commands/history')
@login_required
def command_history(vehicle_id):
    """API endpoint to get command history for a vehicle."""
    handler = get_command_handler()
    
    try:
        # Filter commands by vehicle_id
        commands = []
        for command_id, data in handler.command_cache.items():
            if data.get('vehicle_id') == vehicle_id:
                commands.append({
                    'command_id': command_id,
                    'command': data.get('command'),
                    'status': data.get('status'),
                    'timestamp': data.get('timestamp')
                })
                
        # Sort by timestamp (newest first)
        commands.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            'status': 'success',
            'commands': commands
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting command history: {e}")
        return jsonify({'error': str(e)}), 500