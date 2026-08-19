import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL=os.getenv("DATABASE_URL")

JWT_ALGO=os.getenv("JWT_ALGO")
JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY")