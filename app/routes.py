import asyncio
import json
from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request,
    session, url_for, current_app, jsonify
)
from flask_login import login_required, current_user

from .. import sio
from .auth import get_rivian_client
from .models import User
from rivian import VehicleCommand

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Landing page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page showing all vehicles."""
    client = get_rivian_client()
    
    # Initialize client with user tokens
    asyncio.run(client.initialize(
        access_token=current_user.rivian_tokens.get('access_token', ''),
        refresh_token=current_user.rivian_tokens.get('refresh_token', ''),
        csrf_token=current_user.rivian_tokens.get('csrf_token', ''),
        app_session_token=current_user.rivian_tokens.get('app_session_token', ''),
        user_session_token=current_user.rivian_tokens.get('user_session_token', '')
    ))
    
    # Get user info with vehicles
    user_info = None
    try:
        user_info = asyncio.run(client.get_user_info())
    except Exception as e:
        flash(f"Error retrieving vehicle information: {str(e)}", 'danger')
        return redirect(url_for('auth.logout'))
    
    return render_template('dashboard.html', user_info=user_info, vehicles=client.vehicles)

@main.route('/vehicle/<vehicle_id>')
@login_required
def vehicle_detail(vehicle_id):
    """Vehicle detail page."""
    client = get_rivian_client()
    
    # Initialize client with user tokens
    asyncio.run(client.initialize(
        access_token=current_user.rivian_tokens.get('access_token', ''),
        refresh_token=current_user.rivian_tokens.get('refresh_token', ''),
        csrf_token=current_user.rivian_tokens.get('csrf_token', ''),
        app_session_token=current_user.rivian_tokens.get('app_session_token', ''),
        user_session_token=current_user.rivian_tokens.get('user_session_token', '')
    ))
    
    # Get vehicle info
    vehicle = None
    try:
        # Get user info first to make sure we have vehicle data
        if not client.vehicles:
            asyncio.run(client.get_user_info())
            
        vehicle = client.vehicles.get(vehicle_id)
        if not vehicle:
            flash("Vehicle not found", 'danger')
            return redirect(url_for('main.dashboard'))
            
        # Get vehicle state
        vehicle_state = asyncio.run(client.get_vehicle_state(vehicle.get('vin')))
        
        # Get charging data if available
        charging_data = None
        try:
            charging_data = asyncio.run(client.get_live_charging_session(vehicle.get('vin')))
        except:
            # Ignore errors for charging data
            pass
            
        return render_template(
            'vehicle.html', 
            vehicle=vehicle, 
            vehicle_state=vehicle_state,
            charging_data=charging_data
        )
            
    except Exception as e:
        flash(f"Error retrieving vehicle details: {str(e)}", 'danger')
        return redirect(url_for('main.dashboard'))

@main.route('/api/vehicle/<vehicle_id>/state')
@login_required
def api_vehicle_state(vehicle_id):
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

@main.route('/api/vehicle/<vehicle_id>/charging')
@login_required
def api_vehicle_charging(vehicle_id):
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

@main.route('/api/vehicle/<vehicle_id>/command', methods=['POST'])
@login_required
def api_vehicle_command(vehicle_id):
    """API endpoint to send vehicle commands."""
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
        # Get POST data
        data = request.json
        if not data:
            return jsonify({'error': 'Missing request data'}), 400
            
        command = data.get('command')
        if not command:
            return jsonify({'error': 'Command is required'}), 400
            
        # Validate command exists in VehicleCommand enum
        try:
            vehicle_command = VehicleCommand(command)
        except ValueError:
            return jsonify({'error': f'Invalid command: {command}'}), 400
            
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
            
        # Send command
        command_id = asyncio.run(client.send_vehicle_command(
            command=vehicle_command,
            vehicle_id=vehicle_id,
            phone_id=phone_id,
            identity_id=identity_id,
            vehicle_key=vehicle_key,
            private_key=private_key,
            params=params
        ))
        
        if not command_id:
            return jsonify({'error': 'Failed to send command'}), 500
            
        return jsonify({'command_id': command_id})
        
    except Exception as e:
        current_app.logger.error(f"Error sending vehicle command: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/command/<command_id>')
@login_required
def api_command_status(command_id):
    """API endpoint to check command status."""
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
        # Get command status
        status = asyncio.run(client.get_command_status(command_id))
        return jsonify(status)
        
    except Exception as e:
        current_app.logger.error(f"Error checking command status: {e}")
        return jsonify({'error': str(e)}), 500

# Socket.IO event handlers for real-time updates
@sio.event
def connect(sid, environ):
    """Handle client connection."""
    current_app.logger.info(f"Client connected: {sid}")

@sio.event
def disconnect(sid):
    """Handle client disconnection."""
    current_app.logger.info(f"Client disconnected: {sid}")

@sio.event
def subscribe_vehicle(sid, data):
    """Subscribe to vehicle updates."""
    vehicle_id = data.get('vehicle_id')
    if not vehicle_id:
        return {'error': 'Vehicle ID is required'}
        
    # Start subscription in background
    # Note: This would need more complex session management in production
    # since we need to associate the Socket.IO session with the Flask session
    return {'status': 'subscription_requested'}