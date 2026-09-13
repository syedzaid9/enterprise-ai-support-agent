"""
AI Resolution Chat REST API endpoints for ResolveAI.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command

from app.api.auth import get_current_user
from app.graph.workflow import app_graph
from app.services.customer_service import get_customer_by_user_id
from app.services.conversation_service import get_or_create_conversation, add_message
from app.services.agent_run_service import start_agent_run, finish_agent_run

router = APIRouter(prefix="/chat", tags=["AI Support Chat"])


class ChatMessageRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    conversation_id: Optional[int] = None


class ResumeApprovalRequest(BaseModel):
    thread_id: str
    approved: bool
    feedback: Optional[str] = None


@router.post("")
def chat_with_agent(req: ChatMessageRequest, current_user=Depends(get_current_user)):
    """
    Send a message to the ResolveAI LangGraph support agent with authenticated context.
    """
    cust = get_customer_by_user_id(current_user.id, company_id=current_user.company_id)
    customer_id = cust["id"] if cust else 1
    company_id = current_user.company_id or 1

    # Get or create conversation record
    conv = get_or_create_conversation(company_id=company_id, customer_id=customer_id)
    conversation_id = conv.id

    # Persist user message to PostgreSQL
    add_message(conversation_id=conversation_id, sender_type="customer", content=req.message)

    # Start Agent Run log in PostgreSQL
    agent_run_id = start_agent_run(
        company_id=company_id,
        customer_id=customer_id,
        conversation_id=conversation_id,
        workflow_name="resolve_support_flow",
    )

    thread_id = req.thread_id or f"conv_{conversation_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = app_graph.invoke(
            {
                "messages": [HumanMessage(content=req.message)],
                "customer_id": customer_id,
                "company_id": company_id,
                "conversation_id": conversation_id,
                "agent_run_id": agent_run_id,
            },
            config=config,
        )

        state = app_graph.get_state(config)

        # Check for Sensitive Tool Interruption
        if state.tasks and state.tasks[0].interrupts:
            interrupt_val = state.tasks[0].interrupts[0].value
            finish_agent_run(agent_run_id=agent_run_id, status="interrupted")
            return {
                "status": "requires_approval",
                "message": "This resolution requires Human Supervisor Authorization before financial execution.",
                "pending_action": interrupt_val,
                "thread_id": thread_id,
                "conversation_id": conversation_id,
            }

        final_msg = result["messages"][-1]
        response_text = final_msg.content if isinstance(final_msg, AIMessage) else str(final_msg)

        # Persist Assistant Response in PostgreSQL
        add_message(conversation_id=conversation_id, sender_type="assistant", content=response_text)
        finish_agent_run(agent_run_id=agent_run_id, status="completed")

        return {
            "status": "completed",
            "response": response_text,
            "thread_id": thread_id,
            "conversation_id": conversation_id,
        }

    except Exception as e:
        finish_agent_run(agent_run_id=agent_run_id, status="failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Agent workflow error: {str(e)}")


@router.post("/resume")
def resume_approval(req: ResumeApprovalRequest, current_user=Depends(get_current_user)):
    """
    Resume an interrupted graph turn with supervisor approval/rejection.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required to approve sensitive operations.")

    config = {"configurable": {"thread_id": req.thread_id}}

    try:
        resumed = app_graph.invoke(
            Command(resume={"approved": req.approved, "feedback": req.feedback, "admin_user_id": current_user.id}),
            config=config,
        )
        final_msg = resumed["messages"][-1]
        response_text = final_msg.content if isinstance(final_msg, AIMessage) else str(final_msg)

        return {
            "status": "completed",
            "response": response_text,
            "thread_id": req.thread_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume graph workflow: {str(e)}")
