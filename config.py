# config.py (in your project root)
import os
from dotenv import load_dotenv

# Construct the path to the .env file, assuming it's in the project root
# This config.py file is also in the project root.
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

# Load the .env file if it exists
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    # Fallback if .env is not found, allows for vars to be set in the environment directly
    print("Warning: .env file not found. Relying on system environment variables.")
    load_dotenv()


class Config:
    """Base configuration settings."""
    # Flask Secret Key (for sessions, flash messages, etc. - good to have)
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'secret')

    # JWT Secret Key
    JWT_SECRET_KEY = os.getenv('JWT_KEY', 'secret')

    # Database URL
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./default_fallback.db') # Fallback if not set

    # Flask Environment (e.g., 'development', 'production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', '1') == '1' # Convert '1' or '0' to boolean

    # Add any other global configurations your application might need
    # For example:
    # MAIL_SERVER = os.getenv('MAIL_SERVER')
    # MAIL_PORT = int(os.getenv('MAIL_PORT', 587))