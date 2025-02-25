"""
Authentication routes for the application.
"""
import functools
import uuid
from datetime import datetime, timedelta
from flask import (
    Blueprint, flash, g, redirect, render_template, request,
    session, url_for, current_app, jsonify, abort
)
from flask_login import login_user, logout_user, login_required, current_user
import asyncio

from ..models import User
from ..rivian_client import RivianClient
from ..security import (
    generate_csrf_token, csrf_protect, rate_limit, 
    generate_api_token, user_activity_timeout
)

auth = Blueprint('auth', __name__, url_prefix='/auth')

# Rivian client instance
rivian_client = None

def get_rivian_client():
    """Get or create the Rivian client instance."""
    global rivian_client
    if rivian_client is None:
        rivian_client = RivianClient(timeout=current_app.config['RIVIAN_API_TIMEOUT'])
    return rivian_client

@auth.route('/login', methods=('GET', 'POST'))
@rate_limit(max_requests=10, per_seconds=60)  # Limit login attempts
def login():
    """User login route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        error = None
        
        if not email or not password:
            error = 'Email and password are required.'
            
        if error is None:
            try:
                # Authenticate with Rivian
                client = get_rivian_client()
                result = asyncio.run(client.authenticate(email, password))
                
                if result.get('otp_needed'):
                    # Store info needed for OTP verification
                    session['rivian_email'] = email
                    session['otp_token'] = result.get('otp_token')
                    session['csrf_token'] = result.get('csrf_token')
                    session['app_session_token'] = result.get('app_session_token')
                    
                    # Set last activity timestamp
                    session['last_activity'] = datetime.now().isoformat()
                    
                    # Redirect to OTP verification page
                    return redirect(url_for('auth.verify_otp'))
                    
                else:
                    # Create and login user
                    user = User(id=str(uuid.uuid4()), rivian_email=email)
                    user.store_rivian_tokens(
                        result.get('access_token'),
                        result.get('refresh_token'),
                        result.get('user_session_token'),
                        result.get('app_session_token'),
                        result.get('csrf_token')
                    )
                    user.save_to_session(session)
                    
                    # Set last activity timestamp
                    session['last_activity'] = datetime.now().isoformat()
                    
                    # Generate CSRF token
                    generate_csrf_token()
                    
                    login_user(user)
                    
                    next_page = request.args.get('next')
                    if not next_page or not next_page.startswith('/'):
                        next_page = url_for('main.dashboard')
                    return redirect(next_page)
                    
            except Exception as e:
                error = f"Authentication failed: {str(e)}"
                current_app.logger.error(f"Login error: {e}")
                
        flash(error, 'danger')
    
    # Generate CSRF token for the form
    csrf_token = generate_csrf_token()
    return render_template('login.html', csrf_token=csrf_token)
    
@auth.route('/verify-otp', methods=('GET', 'POST'))
@rate_limit(max_requests=5, per_seconds=60)  # Limit OTP attempts
def verify_otp():
    """OTP verification route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if 'rivian_email' not in session or 'otp_token' not in session:
        flash('Please login again to receive a new verification code.', 'warning')
        return redirect(url_for('auth.login'))
        
    # Check if OTP has expired (10 minutes)
    if 'last_activity' in session:
        last_activity = datetime.fromisoformat(session['last_activity'])
        if datetime.now() - last_activity > timedelta(minutes=10):
            # OTP has expired
            flash('Verification code has expired. Please login again.', 'warning')
            session.clear()
            return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        otp_code = request.form['otp_code']
        error = None
        
        if not otp_code:
            error = 'Verification code is required.'
            
        if error is None:
            try:
                email = session['rivian_email']
                
                # Initialize client with stored tokens
                client = get_rivian_client()
                await client.initialize(
                    csrf_token=session.get('csrf_token', ''),
                    app_session_token=session.get('app_session_token', '')
                )
                
                # Validate OTP
                result = asyncio.run(client.validate_otp(email, otp_code))
                
                # Create and login user
                user = User(id=str(uuid.uuid4()), rivian_email=email)
                user.store_rivian_tokens(
                    result.get('access_token'),
                    result.get('refresh_token'),
                    result.get('user_session_token'),
                    result.get('app_session_token'),
                    result.get('csrf_token')
                )
                user.save_to_session(session)
                
                # Set last activity timestamp
                session['last_activity'] = datetime.now().isoformat()
                
                # Generate CSRF token
                generate_csrf_token()
                
                login_user(user)
                
                # Clean up session
                session.pop('rivian_email', None)
                session.pop('otp_token', None)
                session.pop('csrf_token', None)
                session.pop('app_session_token', None)
                
                return redirect(url_for('main.dashboard'))
                
            except Exception as e:
                error = f"Verification failed: {str(e)}"
                current_app.logger.error(f"OTP verification error: {e}")
                
        flash(error, 'danger')
    
    # Generate CSRF token for the form
    csrf_token = generate_csrf_token()
    return render_template('verify_otp.html', csrf_token=csrf_token)
    
@auth.route('/logout')
@login_required
def logout():
    """User logout route."""
    # Clean up Rivian client
    client = get_rivian_client()
    asyncio.run(client.close())
    
    logout_user()
    # Clear session
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/api/token', methods=['POST'])
@login_required
@csrf_protect
def get_api_token():
    """Get a short-lived API token for WebSocket authentication."""
    try:
        # Generate a 10-minute token
        token = generate_api_token(current_user.id, expiration_seconds=600)
        
        return jsonify({
            'token': token,
            'expires_in': 600
        })
    except Exception as e:
        current_app.logger.error(f"Error generating API token: {e}")
        return jsonify({'error': 'Failed to generate token'}), 500

@auth.before_app_request
def load_logged_in_user():
    """Load logged-in user before each request."""
    user_id = session.get('user_id')
    
    if user_id is None:
        g.user = None
    else:
        g.user = User.load_from_session(session)
        
        # Update last activity time
        if hasattr(g, 'user') and g.user:
            session['last_activity'] = datetime.now().isoformat()
        
        # If user has tokens but they need refreshing, redirect to login
        if g.user and g.user.is_authenticated() and g.user.requires_token_refresh():
            logout_user()
            session.clear()
            flash('Your session has expired. Please login again.', 'info')
            return redirect(url_for('auth.login'))

@auth.app_template_filter('csrf_token')
def get_csrf_token(f):
    """Template filter to get the CSRF token."""
    return generate_csrf_token()