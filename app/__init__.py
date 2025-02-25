import os
from flask import Flask
from flask_login import LoginManager
import socketio

from .config import config

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Create Socket.IO server
sio = socketio.Server(async_mode='threading', cors_allowed_origins='*')

def create_app(config_name=None):
    """Create the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    login_manager.init_app(app)
    
    # Create instance directory
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Register blueprints
    from .routes import main
    from .auth import auth
    
    app.register_blueprint(main)
    app.register_blueprint(auth)
    
    # Wrap with Socket.IO middleware
    app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)
    
    return app