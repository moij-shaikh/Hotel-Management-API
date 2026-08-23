from sqlalchemy.orm import DeclarativeBase , Mapped , mapped_column
from sqlalchemy import ForeignKey , DateTime
from datetime import datetime
from enum import Enum

# # class RoomType(str,Enum):
# class BookingStatus(str,Enum):
#     RESERVED="reserved"
#     CHECKED_IN="check_in"
#     CHECKED_OUT="check_out"
#     CANCELLED="cancelled"
    

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(primary_key=True)
    full_name:Mapped[str]=mapped_column(nullable=False)
    password:Mapped[str]
    email:Mapped[str]
    phone_number:Mapped[str]
    is_blocked:Mapped[bool]=mapped_column(default=False)
    is_verified:Mapped[bool]=mapped_column(default=False)

class Room(Base):
    __tablename__="rooms"
    id:Mapped[int]=mapped_column(primary_key=True)
    room_type:Mapped[str]
    price:Mapped[int]
    is_under_maintenance :Mapped[bool]=mapped_column(default=False)
    is_cleaned:Mapped[bool]=mapped_column(default=False)
    is_available:Mapped[bool]=mapped_column(default=False)


class RoomBooking(Base):
    __tablename__="room_bookings"
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"))
    room_id:Mapped[int]=mapped_column(ForeignKey("rooms.id",ondelete="CASCADE"))
    booked_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    checkout_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    is_checkout:Mapped[bool]=mapped_column(default=False)
    is_extended:Mapped[bool]=mapped_column(default=False)
    total_price:Mapped[int]
    payment:Mapped[bool]=mapped_column(default=False)
    