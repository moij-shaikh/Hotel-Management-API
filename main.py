from fastapi import FastAPI
from routers import users , rooms , admin
import logger

app=FastAPI(debug=True,version="1")

app.include_router(users.router)
app.include_router(rooms.router)
app.include_router(admin.router)