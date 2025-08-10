from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, TIMESTAMP, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY  # PostgreSQL için

from database import Base


# Kullanıcılar
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=True)
    platform_user_id = Column(String(100), nullable=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # İlişkiler
    content_items = relationship(
        "ContentItem",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    settings = relationship(
        "Settings",
        back_populates="user",
        cascade="all, delete-orphan"
    )


# Kullanıcının içerikleri
class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    content_url = Column(Text, nullable=True)  # Örn: /analysis/<name>
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # İlişkiler
    user = relationship("User", back_populates="content_items")
    comments = relationship(
        "Comment",
        back_populates="content_item",
        cascade="all, delete-orphan"
    )


# Yorumlar
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)

    # İlişkiler
    content_item = relationship("ContentItem", back_populates="comments")
    analysis_results = relationship(
        "AnalysisResults",
        back_populates="comment",
        cascade="all, delete-orphan"
    )


# NLP analiz sonuçları
class AnalysisResults(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)

    labels_hukuk = Column("labels_hukuk", ARRAY(String), nullable=True)   # örn: ['a','s','d']
    labels_duygu = Column("labels_duygu", ARRAY(String), nullable=True)   # örn: ['1','2','3']
    labels_niyet = Column("labels_niyet", ARRAY(String), nullable=True)  # örn: ['6','7','q']

    temizlik = Column(String(1), nullable=True)           # 'p','j','k'
    law_score = Column(Float, nullable=True)              # 0.0 - 1.0
    has_dilekce = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # İlişkiler
    comment = relationship("Comment", back_populates="analysis_results")
    dilekce_logs = relationship(
        "DilekceLog",
        back_populates="analysis_result",
        cascade="all, delete-orphan"
    )


# Kullanıcı ayarları
class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mode = Column(String(20), nullable=False)        # 'duzenli' | 'duzensiz'
    frequency = Column(String(20), nullable=True)    # 'daily' | 'weekly' | 'monthly'
    platform = Column(String(50), nullable=False)
    notify_email = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # İlişkiler
    user = relationship("User", back_populates="settings")


# Üretilen dilekçeler
class DilekceLog(Base):
    __tablename__ = "dilekce_logs"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False)
    generated_text = Column(Text, nullable=False)
    pdf_url = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # İlişkiler
    analysis_result = relationship("AnalysisResults", back_populates="dilekce_logs")
