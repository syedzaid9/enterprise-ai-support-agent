from typing import Union
from langchain_core.tools import tool
from app.services.customer_service import get_customer


@tool
def get_customer_details(customer_id: Union[int, str]) -> str:
    """
    Retrieve customer account and profile information using the customer ID from PostgreSQL database.
    Use this tool whenever the customer provides their customer ID or asks about account details.
    """
    try:
        try:
            cid = int(str(customer_id).strip())
        except ValueError:
            return f"Invalid customer ID '{customer_id}'. Customer ID must be an integer."

        customer = get_customer(cid)

        name = customer.get("name", "")
        if isinstance(name, dict):
            full_name = f"{name.get('firstname', '')} {name.get('lastname', '')}".strip()
        else:
            full_name = str(name)

        return (
            f"Customer account details retrieved successfully:\n"
            f"- Customer ID: {customer.get('id')}\n"
            f"- External Customer ID: {customer.get('external_customer_id') or 'N/A'}\n"
            f"- Name: {full_name or 'N/A'}\n"
            f"- Email: {customer.get('email', 'N/A')}\n"
            f"- Phone: {customer.get('phone', 'N/A')}\n"
            f"- Status: {customer.get('status', 'ACTIVE')}"
        )
    except ValueError as ve:
        return f"Customer profile not found: {str(ve)}"
    except Exception as e:
        return f"Unable to retrieve customer information: {str(e)}"