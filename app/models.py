from flask_login import UserMixin
from .. import login_manager
import json
import os
from datetime import datetime, timedelta

class User(UserMixin):
    """User model for authentication."""
    
    def __init__(self, id, rivian_email=None):
        self.id = id
        self.rivian_email = rivian_email
        self.rivian_tokens = {}
        self.last_login = datetime.now()
        
    def save_to_session(self, session):
        """Save user data to session."""
        session['user_id'] = self.id
        session['rivian_email'] = self.rivian_email
        session['rivian_tokens'] = self.rivian_tokens
        session['last_login'] = self.last_login.isoformat()
        
    @classmethod
    def load_from_session(cls, session):
        """Load user from session data."""
        if 'user_id' not in session:
            return None
            
        user = cls(id=session['user_id'])
        user.rivian_email = session.get('rivian_email')
        user.rivian_tokens = session.get('rivian_tokens', {})
        last_login_str = session.get('last_login')
        if last_login_str:
            user.last_login = datetime.fromisoformat(last_login_str)
        return user
        
    def is_authenticated(self):
        """Check if user is authenticated with Rivian."""
        return bool(self.rivian_tokens.get('access_token'))
        
    def requires_token_refresh(self):
        """Check if tokens need refreshing (older than 24 hours)."""
        if not self.last_login:
            return True
        return datetime.now() - self.last_login > timedelta(hours=24)
        
    def store_rivian_tokens(self, access_token, refresh_token, user_session_token, app_session_token, csrf_token):
        """Store Rivian authentication tokens."""
        self.rivian_tokens = {
            'access_token': access_token,
            'refresh_token': refresh_token, 
            'user_session_token': user_session_token,
            'app_session_token': app_session_token,
            'csrf_token': csrf_token
        }
        self.last_login = datetime.now()
        
@login_manager.user_loader
def load_user(user_id):
    """Load user function for Flask-Login."""
    from flask import session
    return User.load_from_session(session)