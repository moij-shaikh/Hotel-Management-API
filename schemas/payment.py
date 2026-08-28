from pydantic import BaseModel , Field
from . enums import  BookingStatus , RoomStatus ,PaymentStatus , RoomType


class UpdatePayment(BaseModel):
    amount:int | None = Field(default=None,gt=0)

class Payment_History(BaseModel):
    user_id:int
    room_id:int
    booking_id:int
    room_type:RoomType
    booking_status:BookingStatus
    room_status:RoomStatus
    payment_status:PaymentStatus
    total_amount:int
    extended_room_amount:int
    grand_total:int
    amount_paid:int

