from fastapi import APIRouter , Depends, HTTPException , status 
from fastapi import Form , Query 

from database.database import get_db
from database.models import Room , RoomBooking ,Payment,BookingExtension
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select 
from sqlalchemy.orm import selectinload

import json
from datetime import datetime , timedelta ,timezone

from logger import admin_logger

from schemas.enums import BookingStatus , RoomStatus ,PaymentStatus , RoomType
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
    user_id=int(payload.get("sub"))
    try:
        room=await db.scalar(select(Room).where(Room.id ==room_id).with_for_update())
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Room not found")
        if room.room_status==RoomStatus.MAINTENANCE:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail="Room is Under MAINTENANCE Right Now.try again later")
        checkout_date=check_in_date + timedelta(days=days)
        existing= await db.scalar(select(RoomBooking).where(RoomBooking.room_id==room_id,RoomBooking.booking_status==BookingStatus.RESERVED,RoomBooking.check_in_date < checkout_date,RoomBooking.check_out_date > check_in_date).order_by(RoomBooking.check_out_date.desc()))
        if existing:
         raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Rooms are booked Try after {existing.check_out_date}")
        
        total_price=room.price*days
        booking=RoomBooking(
            user_id=user_id,
            room_id=room_id,
            check_in_date=check_in_date,
            check_out_date=checkout_date,
            booking_status=BookingStatus.RESERVED
            )
        payment=Payment(total_amount=total_price,payment_status=PaymentStatus.UNPAID,grand_total=total_price)
        booking.payment=payment
        db.add(booking)
        await db.commit()
        redis.delete("cached_rooms_all")
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

@router.get("/bookings")
async def room__user_bookings(payload:dict=Depends(auth.get_token_payload),db:AsyncSession=Depends(get_db)):
    db_rooms_booking= await db.scalars(select(RoomBooking).where(RoomBooking.user_id==int(payload.get("sub"))).options(selectinload(RoomBooking.room)))
    rooms_booking_list=db_rooms_booking.all()
    if not rooms_booking_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Booking Found.")
    display_list=[{ "id":i.id,"room number":i.room_id,"room type":i.room.room_type,"Current room price/day":i.room.price,"total price":i.total_price,"check-in date":i.check_in_date,"checkout date":i.check_out_date} for i in rooms_booking_list]
    return display_list

@router.delete("/cancel")
async def room__booking_cancel(id:int=Query(...),payload:dict=Depends(auth.get_token_payload),db:AsyncSession=Depends(get_db)):
    try:
        user_id=int(payload.get("sub"))
        booking= await db.scalar(select(RoomBooking).where(RoomBooking.id == id , RoomBooking.user_id == user_id))
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Room Booing Found.")
        if booking.check_in_date > datetime.now(timezone.utc) + timedelta(days=1):
            booking.booking_status=BookingStatus.CANCELLED
        else:
            return{
                "message":"your booking can not be canceled"
            }
        await db.commit()

        return{
            "message":f"Booking: {id} is successfully Canceled.",
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Something Went Wrong with db.")
 

@router.patch("/extent")
async def room__extent(
    id:int,
    days:int,
    payload:dict=Depends(auth.get_token_payload),
    db:AsyncSession=Depends(get_db)
    ):
    user_id=int(payload.get("sub"))
    db_room_booking= await db.scalar(select(RoomBooking).where(RoomBooking.id==id,RoomBooking.user_id==user_id).options(selectinload(RoomBooking.room,RoomBooking.payment)))

    if db_room_booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Booking Found.")
    if db_room_booking.booking_status== BookingStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Your Booking Has been already canceled ")
    
    if db_room_booking.payment.payment_status== PaymentStatus.UNPAID:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED,detail="Please Pay your Booking Charges. ")
    
    if db_room_booking.booking_status== BookingStatus.CHECKED_OUT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are already Checkout from our hotel you need to book new Room.")
    await db.scalar(select(Room).where(Room.id == db_room_booking.room.id).with_for_update())
    new_check_out=db_room_booking.check_out_date + timedelta(days=days)
    existing=await db.scalar(select(RoomBooking).where(
        RoomBooking.room_id==db_room_booking.room.id,
        RoomBooking.booking_status==BookingStatus.RESERVED, 
        RoomBooking.id != db_room_booking.id,
        RoomBooking.check_out_date > new_check_out,

        RoomBooking.check_in_date <= new_check_out
        ).order_by(RoomBooking.check_in_date.desc())
        )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Rooms are booked Try after {existing.check_out_date}")

    try:
        total_price=db_room_booking.room.price*days
        extent=BookingExtension(room_book_id=db_room_booking.id,checkout_date=new_check_out)
        db_room_booking.payment.extended_room_amount = total_price
        db_room_booking.payment.grand_total += total_price
        db_room_booking.payment.payment_status=PaymentStatus.PARTIAL
        db_room_booking.extended.append(extent)
        await db.commit()
        return {
            "message":"Your Booking is Extended",
            "Checkout date":db_room_booking.check_out_date,
            "Extended Period price":total_price,
            "Total Price":db_room_booking.total_price
        }
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Something Went Wrong with db.")
