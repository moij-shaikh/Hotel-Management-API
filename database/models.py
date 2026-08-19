from sqlalchemy.orm import DeclarativeBase , Mapped , mapped_column
from sqlalchemy import ForeignKey 

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(primary_key=True)
    full_name:Mapped[str]=mapped_column(nullable=False)
    email:Mapped[str]
    phone_number:Mapped[str]
    is_blocked:Mapped[bool]=mapped_column(default=False)
    is_verified:Mapped[bool]=mapped_column(default=False)