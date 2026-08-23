from fastapi import APIRouter , Depends, HTTPException , status 
from fastapi import Form , Query , Path , Response , Request
from fastapi.security import OAuth2PasswordRequestForm

from database.database import get_db
from database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

from redis_client import redis
from services import auth , utils , email as my_email