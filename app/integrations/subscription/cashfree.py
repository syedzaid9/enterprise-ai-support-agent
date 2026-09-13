"""
Cashfree Subscription Integration for ResolveAI.
Implements recurring subscription management targeting Cashfree Subscriptions Sandbox API.
"""

import requests
from typing import Dict, Any, Optional

from app.config import (
    CASHFREE_CLIENT_ID,
    CASHFREE_CLIENT_SECRET,
    CASHFREE_API_URL,
    CASHFREE_API_VERSION,
    PAYMENT_API_TIMEOUT,
)
from app.integrations.subscription.base import BaseSubscriptionProvider


class CashfreeSubscriptionProvider(BaseSubscriptionProvider):

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

    def create_subscription(
        self,
        subscription_id: str,
        plan_id: str,
        customer_id: str,
        customer_name: str,
        customer_email: str,
        customer_phone: Optional[str] = None,
        return_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a recurring subscription session in Cashfree Sandbox.
        """
        url = f"{self.api_url}/subscriptions"
        clean_phone = customer_phone or "9999999999"
        if len(clean_phone) > 10:
            clean_phone = clean_phone[-10:]

        payload = {
            "subscription_id": subscription_id,
            "plan_details": {
                "plan_id": plan_id,
            },
            "customer_details": {
                "customer_id": str(customer_id)[:50],
                "customer_name": customer_name,
                "customer_email": customer_email,
                "customer_phone": clean_phone,
            },
            "subscription_meta": {
                "return_url": return_url or "https://resolveai.io/subscription/verify?sub_id={subscription_id}",
            }
        }

        try:
            resp = requests.post(url, json=payload, headers=self._get_headers(), timeout=PAYMENT_API_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return data
        except requests.HTTPError as e:
            err = resp.text
            try:
                err = resp.json()
            except Exception:
                pass
            raise RuntimeError(f"Cashfree create_subscription failed ({resp.status_code}): {err}")
        except Exception as e:
            raise RuntimeError(f"Cashfree subscription API error: {str(e)}")

    def get_subscription_status(self, subscription_id: str) -> Dict[str, Any]:
        """
        Retrieve real-time subscription details from Cashfree Sandbox.
        """
        sid = str(subscription_id).strip()
        url = f"{self.api_url}/subscriptions/{sid}"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=PAYMENT_API_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            if resp.status_code == 404:
                raise ValueError(f"Subscription '{sid}' not found in Cashfree Sandbox.")
            raise RuntimeError(f"Cashfree subscription query error: {resp.text}")
        except Exception as e:
            raise RuntimeError(f"Failed to query Cashfree subscription: {str(e)}")

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Cancel a recurring subscription in Cashfree Sandbox.
        """
        sid = str(subscription_id).strip()
        url = f"{self.api_url}/subscriptions/{sid}/cancel"
        try:
            resp = requests.post(url, headers=self._get_headers(), timeout=PAYMENT_API_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            raise RuntimeError(f"Cashfree subscription cancellation failed ({resp.status_code}): {resp.text}")
        except Exception as e:
            raise RuntimeError(f"Failed to cancel Cashfree subscription: {str(e)}")
