from . import crud, agent


def process_incoming_message(db, tenant, channel, contact_external_id, contact_name, message_text):
    """Runs one inbound message through the full pipeline: save it, ask the agent
    for a reply restricted to this tenant's knowledge base, save the reply, and
    capture a booking if the agent gathered enough info. Returns the reply text so
    the caller can decide how to deliver it (return it directly, or send it out
    over a real channel like whatsapp)."""
    convo = crud.get_or_create_conversation(db, tenant.id, channel, contact_external_id, contact_name)

    history = list(convo.messages[-10:]) if convo.messages else []

    crud.save_message(db, convo.id, "inbound", message_text)

    kb_entries = crud.get_active_knowledge(db, tenant.id)

    result = agent.generate_reply(tenant.name, kb_entries, history, message_text)

    crud.save_message(db, convo.id, "outbound", result["reply"])

    booking_created = False
    booking_info = result.get("booking_info")
    if result.get("booking_ready") and booking_info:
        crud.create_booking(
            db, tenant.id, channel, convo.id,
            booking_info.get("name"), booking_info.get("contact"),
            booking_info.get("preferred_time"), booking_info.get("notes"),
        )
        booking_created = True

    return {
        "conversation": convo,
        "reply": result["reply"],
        "booking_created": booking_created,
        "booking_info": booking_info if booking_created else None,
    }
