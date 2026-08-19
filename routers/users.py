from fastapi import APIRouter , Depends, HTTPException , status 
from fastapi import Form , Query , Path , Response , Request
from fastapi.security import OAuth2PasswordRequestForm

from database.database import get_db
from database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from redis_client import redis
from services import auth , utils , email as my_email

router=APIRouter(prefix="/user",tags=["User"])

@router.post("/register")
async def user__register(
    full_name:str=Form(...),
    email:str=Form(...),
    phone_number:str=Form(...,min_length=10,max_length=12),
    db:AsyncSession=Depends(get_db)
):
    try:
        user=User(full_name=full_name,email=email,phone_number=phone_number)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        email_token=utils.generate_email_token()
        my_email.send_email(user.email,email_token)
        redis.set(f"email_token_verify:{email_token}",str(user.id),ex=60*10)

        return {
            "message":"Email was send to your email please verify it "
        }
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail="Database is Down Try again later.")


@router('/auth/verify')
async def user__email_verify(token:str=Query(...),db:AsyncSession=Depends(get_db)):
    redis__user_id=redis.get(f"email_token_verify:{token}")
    if redis__user_id is None:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail="Invalid or expired link")
    try:
        user=await db.get(User,redis__user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not Found")
        if user.is_blocked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Your account have been blocked.")
        user.is_verified=True
        await db.commit()
        return {
            "message":f"{user.full_name} your email have been verified Now you can use our services."
        }
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail="Database is not available. Try Again Later")

@router.post("/login")
async def user__login(form_data:OAuth2PasswordRequestForm=Depends(),db:AsyncSession=Depends(get_db)):
    pass