from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from .database import Base

class API(Base):
    __tablename__ = "apis"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    token = Column(String, nullable=True)

class SourceSite(Base):
    __tablename__ = "source_sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    filters = Column(String, nullable=True)  # Optional comma-separated filters
    is_active = Column(Boolean, default=True)

class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    language = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    channel_url = Column(String, nullable=True)  # ✅ New field

class PostingHistory(Base):
    __tablename__ = "posting_history"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    article_url = Column(String, nullable=True)  # Add this line for the URL
    article_title = Column(String, nullable=True)  # Store article title
    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    channel_name = Column(String, nullable=True)  # Store channel name
    posted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    #content_sent = Column(String, nullable=True)
    # New Columns to store article title and channel name
   

from sqlalchemy.dialects.postgresql import UUID, BIGINT
from sqlalchemy.sql import func

class TelegramCookie(Base):
    __tablename__ = "telegram_cookies"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String, nullable=False)
    value = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    path = Column(String, nullable=False)
    expiry = Column(BIGINT, nullable=True)
    secure = Column(Boolean, default=False)
    http_only = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class CategoryKeywords(Base):
    __tablename__ = "category_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    keywords = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())  # Add this - it exists in your DB

class CategoryArticleCount(Base):
    __tablename__ = "category_article_count"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    article_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    quota_percentage = Column(Integer, default=0, nullable=False)  # This stays here - correct!