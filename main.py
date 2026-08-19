from fastapi import FastAPI
from routers import users
app=FastAPI(debug=True,version="1")

app.include_router(users.router)