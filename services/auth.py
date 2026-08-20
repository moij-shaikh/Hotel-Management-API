import secrets
from jose import jwt, JWTError
from config import JWT_ALGO , JWT_SECRET_KEY
from fastapi import Cookie , HTTPException , status, Depends
from fastapi.security import OAuth2PasswordBearer
from redis_client import redis
from datetime import datetime , timedelta , timezone
from database.database import get_db
from database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyErrors
# from sqlalchemy import select

get_jwt_token=OAuth2PasswordBearer(tokenUrl="/user/login")


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

async def get_token_payload(token:str=Depends(get_jwt_token),db:AsyncSession=Depends(get_db))->dict:
    try:
        payload=jwt.decode(token,JWT_SECRET_KEY,algorithms=[JWT_ALGO])
        user_id=int(payload.get("sub"))
        user= await db.get(User,user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Not Found")
        if user.is_blocked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You have been blocked.")
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid or Wrong Credential Try again later.")
    
async def get_refresh_token(refresh_token:str=Cookie(),db:AsyncSession=Depends(get_db))->str:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Wrong or invalid credential. ")
    try:
        payload=jwt.decode(refresh_token,JWT_SECRET_KEY,algorithms=[JWT_ALGO])
        token_id=payload.get(f"refresh_token:{payload.get("token_id")}")
        if not token_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Expired or invalid credentials try again later.")
        user_id=int(payload.get("sub"))
        db_user= await db.get(User,user_id)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No User Founds")
        if db_user.is_blocked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You have been blocked.")
        return payload.get("sub")

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Expired or invalid credentials try again later.")


    