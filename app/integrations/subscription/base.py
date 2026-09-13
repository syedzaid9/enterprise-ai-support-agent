"""
Abstract Base Class for Subscription Provider Integrations in ResolveAI.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseSubscriptionProvider(ABC):

    @abstractmethod
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
        Initialize a recurring subscription authorization session with provider.
        """
        pass

    @abstractmethod
    def get_subscription_status(self, subscription_id: str) -> Dict[str, Any]:
        """
        Fetch real-time subscription details and status from provider.
        """
        pass

    @abstractmethod
    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Cancel an active recurring subscription.
        """
        pass
