"""
Abstract Base Class for Payment Provider Integrations in ResolveAI.
Allows swapping or extending payment gateways (Cashfree, Stripe, etc.) seamlessly.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BasePaymentProvider(ABC):

    @abstractmethod
    def create_payment_order(
        self,
        order_id: str,
        amount: float,
        currency: str,
        customer_id: str,
        customer_email: str,
        customer_phone: Optional[str] = None,
        return_url: Optional[str] = None,
        notify_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new payment order and return session/token/checkout URL details.
        """
        pass

    @abstractmethod
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Fetch real-time transaction status from the payment provider.
        """
        pass

    @abstractmethod
    def get_order_payments(self, order_id: str) -> Dict[str, Any]:
        """
        Fetch payments associated with an order ID.
        """
        pass

    @abstractmethod
    def request_refund(
        self,
        payment_id: str,
        order_id: Optional[str] = None,
        amount: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Request a refund for an authorized payment transaction.
        """
        pass
