import datetime
from pydantic import BaseModel
from typing import Optional, List


class TenantCreate(BaseModel):
    name: str
    slug: str


class TenantOut(BaseModel):
    id: str
    name: str
    slug: str
    api_key: str

    class Config:
        from_attributes = True


class TenantBasic(BaseModel):
    id: str
    name: str
    slug: str

    class Config:
        from_attributes = True


class SignupIn(BaseModel):
    business_name: str
    slug: str
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


class AuthOut(BaseModel):
    token: str
    tenant: TenantBasic
    email: str


class MeOut(BaseModel):
    tenant: TenantBasic
    email: str


class KnowledgeCreate(BaseModel):
    question: str
    answer: str


class KnowledgeOut(BaseModel):
    id: str
    question: str
    answer: str
    is_active: bool

    class Config:
        from_attributes = True


class TestMessageIn(BaseModel):
    channel: str
    contact_external_id: str
    contact_name: Optional[str] = None
    message: str


class BookingInfo(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    preferred_time: Optional[str] = None
    notes: Optional[str] = None


class TestMessageOut(BaseModel):
    reply: str
    booking_created: bool
    booking_info: Optional[BookingInfo] = None


class MessageOut(BaseModel):
    id: str
    direction: str
    body: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: str
    channel: str
    contact_external_id: str
    contact_name: Optional[str] = None
    last_message_at: datetime.datetime

    class Config:
        from_attributes = True


class WhatsAppOfficialConnectIn(BaseModel):
    phone_number_id: str
    access_token: str
    waba_id: Optional[str] = None


class ChannelConnectionOut(BaseModel):
    id: str
    channel: str
    connection_method: str
    external_account_id: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class WhatsAppQrStatusOut(BaseModel):
    status: str
    qr: Optional[str] = None


class WhatsAppQrStatusWebhookIn(BaseModel):
    tenant_id: str
    status: str


class WhatsAppQrMessageIn(BaseModel):
    tenant_id: str
    sender: str
    name: Optional[str] = None
    text: str


class FacebookConnectIn(BaseModel):
    page_id: str
    access_token: str


class InstagramConnectIn(BaseModel):
    ig_business_account_id: str
    access_token: str


class BookingOut(BaseModel):
    id: str
    channel: str
    conversation_id: Optional[str] = None
    name: Optional[str] = None
    contact: Optional[str] = None
    preferred_time: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True
