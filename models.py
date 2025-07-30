from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, TIMESTAMP
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Şifreli kayıt için eklendi

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mode = Column(String(20), nullable=False)
    frequency = Column(String(20), nullable=True)
    platform = Column(String(50), nullable=False)
    notify_email = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
