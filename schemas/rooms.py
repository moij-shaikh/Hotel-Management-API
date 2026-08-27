from pydantic import BaseModel , Field
from . enums import  BookingStatus , RoomStatus ,PaymentStatus , RoomType

class DisplayRoom(BaseModel):
    id:int
    room_type:RoomType
    price:int
    status:RoomStatus


class UpdateRoom(BaseModel):
    price:int | None=None
    room_type:RoomType|None = None

class UpdatePayment(BaseModel):
    amount:int | None = Field(default=None,gt=0)
