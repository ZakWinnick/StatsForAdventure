"""
Security utility functions for the application.
"""
import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, session, abort, current_app, g, redirect, url_for
from werkzeug.security import safe_str_cmp
import jwt

def generate_csrf_token():
    """Generate a new CSRF token."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

def validate_csrf(token):
    """Validate the CSRF token."""
    session_token = session.get('_csrf_token')
    if not session_token or not token or not safe_str_cmp(session_token, token):
        return False
    return True

def csrf_protect(f):
    """CSRF protection decorator for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            token = request.form.get('_csrf_token')
            if not token and request.is_json:
                token = request.json.get('_csrf_token')
            if not token and request.headers.get('X-CSRF-Token'):
                token = request.headers.get('X-CSRF-Token')
                
            if not validate_csrf(token):
                current_app.logger.warning(f"CSRF validation failed for {request.path}")
                abort(403)
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(max_requests=5, per_seconds=60):
    """Rate limiting decorator for routes."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            ip = request.remote_addr
            
            # Check if rate limit is reached
            current_time = datetime.now()
            key = f'rate_limit:{ip}:{request.path}'
            
            if key not in g:
                g.rate_limit = {}
                
            if key not in g.rate_limit:
                g.rate_limit[key] = []
                
            # Clean up old requests
            g.rate_limit[key] = [t for t in g.rate_limit[key] 
                               if current_time - t < timedelta(seconds=per_seconds)]
                               
            # Check if limit is reached
            if len(g.rate_limit[key]) >= max_requests:
                current_app.logger.warning(f"Rate limit reached for {ip} on {request.path}")
                abort(429)
                
            # Add current request
            g.rate_limit[key].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def generate_api_token(user_id, expiration_seconds=3600):
    """Generate an API token for WebSocket authentication."""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=expiration_seconds),
        'iat': datetime.utcnow(),
        'jti': secrets.token_hex(16)
    }
    
    token = jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    return token

def validate_api_token(token):
    """Validate an API token."""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        
        # Check if token is expired
        if datetime.utcnow() > datetime.fromtimestamp(payload['exp']):
            return None
            
        return payload['user_id']
        
    except jwt.PyJWTError:
        return None

def user_activity_timeout(max_idle_time=1800):
    """Check for user inactivity and log them out if needed."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'last_activity' in session:
            last_activity = datetime.fromisoformat(session['last_activity'])
            if datetime.now() - last_activity > timedelta(seconds=max_idle_time):
                # User was inactive for too long, log them out
                session.clear()
                return redirect(url_for('auth.login', timeout=1))
                
        # Update last activity time
        session['last_activity'] = datetime.now().isoformat()
        return f(*args, **kwargs)
    return decorated_function