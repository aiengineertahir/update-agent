import uuid
import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship

from .database import Base


def gen_id():
    return str(uuid.uuid4())


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=gen_id)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    api_key = Column(String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    knowledge_entries = relationship("KnowledgeEntry", back_populates="tenant", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="tenant", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="tenant", cascade="all, delete-orphan")
    connections = relationship("ChannelConnection", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """A human login account. Belongs to exactly one tenant for now (no cross-tenant staff yet)."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")


class ChannelConnection(Base):
    __tablename__ = "channel_connections"

    id = Column(String(36), primary_key=True, default=gen_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    channel = Column(String(20), nullable=False)
    connection_method = Column(String(20), nullable=False, default="official_api")
    external_account_id = Column(String(255), nullable=True)
    access_token = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    extra = Column(JSON, nullable=True)
    connected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="connections")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=gen_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    channel = Column(String(20), nullable=False)
    contact_external_id = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=True)
    last_message_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation",
        cascade="all, delete-orphan", order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=gen_id)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    direction = Column(String(10), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_base"

    id = Column(String(36), primary_key=True, default=gen_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="knowledge_entries")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String(36), primary_key=True, default=gen_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    channel = Column(String(20), nullable=False)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=True)
    name = Column(String(255), nullable=True)
    contact = Column(String(255), nullable=True)
    preferred_time = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="bookings")
