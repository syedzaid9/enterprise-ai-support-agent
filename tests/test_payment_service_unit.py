import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import requests

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services import payment_service


class TestCashfreePaymentServiceUnit(unittest.TestCase):
    """
    Unit test suite for Cashfree Payment Service with 100% mocked REST API calls.
    Verifies behavior for subscription retrieval, payment verification, refund creation,
    and all error/timeout scenarios.
    """

    def setUp(self):
        payment_service.CASHFREE_APP_ID = "TEST_APP_ID_MOCK"
        payment_service.CASHFREE_SECRET_KEY = "TEST_SECRET_KEY_MOCK"
        payment_service.CASHFREE_API_URL = "https://sandbox.cashfree.com/pg"
        payment_service.CASHFREE_API_VERSION = "2023-08-01"
        payment_service.PAYMENT_API_TIMEOUT = 10

    def test_get_headers_security(self):
        """Test authentication headers generation."""
        headers = payment_service._get_headers()
        self.assertEqual(headers["x-client-id"], "TEST_APP_ID_MOCK")
        self.assertEqual(headers["x-client-secret"], "TEST_SECRET_KEY_MOCK")
        self.assertEqual(headers["x-api-version"], "2023-08-01")
        self.assertEqual(headers["accept"], "application/json")
        self.assertEqual(headers["content-type"], "application/json")

    @patch("requests.get")
    def test_get_subscription_initialized(self, mock_get):
        """Test retrieving a Cashfree subscription with status INITIALIZED."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "subscription_id": "sub_sandbox_001",
            "subscription_status": "INITIALIZED",
            "authorization_status": "INITIALIZED",
            "customer_details": {
                "customer_name": "Zaid Test",
                "customer_email": "zaid@example.com",
                "customer_phone": "9999999999"
            },
            "plan_details": {
                "plan_id": "plan_enterprise_pro",
                "plan_name": "Enterprise Pro Tier",
                "plan_type": "MONTHLY",
                "plan_recurring_amount": 2999.0,
                "plan_currency": "INR"
            },
            "first_charge_date": "2026-10-01",
            "next_schedule_date": "2026-11-01",
            "subscription_url": "https://sandbox.cashfree.com/sub/sub_sandbox_001"
        }
        mock_get.return_value = mock_resp

        result = payment_service.get_subscription("sub_sandbox_001")

        self.assertEqual(result["subscription_id"], "sub_sandbox_001")
        self.assertEqual(result["subscription_status"], "INITIALIZED")
        self.assertEqual(result["authorization_status"], "INITIALIZED")
        self.assertEqual(result["customer_details"]["customer_name"], "Zaid Test")
        self.assertEqual(result["plan_details"]["plan_recurring_amount"], 2999.0)
        self.assertEqual(result["plan_details"]["plan_currency"], "INR")

    @patch("requests.get")
    def test_get_subscription_active(self, mock_get):
        """Test retrieving an ACTIVE Cashfree subscription."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "subscription_id": "sub_sandbox_active",
            "subscription_status": "ACTIVE",
            "authorization_status": "SUCCESS",
            "customer_details": {
                "customer_name": "Enterprise Client",
                "customer_email": "corp@client.com",
                "customer_phone": "9876543210"
            },
            "plan_details": {
                "plan_id": "plan_annual",
                "plan_name": "Annual Business",
                "plan_type": "ANNUAL",
                "plan_recurring_amount": 24999.0,
                "plan_currency": "INR"
            }
        }
        mock_get.return_value = mock_resp

        result = payment_service.get_subscription("sub_sandbox_active")

        self.assertEqual(result["subscription_status"], "ACTIVE")
        self.assertEqual(result["authorization_status"], "SUCCESS")

    def test_get_subscription_empty_id(self):
        """Test empty subscription ID validation."""
        with self.assertRaises(ValueError) as ctx:
            payment_service.get_subscription("   ")
        self.assertIn("Subscription ID must not be empty", str(ctx.exception))

    @patch("requests.get")
    def test_get_subscription_404_not_found(self, mock_get):
        """Test handling of 404 response for non-existent subscription."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = {"message": "Subscription not found"}
        mock_resp.raise_for_status.side_effect = requests.HTTPError("404 Not Found", response=mock_resp)
        mock_get.return_value = mock_resp

        with self.assertRaises(ValueError) as ctx:
            payment_service.get_subscription("sub_nonexistent")
        self.assertIn("Subscription 'sub_nonexistent' not found", str(ctx.exception))

    @patch("requests.get")
    def test_get_subscription_timeout(self, mock_get):
        """Test handling of requests Timeout exception."""
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        with self.assertRaises(RuntimeError) as ctx:
            payment_service.get_subscription("sub_timeout")
        self.assertIn("timed out", str(ctx.exception))

    @patch("requests.get")
    def test_get_payment_success(self, mock_get):
        """Test retrieving a successful payment transaction."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "cf_payment_id": 987654321,
            "order_id": "order_cf_001",
            "payment_status": "SUCCESS",
            "payment_amount": 1499.0,
            "payment_currency": "INR",
            "payment_time": "2026-09-12T10:00:00+05:30",
            "payment_message": "Transaction Successful",
            "payment_method": {"netbanking": {"channel": "hdfc"}}
        }
        mock_get.return_value = mock_resp

        result = payment_service.get_payment("987654321")

        self.assertEqual(result["payment_id"], "987654321")
        self.assertEqual(result["order_id"], "order_cf_001")
        self.assertEqual(result["payment_status"], "SUCCESS")
        self.assertEqual(result["payment_amount"], 1499.0)
        self.assertEqual(result["payment_currency"], "INR")

    @patch("requests.get")
    def test_get_payment_failed(self, mock_get):
        """Test retrieving a failed payment transaction."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "cf_payment_id": "pay_failed_1",
            "payment_status": "FAILED",
            "payment_amount": 500.0,
            "payment_currency": "INR",
            "payment_message": "Bank declined transaction"
        }
        mock_get.return_value = mock_resp

        result = payment_service.get_payment("pay_failed_1")
        self.assertEqual(result["payment_status"], "FAILED")
        self.assertEqual(result["payment_message"], "Bank declined transaction")

    def test_get_payment_empty_id(self):
        """Test empty payment ID validation."""
        with self.assertRaises(ValueError) as ctx:
            payment_service.get_payment("")
        self.assertIn("Payment ID must not be empty", str(ctx.exception))

    @patch("requests.post")
    def test_create_refund_success(self, mock_post):
        """Test issuing a refund via Cashfree Sandbox."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "cf_refund_id": 555666,
            "refund_id": "ref_mock_555666",
            "refund_status": "SUCCESS",
            "refund_amount": 1000.0,
            "refund_currency": "INR",
            "refund_note": "Damaged goods in delivery"
        }
        mock_post.return_value = mock_resp

        result = payment_service.create_refund(
            payment_id="pay_999",
            order_id="order_999",
            amount=1000.0,
            reason="Damaged goods in delivery"
        )

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["refund_id"], "ref_mock_555666")
        self.assertEqual(result["amount_refunded"], 1000.0)
        self.assertIn("successfully", result["message"])

    @patch("requests.post")
    def test_create_refund_failure_response(self, mock_post):
        """Test error handling when Cashfree refund endpoint returns 400."""
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {
            "message": "Refund amount exceeds refundable balance"
        }
        mock_resp.raise_for_status.side_effect = requests.HTTPError("400 Client Error", response=mock_resp)
        mock_post.return_value = mock_resp

        with self.assertRaises(RuntimeError) as ctx:
            payment_service.create_refund(payment_id="pay_999", order_id="order_999", amount=50000.0)
        self.assertIn("Refund amount exceeds refundable balance", str(ctx.exception))



if __name__ == "__main__":
    unittest.main()
