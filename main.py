from fastapi import FastAPI
from routers import users , rooms
app=FastAPI(debug=True,version="1")
import logger

app.include_router(users.router)
app.include_router(rooms.router)