from jose import jwt , JWTError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends , HTTPException , status , Request , Response
from datetime import datetime , timedelta , timezone
from  uuid import uuid4
from config import JWT_ALGO , JWT_SECRET_KEY
from redis_client import redis




def generate_admin_access_token(sub):
    token_id=str(uuid4())
    payload={
        "sub":str(sub),
        "exp":datetime.now(timezone.utc)+ timedelta(minutes=10),
        "role":"admin",
        "token_id":token_id
    }
    access_token=jwt.encode(payload,JWT_SECRET_KEY,algorithm=JWT_ALGO)
    return access_token

def generate_admin_refresh_token(sub):
    payload={
        "sub":str(sub),
        "exp":datetime.now(timezone.utc)+ timedelta(days=20),
        "role":"admin"
    }
    refresh_token=jwt.encode(payload,JWT_SECRET_KEY,algorithm=JWT_ALGO)
    return refresh_token

get_jwt_token=OAuth2PasswordBearer(tokenUrl="/admin/login")

async def check_admin_access_token(token:str=Depends(get_jwt_token)):
    try:
        payload=jwt.decode(token,JWT_SECRET_KEY,algorithms=[JWT_ALGO])
        role=payload.get("role")
        if role != "admin":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="You are unauthorized for this operation.")
        redis_block_token=redis.get(f"admin_token_block:{payload.get("token_id")}")
        sub=payload.get("sub")
        if redis_block_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Login First.")
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Wrong Credential try login first.")

async def admin_check_refresh_token(req:Request,res:Response):
    refresh_token=req.cookies.get("admin_refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Login First.")
    redis_token=redis.get(f"admin_refresh_token:{refresh_token}")
    if not redis_token or redis_token is None:
        res.delete_cookie("admin_refresh_token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Login First.")
    try:
        payload=jwt.decode(refresh_token,JWT_SECRET_KEY,algorithms=[JWT_ALGO])
        role=payload.get("role")
        if role != "admin":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="You are unauthorized for this operation.")
        access_token=generate_admin_access_token(payload.get("sub"))
        return access_token
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Wrong Credential try login first.")





