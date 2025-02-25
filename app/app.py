import functools
import uuid
from flask import (
    Blueprint, flash, g, redirect, render_template, request,
    session, url_for, current_app, jsonify
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import asyncio

from .models import User
from .rivian_client import RivianClient

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
                    login_user(user)
                    
                    next_page = request.args.get('next')
                    if not next_page or next_page.startswith('/'):
                        next_page = url_for('main.dashboard')
                    return redirect(next_page)
                    
            except Exception as e:
                error = f"Authentication failed: {str(e)}"
                current_app.logger.error(f"Login error: {e}")
                
        flash(error, 'danger')
    
    return render_template('login.html')
    
@auth.route('/verify-otp', methods=('GET', 'POST'))
def verify_otp():
    """OTP verification route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if 'rivian_email' not in session or 'otp_token' not in session:
        flash('Please login again to receive a new verification code.', 'warning')
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
    
    return render_template('verify_otp.html')
    
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

@auth.before_app_request
def load_logged_in_user():
    """Load logged-in user before each request."""
    user_id = session.get('user_id')
    
    if user_id is None:
        g.user = None
    else:
        g.user = User.load_from_session(session)
        
        # If user has tokens but they need refreshing, redirect to login
        if g.user and g.user.is_authenticated() and g.user.requires_token_refresh():
            logout_user()
            session.clear()
            flash('Your session has expired. Please login again.', 'info')
            return redirect(url_for('auth.login'))
            
def login_required(view):
    """View decorator that redirects anonymous users to the login page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login', next=request.url))
            
        return view(**kwargs)
        
    return wrapped_view