# app/auth/routes.py
from flask import Blueprint, request, jsonify
from sqlalchemy import Select

from app import db_session
from app.models import User
from .services import create_user, validate_credentials, create_access_token, validate_token

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')

@auth_bp.route("/register", methods=['POST'])
def register_user_route():
    user_req = request.get_json()
    if not user_req or not user_req.get('username') or not user_req.get('password'):
        return jsonify({'message': 'Username and password required'}), 400

    # Check for existing user
    user_query = Select(User).where(User.username == user_req['username'])
    existing_user = db_session.scalars(user_query).first() 

    if existing_user:
        return jsonify({'message': 'Username already exists.'}), 409

    try:
        user_details = create_user(user_req)
        new_db_user = User(username=user_details[0], hashed_password=user_details[1])
        db_session.add(new_db_user)
        db_session.commit()

        return jsonify({'message': 'User Created Successfully'}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'message': f'Error creating user: {str(e)}'}), 500


@auth_bp.route("/login", methods=['POST'])
def login_user_route():
    user_req = request.get_json()
    if not user_req or not user_req.get('username') or not user_req.get('password'):
        return jsonify({'message': 'Username and password required'}), 400

    user_query = Select(User).where(User.username == user_req['username'])
    user_from_db = db_session.scalars(user_query).first()

    if user_from_db and validate_credentials(user_req['password'], user_from_db.hashed_password):
        token_response = create_access_token(user_from_db.id)
        return jsonify(token_response), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401