from passlib.context import CryptContext
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import request
from functools import wraps
import jwt
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
load_dotenv()

def create_user(user_obj):
    username = user_obj['username']
    hashed_password = pwd_context.hash(user_obj['password'])
    return [username, hashed_password]

def validate_credentials(userreqpass,user_def):
    return pwd_context.verify(userreqpass,user_def)
    #     token = create_access_token(user_req['username'])
    #     return token
    # else:
    #     return 'Invalid Credentials VC', False
    
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
            
            # except jwt.InvalidTokenError:
            #     return "Invalid Token"
            except jwt.InvalidTokenError as e: # Capture the exception instance as 'e'
        # Return the specific error message from PyJWT
                return {'error': f"Invalid Token: {str(e)}"}
            except Exception as e:
        # Catch any other unexpected errors during decoding
                return {'error': f"An unexpected error occurred: {str(e)}"}
        else:
            return {'message': 'Token is missing!'}, 401

        return f(current_userid, *args, **kwargs)
    return decorated



# def validate_token(token_string): # Make sure you're passing the actual token string
#     try:
#         # Ensure 'token_string' is just the token, not "Bearer <token>"
#         plain_token = jwt.decode(token_string, os.getenv("JWT_KEY"), algorithms=["HS256"])
#         user_id = plain_token['sub']
#         return user_id # Or perhaps {'success': True, 'user_id': user_id}
#     except jwt.ExpiredSignatureError:
#         # For debugging, you could return a more specific error object or dict
#         return {'error': "Token has Expired"}
#     except jwt.InvalidTokenError as e: # Capture the exception instance as 'e'
#         # Return the specific error message from PyJWT
#         return {'error': f"Invalid Token: {str(e)}"}
#     except Exception as e:
#         # Catch any other unexpected errors during decoding
#         return {'error': f"An unexpected error occurred: {str(e)}"}