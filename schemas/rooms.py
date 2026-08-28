from pydantic import BaseModel , Field
from . enums import  BookingStatus , RoomStatus ,PaymentStatus , RoomType
from datetime import datetime
class DisplayRoom(BaseModel):
    id:int
    room_type:RoomType
    price:int
    status:RoomStatus

        
class UpdateRoom(BaseModel):
    price:int | None=None
    room_type:RoomType|None = None


class DisplayRoomBooking(BaseModel):
    user_id:int
    room_id:int
    booking_id:int
    status:BookingStatus
    booked_at:datetime
    check_in_date:datetime
    check_out_date:datetime
    grand_total:int
    amount_paid:int