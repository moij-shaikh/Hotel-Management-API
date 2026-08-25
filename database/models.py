from sqlalchemy.orm import DeclarativeBase , Mapped , mapped_column ,relationship
from sqlalchemy import ForeignKey , DateTime , Enum 
from datetime import datetime , timezone
from schemas.enums import BookingStatus , RoomStatus ,PaymentStatus , RoomType

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
    room_type:Mapped[RoomType]=mapped_column(Enum(RoomType))
    price:Mapped[int]
    room_status:Mapped[RoomStatus]=mapped_column(Enum(RoomStatus))
    booking:Mapped[list["RoomBooking"]]=relationship("RoomBooking",back_populates="room")


class RoomBooking(Base):
    __tablename__="room_bookings"
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"))
    room_id:Mapped[int]=mapped_column(ForeignKey("rooms.id",ondelete="CASCADE"))

    check_in_date:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    check_out_date:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    created_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc))

    booking_status:Mapped[BookingStatus]=mapped_column(Enum(BookingStatus))

    extended:Mapped[list["BookingExtension"]]=relationship("BookingExtension",back_populates="room_booked")
    payment:Mapped["Payment"]=relationship("Payment",back_populates="room_booked",uselist=False)
    room:Mapped["Room"]=relationship("Room",back_populates="booking")
    
class Payment(Base):
    __tablename__="payments"
    id:Mapped[int]=mapped_column(primary_key=True)
    room_book_id:Mapped[int]=mapped_column(ForeignKey("room_bookings.id",ondelete="CASCADE"))
    payment_status:Mapped[PaymentStatus]=mapped_column(Enum(PaymentStatus))
    total_amount:Mapped[int]
    extended_room_amount:Mapped[int]=mapped_column(default=0)
    grand_total:Mapped[int]
    amount_paid:Mapped[int]=mapped_column(default=0)
    room_booked:Mapped["RoomBooking"]=relationship("RoomBooking",back_populates="payment")

class BookingExtension(Base):
    __tablename__="extended_rooms"
    id:Mapped[int]=mapped_column(primary_key=True)
    room_book_id:Mapped[int]=mapped_column(ForeignKey("room_bookings.id",ondelete="CASCADE"))
    checkout_date:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    room_booked:Mapped["RoomBooking"]=relationship("RoomBooking",back_populates="extended")



