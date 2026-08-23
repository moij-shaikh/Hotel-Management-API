from pydantic import BaseModel

class DisplayRoom(BaseModel):
    id:int
    room_type:str
    price:int
    available:bool