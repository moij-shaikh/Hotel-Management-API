from jose import jwt, JWTError
from datetime import datetime , timedelta , timezone
from config import JWT_ALGO , JWT_SECRET_KEY

def make_jwt_token(user_id:int)->str:
    payload={
        "sub":str(user_id),
        "exp":datetime.now(timezone.utc) + timedelta(minutes=10)
    }
    token=jwt.encode(payload,JWT_SECRET_KEY,algorithm=JWT_ALGO)
    return token

