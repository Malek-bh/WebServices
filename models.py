from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, Text, DateTime, func, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.datetime("now"))

    # Relationships
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    services = relationship("ServiceProvider", back_populates="user", cascade="all, delete-orphan")
    requests = relationship("ServiceRequest", back_populates="user", cascade="all, delete-orphan")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    user = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    post_id = Column(Integer, ForeignKey("posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")


class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Relationships
    tasks = relationship("CropTask", back_populates="crop", cascade="all, delete-orphan")


class CropTask(Base):
    __tablename__ = "crop_tasks"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(String, nullable=False)
    task = Column(Text, nullable=False)
    crop_id = Column(Integer, ForeignKey("crops.id"))

    # Relationships
    crop = relationship("Crop", back_populates="tasks")


class ServiceProvider(Base):
    __tablename__ = "service_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    contact_info = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    user = relationship("User", back_populates="services")
    requests = relationship("ServiceRequest", back_populates="service_provider", cascade="all, delete-orphan")


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    service_provider_id = Column(Integer, ForeignKey("service_providers.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    service_provider = relationship("ServiceProvider", back_populates="requests")
    user = relationship("User", back_populates="requests")

class AgriculturalEvent(Base):
    __tablename__ = "agricultural_events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    date = Column(Date, nullable=False)
    season = Column(String, nullable=True)
    category = Column(String, nullable=True)
    tasks = Column(Text, nullable=True)