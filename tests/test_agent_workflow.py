import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.types import Command
from app.graph.workflow import create_support_graph, MemorySaver
from app.db.database import init_db
from app.db.seed import seed_database
from app.tools.customer_tools import get_customer_details
from app.tools.billing_tools import check_subscription, check_payment, refund_payment
from app.tools.knowledge_tools import search_company_policy
from app.tools.ticket_tools import create_support_ticket, cancel_order_request


class TestAgentWorkflow(unittest.TestCase):
    """
    Integration and unit tests for enterprise agent tools and LangGraph workflow orchestration.
    """

    @classmethod
    def setUpClass(cls):
        init_db()
        seed_database()

    def test_customer_tool(self):
        """Test customer database CRM lookup and not-found behavior."""
        cust_res = get_customer_details.invoke({"customer_id": 1})
        self.assertIn("Customer account details retrieved successfully", cust_res)

        not_found_res = get_customer_details.invoke({"customer_id": 99999})
        self.assertIn("Customer profile not found", not_found_res)

    def test_policy_rag_tool(self):
        """Test RAG knowledge base search."""
        policy_res = search_company_policy.invoke({"query": "refund policy eligibility"})
        self.assertIn("refund", policy_res.lower())

    def test_ticket_tool(self):
        """Test support ticket creation."""
        ticket_res = create_support_ticket.invoke({
            "customer_id": 1,
            "issue_description": "Damaged goods",
            "priority": "high"
        })
        self.assertIn("TICK-1-", ticket_res)

    def test_cancel_order_tool(self):
        """Test cancellation request tool."""
        cancel_res = cancel_order_request.invoke({
            "order_id": 12345,
            "reason": "Accidental order"
        })
        self.assertIn("ORDER CANCELLATION EXECUTED SUCCESSFULLY", cancel_res)

    @patch("requests.get")
    def test_cashfree_subscription_tool(self, mock_get):
        """Test check_subscription tool with mock Cashfree response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "subscription_id": "sub_test_123456",
            "subscription_status": "INITIALIZED",
            "authorization_status": "INITIALIZED",
            "customer_details": {
                "customer_name": "John Doe",
                "customer_email": "john@example.com",
                "customer_phone": "1234567890"
            },
            "plan_details": {
                "plan_id": "plan_monthly_pro",
                "plan_name": "Pro Monthly",
                "plan_type": "MONTHLY",
                "plan_recurring_amount": 999.0,
                "plan_currency": "INR"
            },
            "first_charge_date": "2026-10-01",
            "next_schedule_date": "2026-11-01"
        }
        mock_get.return_value = mock_resp

        sub_res = check_subscription.invoke({"subscription_id": "sub_test_123456"})
        self.assertIn("INITIALIZED", sub_res)
        self.assertIn("Pro Monthly", sub_res)

    @patch("requests.get")
    def test_cashfree_payment_tool(self, mock_get):
        """Test check_payment tool with mock Cashfree response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "cf_payment_id": 789123456,
            "order_id": "order_test_789",
            "payment_status": "SUCCESS",
            "payment_amount": 999.0,
            "payment_currency": "INR",
            "payment_time": "2026-09-12T12:00:00+05:30",
            "payment_message": "Transaction Successful"
        }
        mock_get.return_value = mock_resp

        pay_res = check_payment.invoke({"payment_id": "789123456"})
        self.assertIn("SUCCESS", pay_res)
        self.assertIn("999.0 INR", pay_res)

    @patch("requests.post")
    def test_cashfree_refund_tool(self, mock_post):
        """Test refund_payment tool with mock Cashfree response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "cf_refund_id": 444555,
            "refund_id": "ref_444555",
            "refund_status": "SUCCESS",
            "refund_amount": 999.0,
            "refund_currency": "INR",
            "refund_note": "Damaged item during transit"
        }
        mock_post.return_value = mock_resp

        refund_res = refund_payment.invoke({
            "payment_id": "789123456",
            "amount": 999.0,
            "reason": "Damaged item"
        })
        self.assertIn("CASHFREE REFUND EXECUTED SUCCESSFULLY", refund_res)

    @patch("app.graph.workflow.is_valid_hf_token", return_value=True)
    @patch("app.graph.workflow.model_with_tools")
    def test_workflow_safe_tool_execution(self, mock_model, mock_is_valid):
        """Test safe tool execution in LangGraph loop."""
        # First turn: LLM calls customer tool
        mock_model.invoke.side_effect = [
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "get_customer_details",
                    "args": {"customer_id": 1},
                    "id": "call_cust_1",
                    "type": "tool_call"
                }]
            ),
            # Second turn: LLM provides final answer based on ToolMessage
            AIMessage(content="Customer 1 is John Doe (john@gmail.com).")
        ]

        checkpointer = MemorySaver()
        graph = create_support_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "test_safe_tools_thread"}}

        res = graph.invoke(
            {"messages": [HumanMessage(content="Get customer details for customer 1")]},
            config=config
        )

        final_content = res["messages"][-1].content
        self.assertIn("John Doe", final_content)

    @patch("app.graph.workflow.is_valid_hf_token", return_value=True)
    @patch("app.graph.workflow.model_with_tools")
    @patch("requests.post")
    def test_workflow_human_approval_approved(self, mock_post, mock_model, mock_is_valid):
        """Test sensitive tool interrupt and human approval execution."""
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {
            "refund_id": "ref_999",
            "refund_status": "SUCCESS",
            "refund_amount": 500.0,
        }
        mock_post.return_value = mock_post_resp

        # First turn: LLM requests sensitive refund_payment tool
        mock_model.invoke.side_effect = [
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "refund_payment",
                    "args": {"payment_id": "pay_test_1", "amount": 500.0, "reason": "Damaged goods"},
                    "id": "call_ref_1",
                    "type": "tool_call"
                }]
            ),
            # Resumed turn: LLM confirms refund to customer
            AIMessage(content="Your refund of 500.0 INR has been approved and processed.")
        ]

        checkpointer = MemorySaver()
        graph = create_support_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "test_human_approval_thread"}}

        res = graph.invoke(
            {"messages": [HumanMessage(content="Please refund payment pay_test_1")]},
            config=config
        )

        # Check that execution was interrupted
        state = graph.get_state(config)
        self.assertTrue(bool(state.tasks and state.tasks[0].interrupts))
        interrupt_data = state.tasks[0].interrupts[0].value
        self.assertEqual(interrupt_data["tool_name"], "refund_payment")

        # Resume with supervisor approval
        resumed = graph.invoke(
            Command(resume={"approved": True, "feedback": "Supervisor approved under 30-day guarantee."}),
            config=config
        )
        final_content = resumed["messages"][-1].content
        self.assertIn("refund", final_content.lower())

    @patch("app.graph.workflow.is_valid_hf_token", return_value=True)
    @patch("app.graph.workflow.model_with_tools")
    def test_workflow_human_approval_rejected(self, mock_model, mock_is_valid):
        """Test sensitive tool interrupt and human supervisor rejection."""
        mock_model.invoke.side_effect = [
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "refund_payment",
                    "args": {"payment_id": "pay_test_2", "amount": 1000.0, "reason": "Buyer remorse"},
                    "id": "call_ref_2",
                    "type": "tool_call"
                }]
            ),
            AIMessage(content="I apologize, but the refund was not approved by the supervisor because it exceeds the policy window.")
        ]

        checkpointer = MemorySaver()
        graph = create_support_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "test_rejection_thread"}}

        graph.invoke(
            {"messages": [HumanMessage(content="Refund payment pay_test_2")]},
            config=config
        )

        state = graph.get_state(config)
        self.assertTrue(bool(state.tasks and state.tasks[0].interrupts))

        # Resume with supervisor rejection
        resumed = graph.invoke(
            Command(resume={"approved": False, "feedback": "Out of 30-day refund window."}),
            config=config
        )
        final_content = resumed["messages"][-1].content
        self.assertIn("not approved", final_content.lower())

    def test_unconfigured_token_notice(self):
        """Test safe configuration notice when no valid token is present."""
        with patch("app.graph.workflow.is_valid_hf_token", return_value=False):
            checkpointer = MemorySaver()
            graph = create_support_graph(checkpointer=checkpointer)
            config = {"configurable": {"thread_id": "test_unconfigured_thread"}}

            res = graph.invoke(
                {"messages": [HumanMessage(content="Hello")]},
                config=config
            )
            final_content = res["messages"][-1].content
            self.assertIn("Configuration Notice", final_content)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    unittest.main()


