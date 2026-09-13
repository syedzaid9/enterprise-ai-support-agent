"""
SQLAlchemy database models for ResolveAI.
Defines foundational schema for multi-portal customer support, authentication,
multi-tenancy, subscriptions, payments, tickets, human-in-the-loop approvals,
agent runs, and audit logs.
"""

import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, SUSPENDED
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    # Relationships
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="company", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="company", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="company", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="company", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="company", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="company", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="company", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="company", cascade="all, delete-orphan")
    knowledge_documents = relationship("KnowledgeDocument", back_populates="company", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="customer")  # "customer" | "admin"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    # Relationships
    company = relationship("Company", back_populates="users")
    customer_profile = relationship("Customer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    external_customer_id = Column(String(100), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE, SUSPENDED
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    # Relationships
    user = relationship("User", back_populates="customer_profile")
    company = relationship("Company", back_populates="customers")
    subscriptions = relationship("Subscription", back_populates="customer", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="customer", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="customer", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="customer", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="customer")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    provider = Column(String(50), default="cashfree", nullable=False)
    external_subscription_id = Column(String(100), nullable=True, index=True)
    plan = Column(String(100), nullable=False, default="Pro Monthly")
    amount = Column(Float, default=499.0, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(50), default="INITIALIZED", nullable=False)  # INITIALIZED, ACTIVE, CANCELLED, PAST_DUE
    started_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    next_billing_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    # Relationships
    company = relationship("Company", back_populates="subscriptions")
    customer = relationship("Customer", back_populates="subscriptions")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    provider = Column(String(50), default="cashfree", nullable=False)
    external_payment_id = Column(String(100), nullable=True, index=True)
    order_id = Column(String(100), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(50), default="INITIALIZED", nullable=False)  # INITIALIZED, PENDING, SUCCESS, FAILED, REFUNDED
    payment_method = Column(String(100), default="UPI / Cards (Cashfree Sandbox)", nullable=True)
    provider_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    # Relationships
    company = relationship("Company", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    title = Column(String(255), default="Customer Support Inquiry", nullable=False)
    status = Column(String(50), default="active", nullable=False)  # active, resolved, closed
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    # Relationships
    company = relationship("Company", back_populates="conversations")
    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="conversation")
    approvals = relationship("Approval", back_populates="conversation")
    agent_runs = relationship("AgentRun", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender_type = Column(String(50), nullable=False)  # "customer", "assistant", "tool", "system"
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utc_now)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), unique=True, index=True, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(50), default="normal", nullable=False)  # low, normal, high, urgent
    status = Column(String(50), default="open", nullable=False)  # open, in_progress, waiting_for_customer, resolved, closed
    assigned_to = Column(String(255), nullable=True)
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    # Relationships
    company = relationship("Company", back_populates="tickets")
    customer = relationship("Customer", back_populates="tickets")
    conversation = relationship("Conversation", back_populates="tickets")


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    agent_run_id = Column(Integer, ForeignKey("agent_runs.id"), nullable=True)
    action_type = Column(String(100), nullable=False)  # "refund_payment", "cancel_subscription", "account_change"
    target_id = Column(String(100), nullable=True)  # payment_id or subscription_id
    action_data = Column(Text, nullable=False)  # JSON formatted parameter payload
    reason = Column(Text, nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, approved, rejected, completed, failed
    requested_by = Column(String(100), default="ai_agent", nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utc_now)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    company = relationship("Company", back_populates="approvals")
    customer = relationship("Customer", back_populates="approvals")
    conversation = relationship("Conversation", back_populates="approvals")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    workflow_name = Column(String(100), default="resolve_support_flow", nullable=False)
    intent = Column(String(100), nullable=True)
    status = Column(String(50), default="completed", nullable=False)  # running, completed, interrupted, failed
    error = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    started_at = Column(DateTime, default=_utc_now)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    company = relationship("Company", back_populates="agent_runs")
    conversation = relationship("Conversation", back_populates="agent_runs")
    customer = relationship("Customer", back_populates="agent_runs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    actor_type = Column(String(50), default="user", nullable=False)  # "user", "admin", "ai_agent", "system"
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=True)  # "payment", "subscription", "ticket", "approval", "auth", "knowledge"
    target_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    status = Column(String(50), default="SUCCESS", nullable=False)  # "SUCCESS", "DENIED", "FAILED"
    created_at = Column(DateTime, default=_utc_now)

    # Relationships
    company = relationship("Company", back_populates="audit_logs")
    customer = relationship("Customer", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    doc_type = Column(String(50), default="policy", nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="active", nullable=False)  # active, indexing, archived
    chunk_count = Column(Integer, default=0, nullable=False)
    vector_index_ref = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    # Relationships
    company = relationship("Company", back_populates="knowledge_documents")
