from sqlalchemy import (Boolean, Column, ForeignKey,
                        Integer, String, DateTime, Enum)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .database import Base


class RoleName(enum.Enum):
    USER = 'Пользователь'
    APPROVER = 'Согласующий'
    BLOCK_MANAGER = 'Руководитель блока'
    ADMIN = 'Администратор'


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)  # Индекс для telegram_id
    role_id = Column(Integer, ForeignKey('role.id'))
    username = Column(String, nullable=True)
    block_manager = Column(Boolean, nullable=False, default=False)
    is_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())  # Время создания записи
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  # Время обновления записи

    blocks = relationship("Block", order_by="Block.id", back_populates="creator")


class Role(Base):
    __tablename__ = 'role'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(Enum(RoleName), unique=True, nullable=False)


class Block(Base):
    __tablename__ = 'blocks'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    creator_id = Column(Integer, ForeignKey('users.id'))
    creator = relationship("User", back_populates="blocks")
    created_at = Column(DateTime, server_default=func.now())  # Время создания записи
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  # Время обновления записи


class Token(Base):
    __tablename__ = 'tokens'

    id = Column(Integer, primary_key=True)
    value = Column(String, unique=True)
