from fastapi import APIRouter , Depends, HTTPException , status 
from fastapi import Form , Query , Path , Response , Request
from fastapi.security import OAuth2PasswordRequestForm

from database.database import get_db
from database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

from redis_client import redis
from services import auth , utils , email as my_email

router=APIRouter(prefix="/user",tags=["User"])

@router.post("/register")
async def user__register(
    full_name:str=Form(...),
    email:str=Form(...),
    password:str=Form(...,min_length=8),
    phone_number:str=Form(...,min_length=10,max_length=12),
    db:AsyncSession=Depends(get_db)
):
    try:
        user=User(full_name=full_name,email=email,phone_number=phone_number,password=utils.pass_hasher.hash(password))
        db.add(user)
        await db.commit()
        await db.refresh(user)

        email_token=utils.generate_email_token()
        # my_email.send_email(user.email,email_token)
        redis.set(f"email_token_verify:{email_token}",str(user.id),ex=60*10)

        return {
            "message":"Email was send to your email please verify it ",
            "token":email_token
        }
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail="Database is Down Try again later.")


@router.post('/auth/verify')
async def user__email_verify(token:str=Query(...),db:AsyncSession=Depends(get_db)):
    redis__user_id=redis.get(f"email_token_verify:{token}")
    if redis__user_id is None:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail="Invalid or expired link")
    try:
        redis__user_id=int(redis__user_id)
        user= await db.get(User,redis__user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not Found")
        if user.is_blocked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Your account have been blocked.")
        user.is_verified=True
        await db.commit()
        redis.delete(f"email_token_verify:{token}")
        return {
            "message":f"{user.full_name} your email have been verified Now you can use our services."
        }
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail="Database is not available. Try Again Later")

@router.post("/login")
async def user__login(res:Response,form_data:OAuth2PasswordRequestForm=Depends(),db:AsyncSession=Depends(get_db)):
    user= await db.scalar(select(User).where(User.full_name==form_data.username))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found.")
    if not utils.pass_hasher.verify(form_data.password , user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Wrong credentials Try again later.")
    if user.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Your account have been blocked")
    if not user.is_verified:
        return "token"
    access_token=auth.make_jwt_access_token(user.id,"user")
    refresh_token=auth.make_jwt_refresh_token(user.id,"user")
    print(refresh_token["id"])
    redis.set(f"refresh_token:{refresh_token["id"]}",user.id,ex=60*60*24*10)
    res.set_cookie(key="refresh_token",value=refresh_token,samesite="strict",path="/user/auth",httponly=True,max_age=60*30*24*10)
    return{
        "token_type":"bearer",
        "access_token":access_token
    }

@router.post("/auth/refresh")
async def user__refresh_token(user_id:str=Depends(auth.get_refresh_token)):
    access_token=auth.make_jwt_access_token(user_id,"user")
    return {
        "token_type":"bearer",
        "access_token":access_token
    }
@router.post("/logout")
async def user__logout(res:Response,req:Request,payload:dict=Depends()):
    redis_id=redis.get(f"blocked_token_id:{payload.get("token_id")}")
    cookie_token=req.cookies.get("refresh_token")

    if not redis_id and not cookie_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="you are logout already.")
    res.delete_cookie("refresh_token")
    redis.set(f"blocked_token_id:{payload.get("token_id")}",'1',ex=60*60*8)

    return{
        "message":"You have been logout."
    }
   