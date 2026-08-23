from fastapi import APIRouter , Depends, HTTPException , status 
from fastapi import Form , Query , Path , Response , Request

from database.database import get_db
from database.models import Room , RoomBooking
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

import json
from datetime import datetime , timedelta

from logger import admin_logger

from schemas.rooms import DisplayRoom
from redis_client import redis
from services import auth , utils , email as my_email

router=APIRouter(prefix="/rooms",tags=["Room"])


@router.get("/",response_model=list[DisplayRoom])
async def room__show_all(db:AsyncSession=Depends(get_db)):
    cached_room_list=redis.get("cached_rooms_all")
    if cached_room_list is not None:
        display_room_list=json.loads(cached_room_list)
        return display_room_list
    db_room_list= await db.scalars(select(Room))
    room_list=db_room_list.all()
    display_room_list=[{"id":i.id,"room_type":i.room_type,"price":i.price,"available":i.is_available}for i in room_list]
    redis.set("cached_rooms_all",json.dumps(display_room_list),ex=60*60)
    return display_room_list

@router.post("/book")
async def room__book(
    payload:dict=Depends(auth.get_token_payload),
    room_id:int=Query(...),
    db:AsyncSession=Depends(get_db),
    check_in_date:datetime=Form(...),
    days:int=Form(),
    ):
    user_id=payload.get("sub")
    try:
        room=await db.get(Room,room_id)
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Room not found")
        checkout_date=check_in_date + timedelta(days=days)
        total_price=room.price*days
        book=RoomBooking(user_id=user_id,room_id=room_id,booked_at=check_in_date,checkout_at=checkout_date,total_price=total_price)
        db.add(book)
        await db.commit()
        return {
            "message":"your room have been booked",
            "Total Amount":total_price,
            "Checkout date":checkout_date,
            "info":"Only After paying this Amount at Hotel Counter you will be given the room key. ",
            "warning":"If Failed to Check-in within in 1 hour of Selected Date we will cancel your Booking"
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Something Went Wrong with db.")