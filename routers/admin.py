from fastapi import APIRouter , Depends, HTTPException , status 
from fastapi import Form  , Path , Response , Request
from fastapi.security import OAuth2PasswordRequestForm
from database.database import get_db
from database.models import Room , RoomBooking,User , Admin
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select 
from sqlalchemy.orm import selectinload

from datetime import datetime  ,timezone

from logger import admin_logger

from schemas.enums import BookingStatus , RoomStatus ,PaymentStatus , RoomType
from schemas.rooms import DisplayRoom , UpdateRoom ,UpdatePayment
from redis_client import redis
from services import admin_auth , utils , email as my_email

router=APIRouter(prefix="/admin",tags=["Admin"])

@router.post("/login")
async def admin__login(
    res:Response,
    form_data:OAuth2PasswordRequestForm=Depends(),
    db:AsyncSession=Depends(get_db)
):
    admin= await db.get(Admin,form_data.username)
    if not admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You can not access this.")
    if not utils.pass_hasher.verify(form_data.password,admin.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="You can not access this.")
    access_token=admin_auth.generate_admin_access_token(admin.username)
    refresh_token=admin_auth.generate_admin_refresh_token(admin.username)
    res.set_cookie(key="admin_refresh_token",value=refresh_token,samesite='strict',path="/admin",httponly=True, max_age=60*60*24*20)
    redis.set(f"admin_refresh_token:{refresh_token}",str(admin.username),ex=60*60*24*20)
    return {
        "token_type":"bearer",
        "access_token":access_token
    }
@router.post("/refresh")
async def admin__refresh_token(token:str=Depends(admin_auth.admin_check_refresh_token)):
    return{
        "token_type":"bearer",
        "access_token":token
    }
@router.post("/logout")
async def admin__logout(res:Response,req:Request,admin:dict=Depends(admin_auth.check_admin_access_token)):
    token_id=admin.get("token_id")
    redis.set(f"admin_token_block:{token_id}","1",ex=60*10)
    refresh_token=req.cookies.get("admin_refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Already Logout.")
    res.delete_cookie("admin_refresh_token")
    redis.delete(f"admin_refresh_token:{refresh_token}")

@router.get("/room",response_model=list[DisplayRoom])
async def admin__show_rooms(db:AsyncSession=Depends(get_db),admin:dict=Depends(admin_auth.check_admin_access_token)):
    rooms=await db.scalars(select(Room))
    room_list=rooms.all()
    display_list=[{"id":i.id,"room_type":i.room_type.value,"price":i.price,"status":i.room_status.value} for i in room_list]
    return display_list

@router.get("/room/{id}",response_model=DisplayRoom)
async def admin__show_room_Byid(id:int,db:AsyncSession=Depends(get_db),admin:dict=Depends(admin_auth.check_admin_access_token)):
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
    room_status:RoomStatus=Form(...),
    admin:dict=Depends(admin_auth.check_admin_access_token)
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
    db:AsyncSession=Depends(get_db),
    admin:dict=Depends(admin_auth.check_admin_access_token)
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
    room_status:RoomStatus=Form(...),
    admin:dict=Depends(admin_auth.check_admin_access_token)
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
async def admin__get_payment_history(db:AsyncSession=Depends(get_db),admin:dict=Depends(admin_auth.check_admin_access_token)):
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
async def admin__get_payment_history_id(id:int,db:AsyncSession=Depends(get_db),admin:dict=Depends(admin_auth.check_admin_access_token)):
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
async def admin__handle_payment(id:int,update_data:UpdatePayment,db:AsyncSession=Depends(get_db),admin:dict=Depends(admin_auth.check_admin_access_token)):
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
            "payment_status":db_booking.payment.payment_status.value,
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
async def admin__get_bookings(db:AsyncSession=Depends(get_db),admin:dict=Depends(admin_auth.check_admin_access_token)):
    db_bookings= await db.scalars(select(RoomBooking).options(selectinload(RoomBooking.payment)))
    data_list=db_bookings.all()
    if not data_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Data Available .")

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
        for i in data_list
    ]
    return display_list

@router.get("/bookings/{id}")
async def admin__get_booking_ById(id:int,db:AsyncSession=Depends(get_db),admin:dict=Depends(admin_auth.check_admin_access_token)):
    db_bookings= await db.scalar(select(RoomBooking).where(RoomBooking.id==id).options(selectinload(RoomBooking.payment)))
    if not db_bookings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Data Available .")
    display_list={
            "user_id":db_bookings.user_id,
            "room_id":db_bookings.room_id,
            "booking_id":db_bookings.id,
            "status":db_bookings.booking_status.value,
            "booked_at":db_bookings.created_at,
            "check_in_date":db_bookings.check_in_date,
            "check_out_date":db_bookings.check_out_date,
            "grand_total":db_bookings.payment.grand_total,
            "amount_paid":db_bookings.payment.amount_paid,
        }
        
    return display_list

@router.post("/check-in/{id}")
async def admin__check_in(id:int,db:AsyncSession=Depends(get_db),admin:dict=Depends(admin_auth.check_admin_access_token)):
    booking= await db.scalar(select(RoomBooking).where(RoomBooking.id==id).with_for_update().options(selectinload(RoomBooking.payment)))
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Booking Found .")
    if booking.booking_status==BookingStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Booking was cancelled.")
    if  booking.booking_status==BookingStatus.CHECKED_OUT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Guest was already checkout.")
    if  booking.booking_status==BookingStatus.CHECKED_IN:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Guest was already check-in.")
    if booking.payment.payment_status == PaymentStatus.UNPAID:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED,detail="Please First pay fees.")
    booking.booking_status=BookingStatus.CHECKED_IN
    try:
        await db.commit()
        display={
            "user_id":booking.user_id,
            "room_id":booking.room_id,
            "booking_id":booking.id,
            "status":booking.booking_status.value,
            "booked_at":booking.created_at,
            "check_in_date":booking.check_in_date,
            "check_out_date":booking.check_out_date,
            "grand_total":booking.payment.grand_total,
            "amount_paid":booking.payment.amount_paid,
        }
        return display
    except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is down.")
    

@router.post("/check-out/{id}")
async def admin__check_out(id:int,db:AsyncSession=Depends(get_db),admin:dict=Depends(admin_auth.check_admin_access_token)):
    booking= await db.scalar(select(RoomBooking).with_for_update().where(RoomBooking.id==id)
                             .options(selectinload(RoomBooking.payment),
                              selectinload(RoomBooking.room))
                              )
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Booking Found .")
    if booking.payment.payment_status==PaymentStatus.UNPAID or booking.payment.payment_status==PaymentStatus.PARTIAL:
        remaining= booking.payment.grand_total - booking.payment.amount_paid
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED,detail=f"Please pay the bill. Remaining: {remaining} Out of {booking.payment.grand_total}")
    if booking.check_out_date > datetime.now(timezone.utc):
        time_left=booking.check_out_date - datetime.now(timezone.utc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Time left before decided checkout date {time_left}")
    if booking.booking_status != BookingStatus.CHECKED_IN:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Guest Did not check-in")
    booking.booking_status=BookingStatus.CHECKED_OUT
    booking.room.room_status=RoomStatus.CLEANING
    try:
        await db.commit()
        return{
            "message":"Check-out was successful"
        }
    except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is down.")


@router.get("/user")
async def admin__get_users(db:AsyncSession=Depends(get_db),admin:dict=Depends(admin_auth.check_admin_access_token)):
    db_users= await db.scalars(select(User))
    db_list=db_users.all()
    if not db_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No data found.")
    display_list=[
        {
            "id":user.id,
            "full_name":user.full_name,
            "email":user.email,
            "phone_number":user.phone_number,
            "is_blocked":user.is_blocked,
            "is_verified":user.is_verified
        }
        for user in db_list
    ]
    return display_list


@router.get("/user/{id}")
async def admin__get_user_ById(id:int,db:AsyncSession=Depends(get_db),admin:dict=Depends(admin_auth.check_admin_access_token)):
    user= await db.get(User,id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No data found.")
    display={
            "id":user.id,
            "full_name":user.full_name,
            "email":user.email,
            "phone_number":user.phone_number,
            "is_blocked":user.is_blocked,
            "is_verified":user.is_verified
        }
        
    return display

@router.patch("/user/{id}/block")
async def admin__block_user(id:int=Path(gt=0),db:AsyncSession=Depends(get_db),admin:dict=Depends(admin_auth.check_admin_access_token)):
    user= await db.get(User,id)
    if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No data found.")
    if user.is_blocked:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="User is already Blocked")
    try:
        user.is_blocked=True
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is down.")


@router.patch("/user/{id}/unblock")
async def admin__unblock_user(id:int=Path(gt=0),db:AsyncSession=Depends(get_db),admin:dict=Depends(admin_auth.check_admin_access_token)):
    user= await db.get(User,id)
    if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No data found.")
    if not user.is_blocked:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="User is already Unblocked")
    try:
        user.is_blocked=False
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is down.")