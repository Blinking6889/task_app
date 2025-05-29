# app/__init__.py
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config import Config 
import os

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False))

def create_app(config_class=Config):
    """
    Application factory function.
    """
    app = Flask(__name__)
    app.config.from_object(config_class) 

    if not app.config.get('DATABASE_URL'):
        raise RuntimeError("DATABASE_URL not set in configuration!")
        
    engine = create_engine(app.config['DATABASE_URL'])
    db_session.configure(bind=engine) 

    from . import models 
    models.Base.metadata.create_all(bind=engine) 

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    from .auth import auth_bp as auth_blueprint
    app.register_blueprint(auth_blueprint)
 
    from .tasks import tasks_bp as tasks_blueprint # Import the tasks blueprint
    app.register_blueprint(tasks_blueprint)        # Register it

    @app.route('/hello_factory')
    def hello_factory():
        return "Hello from the app factory!"

    return app