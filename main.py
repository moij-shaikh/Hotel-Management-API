from fastapi import FastAPI
from routers import users , rooms , admin
import logger
from contextlib import asynccontextmanager
from arq import create_pool
from arq.connections import RedisSettings

@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.arq = await create_pool(RedisSettings(host="localhost",port=6379))
    yield
    await app.state.arq.close()

app=FastAPI(debug=True,version="1",lifespan=lifespan)

app.include_router(users.router)
app.include_router(rooms.router)
app.include_router(admin.router)