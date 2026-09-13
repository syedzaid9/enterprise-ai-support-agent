"""
LangGraph Resolution Workflow for ResolveAI.
Orchestrates agent reasoning, safe tool execution, human-in-the-loop approval pauses,
database approval synchronization, and conversation state management.
"""

import json
import logging
import re
from typing import Annotated, Sequence, TypedDict, Optional, Dict, Any, List
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage, AIMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

from app.config import is_valid_hf_token
from app.db.database import get_db
from app.db.models import Approval, AuditLog
from app.agent.agent import (
    model_with_tools,
    SYSTEM_PROMPT,
    TOOLS_BY_NAME,
    SAFE_TOOLS,
    SENSITIVE_TOOLS,
    SENSITIVE_TOOL_NAMES,
)

logger = logging.getLogger(__name__)


class SupportAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    customer_id: Optional[int]
    company_id: Optional[int]
    conversation_id: Optional[int]
    agent_run_id: Optional[int]
    pending_action: Optional[Dict[str, Any]]
    approval_status: Optional[str]


def _sanitize_error_message(error_str: str) -> str:
    """
    Remove any potential API keys, tokens, or secret credentials from error strings.
    """
    if not error_str:
        return ""
    sanitized = re.sub(r"hf_[A-Za-z0-9_]{10,}", "[REDACTED_TOKEN]", error_str)
    sanitized = re.sub(r"(token|secret|key|authorization)=['\"][^'\"]+['\"]", r"\1=[REDACTED]", sanitized, flags=re.IGNORECASE)
    return sanitized


def agent_node(state: SupportAgentState) -> Dict[str, Any]:
    """
    Invokes the LLM with the conversation history and bound tools.
    Provides robust, categorized error handling without exposing secrets.
    """
    messages = list(state.get("messages", []))

    # Ensure system instructions are present at the start of conversation
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    # Fast check for unconfigured or placeholder Hugging Face token
    if not is_valid_hf_token():
        msg = (
            "Configuration Notice: The Hugging Face API token is not configured or is set to a placeholder in `.env`. "
            "Please configure a valid `HUGGINGFACEHUB_API_TOKEN` (starting with `hf_`) to enable live AI responses."
        )
        logger.warning("Invocation attempted without a valid Hugging Face API token.")
        return {"messages": [AIMessage(content=msg)]}

    try:
        response = model_with_tools.invoke(messages)
    except Exception as e:
        raw_error = str(e)
        clean_error = _sanitize_error_message(raw_error)
        logger.error(f"Error during LLM invocation: {clean_error}", exc_info=True)

        lower_err = raw_error.lower()
        if "auto-router" in lower_err or "non-hugging face api key" in lower_err:
            response = AIMessage(
                content=(
                    "Authentication Error: Hugging Face auto-router rejected the API key format. "
                    "Please ensure `HUGGINGFACEHUB_API_TOKEN` in your `.env` is a valid Hugging Face token starting with `hf_`."
                )
            )
        elif "401" in raw_error or "unauthorized" in lower_err or "invalid token" in lower_err:
            response = AIMessage(
                content="Authentication Error: The provided Hugging Face API token is invalid or expired. Please check your `.env` credentials."
            )
        elif "402" in raw_error or "credits" in lower_err or "429" in raw_error or "rate limit" in lower_err:
            response = AIMessage(
                content="I apologize for the delay. The AI model service is currently experiencing high traffic or quota limits. Please try again in a moment."
            )
        elif "503" in raw_error or "loading" in lower_err or "temporarily unavailable" in lower_err:
            response = AIMessage(
                content="The AI model is currently warming up on the server. Please retry your request in a few seconds."
            )
        elif "timeout" in lower_err or "timed out" in lower_err:
            response = AIMessage(
                content="The connection to the AI model timed out. Please verify your internet connection and try again."
            )
        else:
            response = AIMessage(
                content=f"I encountered an issue connecting to the resolution service: {clean_error}"
            )

    return {"messages": [response]}


def route_agent_output(state: SupportAgentState) -> str:
    """
    Determines whether to route to safe tools, human approval for sensitive tools, or END.
    """
    messages = state.get("messages", [])
    if not messages:
        return END

    last_message = messages[-1]
    if not isinstance(last_message, AIMessage) or not getattr(last_message, "tool_calls", None):
        return END

    # Check if any requested tool is sensitive
    for tool_call in last_message.tool_calls:
        if tool_call["name"] in SENSITIVE_TOOL_NAMES:
            return "human_approval_node"

    return "safe_tools_node"


def safe_tools_node(state: SupportAgentState) -> Dict[str, Any]:
    """
    Executes non-sensitive, read-only tools automatically.
    """
    last_message = state["messages"][-1]
    tool_messages: List[ToolMessage] = []

    for tool_call in getattr(last_message, "tool_calls", []):
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if tool_name in TOOLS_BY_NAME and tool_name not in SENSITIVE_TOOL_NAMES:
            tool = TOOLS_BY_NAME[tool_name]
            try:
                result = tool.invoke(tool_args)
            except Exception as e:
                result = f"Error executing {tool_name}: {str(e)}"

            tool_message = ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"],
                name=tool_name
            )
            tool_messages.append(tool_message)

    return {"messages": tool_messages}


def human_approval_node(state: SupportAgentState) -> Dict[str, Any]:
    """
    Halts graph execution for sensitive tools, registers Approval in PostgreSQL,
    and resumes execution once approved/denied by a human supervisor.
    """
    last_message = state["messages"][-1]
    tool_messages: List[ToolMessage] = []

    customer_id = state.get("customer_id") or 1
    company_id = state.get("company_id") or 1
    conversation_id = state.get("conversation_id")
    agent_run_id = state.get("agent_run_id")

    for tool_call in getattr(last_message, "tool_calls", []):
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if tool_name in SENSITIVE_TOOL_NAMES:
            action_payload = {
                "tool_name": tool_name,
                "args": tool_args,
                "tool_call_id": tool_call["id"],
                "description": f"Sensitive action '{tool_name}' requested with parameters: {tool_args}",
                "customer_id": customer_id,
                "company_id": company_id,
            }

            # 1. Register Approval in PostgreSQL
            approval_db_id = None
            with get_db() as db:
                approval_rec = Approval(
                    company_id=company_id,
                    customer_id=customer_id,
                    conversation_id=conversation_id,
                    agent_run_id=agent_run_id,
                    action_type=tool_name,
                    target_id=str(tool_args.get("payment_id") or tool_args.get("subscription_id") or tool_args.get("order_id") or ""),
                    action_data=json.dumps(tool_args),
                    reason=tool_args.get("reason", "AI Support resolution proposal"),
                    status="pending",
                    requested_by="ai_agent",
                )
                db.add(approval_rec)
                db.flush()
                approval_db_id = approval_rec.id

                audit = AuditLog(
                    company_id=company_id,
                    customer_id=customer_id,
                    actor_type="ai_agent",
                    action="APPROVAL_REQUESTED",
                    target_type="approval",
                    target_id=str(approval_db_id),
                    details=f"AI requested approval for '{tool_name}' on target '{approval_rec.target_id}'",
                    status="PENDING",
                )
                db.add(audit)
                db.flush()

            # 2. Interrupt graph execution and wait for human supervisor decision
            action_payload["approval_id"] = approval_db_id
            decision = interrupt(action_payload)

            is_approved = bool(decision.get("approved", False))
            feedback = decision.get("feedback", "")
            admin_id = decision.get("admin_user_id")

            # 3. Update PostgreSQL Approval record
            with get_db() as db:
                if approval_db_id:
                    appr = db.query(Approval).filter(Approval.id == approval_db_id).first()
                    if appr:
                        appr.status = "approved" if is_approved else "rejected"
                        appr.approved_by = admin_id
                        appr.notes = feedback
                        db.flush()

            if is_approved:
                tool = TOOLS_BY_NAME[tool_name]
                try:
                    tool_output = tool.invoke(tool_args)
                    content = f"[SUPERVISOR APPROVED]\n{tool_output}"
                except Exception as e:
                    content = f"[SUPERVISOR APPROVED BUT EXECUTION FAILED]\nError: {str(e)}"
            else:
                reason = feedback if feedback else "No specific reason provided by supervisor."
                content = (
                    f"[SUPERVISOR REJECTED]\n"
                    f"The action '{tool_name}' was NOT approved by the human supervisor. "
                    f"Reason: {reason}. Please inform the customer politely, explain the policy basis, and offer to open a support ticket."
                )

            tool_messages.append(
                ToolMessage(
                    content=content,
                    tool_call_id=tool_call["id"],
                    name=tool_name
                )
            )

        elif tool_name in TOOLS_BY_NAME:
            tool = TOOLS_BY_NAME[tool_name]
            try:
                res = tool.invoke(tool_args)
            except Exception as e:
                res = f"Error executing {tool_name}: {str(e)}"
            tool_messages.append(
                ToolMessage(
                    content=str(res),
                    tool_call_id=tool_call["id"],
                    name=tool_name
                )
            )

    return {"messages": tool_messages}


def create_support_graph(checkpointer: Optional[Any] = None):
    """
    Builds and compiles the customer support LangGraph workflow.
    """
    builder = StateGraph(SupportAgentState)

    builder.add_node("agent", agent_node)
    builder.add_node("safe_tools", safe_tools_node)
    builder.add_node("human_approval", human_approval_node)

    builder.add_edge(START, "agent")

    builder.add_conditional_edges(
        "agent",
        route_agent_output,
        {
            "safe_tools_node": "safe_tools",
            "human_approval_node": "human_approval",
            END: END
        }
    )

    builder.add_edge("safe_tools", "agent")
    builder.add_edge("human_approval", "agent")

    return builder.compile(checkpointer=checkpointer)


# Global checkpointer for conversation memory
global_memory = MemorySaver()
app_graph = create_support_graph(checkpointer=global_memory)
