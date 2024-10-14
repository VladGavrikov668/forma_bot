from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from app.config import SQL_ALCHEMY_DATABASE_URL
from .models import User

Base = declarative_base()

engine = create_async_engine(SQL_ALCHEMY_DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


# проверка прав администратора
async def check_admin(user_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()  # получаем пользователя или None, если не найден

        if user and user.is_admin:  # если пользователь найден и является администратором
            return True
        return False  # если не найден или не администратор
