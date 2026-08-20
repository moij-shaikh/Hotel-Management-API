import secrets
from jose import jwt, JWTError
from datetime import datetime , timedelta , timezone
from config import JWT_ALGO , JWT_SECRET_KEY


def make_jwt_access_token(user_id:int,role:str)->str:
    payload={
        "sub":str(user_id),
        "exp":datetime.now(timezone.utc) + timedelta(minutes=10),
        "token_id":str(secrets.token_urlsafe(16)),
        "role":role
    }
    token=jwt.encode(payload,JWT_SECRET_KEY,algorithm=JWT_ALGO)
    return token
def make_jwt_refresh_token(user_id:int,role:str)->str:
    token_id=str(secrets.token_urlsafe(16))
    payload={
        "sub":str(user_id),
        "exp":datetime.now(timezone.utc) + timedelta(days=10),
        "token_id":token_id,
        "role":role
    }
    token=jwt.encode(payload,JWT_SECRET_KEY,algorithm=JWT_ALGO)
    return {"token":token,"id":token_id}
