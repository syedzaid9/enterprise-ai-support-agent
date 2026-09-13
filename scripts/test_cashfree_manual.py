import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.payment_service import get_subscription, get_payment
from app.tools.billing_tools import check_subscription, check_payment

# Set UTF-8 encoding for Windows console
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    print("=" * 60)
    print("Cashfree Sandbox Live Verification Utility")
    print("=" * 60)

    if len(sys.argv) > 1:
        target_id = sys.argv[1].strip()
    else:
        target_id = input("\nEnter Cashfree Subscription ID or Payment ID: ").strip()

    if not target_id:
        print("Error: No ID provided.")
        return

    print(f"\n[1] Testing LangChain billing tool output for: '{target_id}'")
    if target_id.startswith("sub_") or "sub" in target_id.lower():
        tool_output = check_subscription.invoke({"subscription_id": target_id})
        print("\n--- check_subscription Tool Result ---")
        print(tool_output)

        print("\n[2] Testing Direct REST API Response:")
        try:
            raw_sub = get_subscription(target_id)
            print(json.dumps(raw_sub, indent=2))
        except Exception as e:
            print(f"API Error: {e}")
    else:
        tool_output = check_payment.invoke({"payment_id": target_id})
        print("\n--- check_payment Tool Result ---")
        print(tool_output)

        print("\n[2] Testing Direct REST API Response:")
        try:
            raw_pay = get_payment(target_id)
            print(json.dumps(raw_pay, indent=2))
        except Exception as e:
            print(f"API Error: {e}")


if __name__ == "__main__":
    main()
