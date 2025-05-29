# run.py (in your project root)
from app import create_app # We will define create_app in app/__init__.py shortly
import os

# Create an application instance using the app factory
# It will load configuration from app.config (which loads from .env via config.py)
app = create_app()

if __name__ == '__main__':
    # This block runs only when you execute `python run.py` directly.
    # It's for the Flask development server.
    # Gunicorn will directly use the 'app' callable created by create_app().
    # The host and port here are for the dev server and might be overridden
    # by FLASK_RUN_HOST and FLASK_RUN_PORT environment variables if set.
    app.run(
        host=os.getenv('FLASK_RUN_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_RUN_PORT', '5000')),
        debug=(os.getenv('FLASK_DEBUG', '1') == '1')
    )