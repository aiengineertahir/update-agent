import datetime
from sqlalchemy.orm import Session
from . import models


def get_tenant_by_api_key(db: Session, api_key: str):
    return db.query(models.Tenant).filter(models.Tenant.api_key == api_key).first()


def create_tenant(db: Session, name: str, slug: str):
    tenant = models.Tenant(name=name, slug=slug)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def upsert_channel_connection(db: Session, tenant_id: str, channel: str, connection_method: str,
                               external_account_id: str, access_token: str, extra=None):
    conn = db.query(models.ChannelConnection).filter(
        models.ChannelConnection.tenant_id == tenant_id,
        models.ChannelConnection.channel == channel,
        models.ChannelConnection.connection_method == connection_method,
    ).first()
    now = datetime.datetime.utcnow()
    if conn:
        conn.external_account_id = external_account_id
        conn.access_token = access_token
        conn.extra = extra
        conn.status = "connected"
        conn.connected_at = now
    else:
        conn = models.ChannelConnection(
            tenant_id=tenant_id, channel=channel, connection_method=connection_method,
            external_account_id=external_account_id, access_token=access_token,
            extra=extra, status="connected", connected_at=now,
        )
        db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


def get_channel_connections(db: Session, tenant_id: str):
    return db.query(models.ChannelConnection).filter(
        models.ChannelConnection.tenant_id == tenant_id
    ).all()


def disconnect_channel_connection(db: Session, tenant_id: str, connection_id: str):
    conn = db.query(models.ChannelConnection).filter(
        models.ChannelConnection.tenant_id == tenant_id,
        models.ChannelConnection.id == connection_id,
    ).first()
    if conn:
        conn.status = "disconnected"
        db.commit()
        db.refresh(conn)
    return conn


def disconnect_channel_by_name(db: Session, tenant_id: str, channel: str):
    conns = db.query(models.ChannelConnection).filter(
        models.ChannelConnection.tenant_id == tenant_id,
        models.ChannelConnection.channel == channel,
    ).all()
    for conn in conns:
        conn.status = "disconnected"
    db.commit()
    return conns


def create_user(db: Session, tenant_id: str, email: str, hashed_password: str):
    user = models.User(tenant_id=tenant_id, email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_active_knowledge(db: Session, tenant_id: str):
    return db.query(models.KnowledgeEntry).filter(
        models.KnowledgeEntry.tenant_id == tenant_id,
        models.KnowledgeEntry.is_active.is_(True),
    ).all()


def add_knowledge(db: Session, tenant_id: str, question: str, answer: str):
    entry = models.KnowledgeEntry(tenant_id=tenant_id, question=question, answer=answer)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def delete_knowledge(db: Session, tenant_id: str, entry_id: str):
    entry = db.query(models.KnowledgeEntry).filter(
        models.KnowledgeEntry.tenant_id == tenant_id,
        models.KnowledgeEntry.id == entry_id,
    ).first()
    if entry:
        entry.is_active = False
        db.commit()
        return True
    return False


def update_knowledge(db: Session, tenant_id: str, entry_id: str, question: str, answer: str):
    entry = db.query(models.KnowledgeEntry).filter(
        models.KnowledgeEntry.tenant_id == tenant_id,
        models.KnowledgeEntry.id == entry_id,
        models.KnowledgeEntry.is_active.is_(True),
    ).first()
    if entry:
        entry.question = question
        entry.answer = answer
        db.commit()
        db.refresh(entry)
        return entry
    return None


def delete_all_knowledge(db: Session, tenant_id: str) -> int:
    count = db.query(models.KnowledgeEntry).filter(
        models.KnowledgeEntry.tenant_id == tenant_id,
        models.KnowledgeEntry.is_active.is_(True),
    ).update({"is_active": False}, synchronize_session=False)
    db.commit()
    return count


def get_or_create_conversation(db: Session, tenant_id: str, channel: str, contact_external_id: str, contact_name: str = None):
    convo = db.query(models.Conversation).filter(
        models.Conversation.tenant_id == tenant_id,
        models.Conversation.channel == channel,
        models.Conversation.contact_external_id == contact_external_id,
    ).first()
    if convo:
        return convo
    convo = models.Conversation(
        tenant_id=tenant_id, channel=channel,
        contact_external_id=contact_external_id, contact_name=contact_name,
    )
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo


def save_message(db: Session, conversation_id: str, direction: str, body: str):
    now = datetime.datetime.utcnow()
    msg = models.Message(conversation_id=conversation_id, direction=direction, body=body, created_at=now)
    db.add(msg)
    convo = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if convo:
        convo.last_message_at = now
    db.commit()
    return msg


def create_booking(db: Session, tenant_id: str, channel: str, conversation_id: str, name, contact, preferred_time, notes):
    booking = models.Booking(
        tenant_id=tenant_id, channel=channel, conversation_id=conversation_id,
        name=name, contact=contact, preferred_time=preferred_time, notes=notes,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_tenant_system_prompt(db: Session, tenant_id: str) -> str:
    tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if tenant and tenant.custom_system_prompt:
        return tenant.custom_system_prompt
    return ""


def update_tenant_system_prompt(db: Session, tenant_id: str, prompt: str) -> str:
    tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if tenant:
        tenant.custom_system_prompt = prompt
        db.commit()
        db.refresh(tenant)
        return tenant.custom_system_prompt or ""
    return ""
