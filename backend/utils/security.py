"""Security utilities."""

import json
import time
from typing import Dict, Optional
import base64

from cryptography.fernet import Fernet
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired

from ..config import settings
from ..schemas.session import SessionData


# Create a signer for session tokens
signer = TimestampSigner(settings.SESSION_SECRET_KEY)

# Create a Fernet cipher for encrypting session data
fernet = Fernet(base64.urlsafe_b64encode(settings.SECRET_KEY.encode()[:32].ljust(32, b' ')))


def create_session_token(session_data: SessionData) -> str:
    """
    Create a session token containing encrypted session data.
    
    The token consists of:
    1. A timestamp signature (for expiration validation)
    2. Encrypted session data (for confidentiality)
    """
    # Serialize and encrypt the session data
    session_json = json.dumps(session_data.model_dump())
    encrypted_data = fernet.encrypt(session_json.encode())
    
    # Sign the encrypted data with a timestamp
    token = signer.sign(encrypted_data).decode()
    
    return token


def verify_session_token(token: str) -> bool:
    """Verify a session token's signature and expiration."""
    try:
        # Verify the token signature and check if it's expired
        signer.unsign(token, max_age=settings.SESSION_MAX_AGE)
        return True
    except (BadSignature, SignatureExpired):
        return False


def decrypt_session_data(token: str) -> Optional[SessionData]:
    """Decrypt session data from a token."""
    try:
        # Unsign the token to get the encrypted data
        signed_data = signer.unsign(token, max_age=settings.SESSION_MAX_AGE)
        
        # Decrypt the data
        decrypted_data = fernet.decrypt(signed_data)
        session_dict = json.loads(decrypted_data.decode())
        
        # Convert to SessionData object
        return SessionData(**session_dict)
    except (BadSignature, SignatureExpired, json.JSONDecodeError):
        return None