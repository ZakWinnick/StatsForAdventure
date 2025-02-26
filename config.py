import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API settings
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*").split(",")
