from passlib.context import CryptContext
from datetime import datetime, timedelta
from flask import request
from functools import wraps
import jwt
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(user_obj):
    username = user_obj['username']
    hashed_password = pwd_context.hash(user_obj['password'])
    return [username, hashed_password]

def validate_credentials(userreqpass,user_def):
    return pwd_context.verify(userreqpass,user_def)
    
def create_access_token(user_integer_id):
    payload = {
        'sub': str(user_integer_id),
        'iat': datetime.utcnow(), # iat (issued at)
        'exp': datetime.utcnow() + timedelta(minutes=30) # exp (expiration time)
    }
    token = jwt.encode(payload, os.getenv("JWT_KEY"), algorithm="HS256")
    return {'access_token': token}

def validate_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get('Authorization'):
            try:
                parsed_token = request.headers.get('Authorization').split()[1]
                plain_token = jwt.decode(parsed_token,os.getenv("JWT_KEY"), algorithms=["HS256"])
                current_userid = int(plain_token['sub'])

            except jwt.ExpiredSignatureError:        
                return "Token has Expired"
            
            except jwt.InvalidTokenError as e: 
                return {'error': f"Invalid Token: {str(e)}"}
            except Exception as e:

                return {'error': f"An unexpected error occurred: {str(e)}"}
        else:
            return {'message': 'Token is missing!'}, 401

        return f(current_userid, *args, **kwargs)
    return decorated
