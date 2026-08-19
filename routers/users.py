from fastapi import APIRouter , Depends, HTTPException , status 
from fastapi import Form , Query , Path , Response , Request

from database.database import get_db
from database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from services import auth , utils

router=APIRouter(prefix="/User",tags=["User"])

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

        token=utils.generate_email_token()

        return token
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail="Database is Down Try again later.")