from enum import Enum

class BookingStatus(str,Enum):
    RESERVED="reserved"
    CHECKED_IN="check_in"
    CHECKED_OUT="check_out"
    CANCELLED="cancelled"

class RoomStatus(str,Enum):
    AVAILABLE="AVAILABLE"
    OCCUPIED="OCCUPIED"
    CLEANING="CLEANING"
    MAINTENANCE="MAINTENANCE"
    
class PaymentStatus(str,Enum):
    PAID="paid"
    UNPAID="unpaid"
    PARTIAL="partial"
    
class RoomType(str,Enum):
    SINGLE="single"
    DOUBLE="double"
    SUITE="suite"