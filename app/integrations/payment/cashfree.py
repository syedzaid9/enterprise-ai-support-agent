"""
Cashfree Payment Gateway Integration for ResolveAI.
Implements BasePaymentProvider targeting Cashfree PG Sandbox APIs.
"""

import uuid
import requests
from typing import Dict, Any, Optional

from app.config import (
    CASHFREE_CLIENT_ID,
    CASHFREE_CLIENT_SECRET,
    CASHFREE_API_URL,
    CASHFREE_API_VERSION,
    PAYMENT_API_TIMEOUT,
)
from app.integrations.payment.base import BasePaymentProvider


class CashfreePaymentProvider(BasePaymentProvider):
    """
    Cashfree PG API Client supporting payment order creation, status verification,
    and refund processing in Sandbox environment.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        api_url: Optional[str] = None,
        api_version: Optional[str] = None,
    ):
        self.client_id = client_id or CASHFREE_CLIENT_ID
        self.client_secret = client_secret or CASHFREE_CLIENT_SECRET
        self.api_url = (api_url or CASHFREE_API_URL).rstrip("/")
        self.api_version = api_version or CASHFREE_API_VERSION

    def _get_headers(self) -> Dict[str, str]:
        if not self.client_id or not self.client_secret:
            raise RuntimeError("Cashfree API credentials are not configured in environment (.env).")
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-version": self.api_version,
            "x-client-id": self.client_id,
            "x-client-secret": self.client_secret,
        }

    def create_payment_order(
        self,
        order_id: str,
        amount: float,
        currency: str = "INR",
        customer_id: str = "CUST_DEFAULT",
        customer_email: str = "customer@example.com",
        customer_phone: Optional[str] = None,
        return_url: Optional[str] = None,
        notify_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a payment order in Cashfree Sandbox.
        Returns order details including payment_session_id and sandbox checkout URL.
        """
        url = f"{self.api_url}/orders"
        clean_phone = customer_phone or "9999999999"
        if len(clean_phone) > 10:
            clean_phone = clean_phone[-10:]

        payload = {
            "order_id": order_id,
            "order_amount": round(float(amount), 2),
            "order_currency": currency.upper(),
            "customer_details": {
                "customer_id": str(customer_id)[:50],
                "customer_email": customer_email,
                "customer_phone": clean_phone,
            },
            "order_meta": {
                "return_url": return_url or "https://resolveai.io/payment/status?order_id={order_id}",
            }
        }
        if notify_url:
            payload["order_meta"]["notify_url"] = notify_url

        try:
            resp = requests.post(url, json=payload, headers=self._get_headers(), timeout=PAYMENT_API_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            # Construct a safe sandbox payment link if returned
            session_id = data.get("payment_session_id")
            if session_id:
                data["payment_link"] = f"https://sandbox.cashfree.com/pg/orders/sessions/{session_id}"
            return data
        except requests.HTTPError as e:
            err = resp.text
            try:
                err = resp.json()
            except Exception:
                pass
            raise RuntimeError(f"Cashfree create_payment_order failed ({resp.status_code}): {err}")
        except Exception as e:
            raise RuntimeError(f"Cashfree API connection error: {str(e)}")

    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Retrieve single payment details using payment_id.
        """
        pid = str(payment_id).strip()
        url = f"{self.api_url}/payments/{pid}"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=PAYMENT_API_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            if resp.status_code == 404:
                # Try fallback query against subscriptions/payments
                fallback_url = f"{self.api_url}/subscriptions/payments/{pid}"
                try:
                    f_resp = requests.get(fallback_url, headers=self._get_headers(), timeout=PAYMENT_API_TIMEOUT)
                    f_resp.raise_for_status()
                    f_data = f_resp.json()
                    return f_data[0] if isinstance(f_data, list) and f_data else f_data
                except Exception:
                    pass
                raise ValueError(f"Payment '{pid}' not found in Cashfree Sandbox.")
            raise RuntimeError(f"Cashfree payment lookup error: {resp.text}")
        except Exception as e:
            raise RuntimeError(f"Cashfree payment query failed: {str(e)}")

    def get_order_payments(self, order_id: str) -> Dict[str, Any]:
        """
        Fetch all payment attempts made for a given order_id.
        """
        oid = str(order_id).strip()
        url = f"{self.api_url}/orders/{oid}/payments"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=PAYMENT_API_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch payments for order '{oid}': {str(e)}")

    def request_refund(
        self,
        payment_id: str,
        order_id: Optional[str] = None,
        amount: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a refund in Cashfree Sandbox for an order.
        """
        pid = str(payment_id).strip()
        target_order_id = order_id
        if not target_order_id:
            try:
                payment_info = self.get_payment_status(pid)
                target_order_id = payment_info.get("order_id") or pid
            except Exception:
                target_order_id = pid

        url = f"{self.api_url}/orders/{target_order_id}/refunds"
        refund_id = f"rfnd_{uuid.uuid4().hex[:12]}"
        payload = {"refund_id": refund_id}
        if amount is not None and amount > 0:
            payload["refund_amount"] = round(float(amount), 2)
        if reason:
            payload["refund_note"] = str(reason)[:100]

        try:
            resp = requests.post(url, json=payload, headers=self._get_headers(), timeout=PAYMENT_API_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            err = resp.text
            try:
                err = resp.json()
            except Exception:
                pass
            raise RuntimeError(f"Cashfree refund request failed ({resp.status_code}): {err}")
        except Exception as e:
            raise RuntimeError(f"Cashfree refund execution error: {str(e)}")
