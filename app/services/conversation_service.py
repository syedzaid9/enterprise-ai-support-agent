"""
Conversation and message persistence service for ResolveAI.
Ensures every customer inquiry, AI response, and tool invocation is recorded in PostgreSQL.
"""

from typing import Optional, Dict, Any, List
from app.db.database import get_db
from app.db.models import Conversation, Message, Customer


def get_or_create_conversation(
    company_id: int,
    customer_id: int,
    title: str = "Customer Support Inquiry",
) -> Conversation:
    """
    Get active conversation or create a new one for a customer.
    """
    with get_db() as db:
        conv = (
            db.query(Conversation)
            .filter(
                Conversation.company_id == company_id,
                Conversation.customer_id == customer_id,
                Conversation.status == "active",
            )
            .order_by(Conversation.created_at.desc())
            .first()
        )
        if not conv:
            conv = Conversation(
                company_id=company_id,
                customer_id=customer_id,
                title=title,
                status="active",
            )
            db.add(conv)
            db.flush()
            db.refresh(conv)
        return conv


def add_message(
    conversation_id: int,
    sender_type: str,  # "customer", "assistant", "tool", "system"
    content: str,
    metadata_json: Optional[str] = None,
) -> Message:
    """
    Persist a single message to a conversation.
    """
    with get_db() as db:
        msg = Message(
            conversation_id=conversation_id,
            sender_type=sender_type.lower(),
            content=content,
            metadata_json=metadata_json,
        )
        db.add(msg)
        db.flush()
        db.refresh(msg)
        return msg


def get_conversation_history(conversation_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve all messages for a conversation.
    """
    with get_db() as db:
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )
        return [
            {
                "id": m.id,
                "sender_type": m.sender_type,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ]
