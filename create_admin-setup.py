import asyncio
from services.utils import pass_hasher
from database.database import session
from database.models import Admin
from sqlalchemy import select

async def create_admin():
    username=input("Enter username:  ")
    password=input("Enter password:  ")
    email=input("Enter email:  ")
    async with session() as s:
        check= await s.scalar(select(Admin))
        if check:
            print("Admin already exists")
            return

        admin=Admin(username=username,password=pass_hasher.hash(password),email=email)
        s.add(admin)
        await s.commit()
        print("Admin Created ")


if __name__ == "__main__":
    asyncio.run(create_admin())
