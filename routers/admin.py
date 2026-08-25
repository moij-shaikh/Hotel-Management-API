from fastapi import APIRouter , Depends, HTTPException , status 
from fastapi import Form , Query , Path , Response , Request

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
from schemas.rooms import DisplayRoom , UpdateRoom ,UpdatePayment
from redis_client import redis
from services import auth , utils , email as my_email

router=APIRouter(prefix="/admin",tags=["Admin"])

@router.get("/room",response_model=list[DisplayRoom])
async def admin__show_rooms(db:AsyncSession=Depends(get_db)):
    rooms=await db.scalars(select(Room))
    room_list=rooms.all()
    display_list=[{"id":i.id,"room_type":i.room_type.value,"price":i.price,"status":i.room_status.value} for i in room_list]
    return display_list
@router.get("/room/{id}",response_model=DisplayRoom)
async def admin__show_room_Byid(id:int,db:AsyncSession=Depends(get_db)):
    room= await db.get(Room,id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Room not Found")
    display_room={
        "id":room.id,
        "room_type":room.room_type.value,
        "price":room.price,
        "status":room.room_status.value
        }
    
    return display_room

@router.post("/room")
async def admin__create_new_room(
    db:AsyncSession=Depends(get_db),
    room_type:RoomType=Form(...),
    price:int=Form(...,gt=0),
    room_status:RoomStatus=Form(...)
):
    new_room=Room(room_type=room_type,price=price,room_status=room_status)
    try:
        db.add(new_room)
        await db.commit()
        await db.refresh(new_room)
        return{
            "message":"new room added",
            "room id":new_room.id,
            "price":new_room.price,
            "type":new_room.room_type
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is down.")


@router.patch("/room/{id}")
async def admin__update_room(
    id:int,
    update_data:UpdateRoom,
    db:AsyncSession=Depends(get_db)
):
    room=await db.get(Room,id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Room not Found")
    if update_data.price is not None:
        room.price=update_data.price
    if update_data.room_type is not None:
        room.room_type=update_data.room_type
    try:
        await db.commit()
        return{
            "message":"Values are Updated"
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is down.")

@router.patch("/room/{id}/status")
async def admin__update_room_status(
    id:int,
    db:AsyncSession=Depends(get_db),
    room_status:RoomStatus=Form(...)
):
    room=await db.get(Room,id)
    if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Room not Found")
    if room.room_status ==  RoomStatus.OCCUPIED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Guest is present")
    try:
        room.room_status = room_status
        await db.commit()
        return{
            "message":"Values are Updated"
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is down.")

@router.get("/payment")
async def admin__get_payment_history(db:AsyncSession=Depends(get_db)):
    db_data = await db.scalars(select(RoomBooking).options(selectinload(RoomBooking.payment),selectinload(RoomBooking.room)))
    db_data_list=db_data.all()
    if not db_data_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Data Available .")
    display_list=[
        {
            "user_id":i.user_id,
            "room_id":i.room_id,
            "booking_id":i.id,
            "room_type":i.room.room_type.value,
            "booking_status":i.booking_status.value,
            "room_status":i.room.room_status.value,
            "payment_status":i.payment.payment_status.value,
            "total_amount":i.payment.total_amount,
            "extended_room_amount":i.payment.extended_room_amount,
            "grand_total":i.payment.grand_total,
            "amount_paid":i.payment.amount_paid
        } 
        for i in db_data_list
    ]
    return display_list

@router.get("/payment/{id}")
async def admin__get_payment_history_id(id:int,db:AsyncSession=Depends(get_db)):
    db_history= await db.scalar(select(RoomBooking).where(RoomBooking.id == id).options(selectinload(RoomBooking.payment),selectinload(RoomBooking.room)))
    if not db_history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Data Available .")
    display={
                "user_id":db_history.user_id,
                "room_id":db_history.room_id,
                "booking_id":db_history.id,
                "room_type":db_history.room.room_type.value,
                "booking_status":db_history.booking_status.value,
                "room_status":db_history.room.room_status.value,
                "payment_status":db_history.payment.payment_status.value,
                "total_amount":db_history.payment.total_amount,
                "extended_room_amount":db_history.payment.extended_room_amount,
                "grand_total":db_history.payment.grand_total,
                "amount_paid":db_history.payment.amount_paid
            }
    return display

@router.post("/payment/{id}/pay")
async def admin__handle_payment(id:int,update_data:UpdatePayment,db:AsyncSession=Depends(get_db)):
    db_booking= await db.scalar(select(RoomBooking).where(RoomBooking.id==id).with_for_update()
                                .options(
                                    selectinload(RoomBooking.room),
                                    selectinload(RoomBooking.payment),
                                    selectinload(RoomBooking.extended)
                                    )
                                    
                                    )
    if not db_booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Data Available .")
    if db_booking.booking_status == BookingStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Booking was already cancelled")
    if db_booking.payment.payment_status == PaymentStatus.PAID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Payment is already done.")


    try:
        if update_data.amount is not None:
            new_amount=db_booking.payment.amount_paid + update_data.amount
            if new_amount > db_booking.payment.grand_total:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Amount exceeds total amount")
        if new_amount == db_booking.payment.grand_total:
            db_booking.payment.payment_status=PaymentStatus.PAID
        if new_amount < db_booking.payment.grand_total:
            db_booking.payment.payment_status=PaymentStatus.PARTIAL
        db_booking.payment.amount_paid=new_amount
        await db.commit()
        details={
            "user_id":db_booking.user_id,
            "room_id":db_booking.room_id,
            "booking_id":db_booking.id,
            "payment_status":db_booking.payment.payment_status,
            "amount_paid":db_booking.payment.amount_paid,
            "total_amount":db_booking.payment.total_amount,
            "extensions":[
                {
                    "checkout_date":i.extended.checkout_date
                }
                for i in db_booking.extended
            ],
            "extended_amount":db_booking.payment.extended_room_amount,
            "grand_total":db_booking.payment.grand_total,

        }
        return details
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is down.")


@router.get("/bookings")
async def admin__get_bookings(db:AsyncSession=Depends(get_db)):
    db_bookings= await db.scalars(select(RoomBooking).options(selectinload(RoomBooking.payment)))
    display_list=[
        {
            "user_id":i.user_id,
            "room_id":i.room_id,
            "booking_id":i.id,
            "status":i.booking_status.value,
            "booked_at":i.created_at,
            "check_in_date":i.check_in_date,
            "check_out_date":i.check_out_date,
            "grand_total":i.payment.grand_total,
            "amount_paid":i.payment.amount_paid,

        }
        for i in db_bookings.all()
    ]