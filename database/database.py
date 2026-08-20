from config import DATABASE_URL

from sqlalchemy.ext.asyncio import create_async_engine , async_sessionmaker
engine=create_async_engine(DATABASE_URL)

session=async_sessionmaker(bind=engine,autoflush=False,expire_on_commit=False)

async def get_db():
    async with session() as db:
        yield db