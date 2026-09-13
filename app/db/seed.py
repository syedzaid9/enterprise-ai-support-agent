"""
Database seed utility for ResolveAI.
Populates initial company, demo customer, demo admin, and test records if database is empty.
Idempotent and safe to run multiple times.
"""

import sys
import datetime
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.db.database import init_db, get_db
from app.db.models import (
    Company,
    User,
    Customer,
    Subscription,
    Payment,
    Ticket,
    Approval,
    AuditLog,
    KnowledgeDocument,
)
from app.auth.security import hash_password


def seed_database():
    """
    Seed initial enterprise data.
    """
    print("[+] Initializing database tables...")
    init_db()

    with get_db() as db:
        # 1. Company
        company = db.query(Company).filter(Company.name == "ResolveAI Enterprise Corp").first()
        if not company:
            company = Company(name="ResolveAI Enterprise Corp")
            db.add(company)
            db.flush()
            print(f"[+] Created Company: {company.name} (ID: {company.id})")

        # 2. Demo Admin User
        admin_user = db.query(User).filter(User.email == "admin@resolveai.io").first()
        if not admin_user:
            admin_user = User(
                company_id=company.id,
                email="admin@resolveai.io",
                password_hash=hash_password("admin123"),
                role="admin",
                is_active=True,
            )
            db.add(admin_user)
            db.flush()
            print(f"[+] Created Admin User: admin@resolveai.io / admin123")

        # 3. Demo Customer 1 (Alex Rivera)
        cust_user1 = db.query(User).filter(User.email == "customer@resolveai.io").first()
        if not cust_user1:
            cust_user1 = User(
                company_id=company.id,
                email="customer@resolveai.io",
                password_hash=hash_password("password123"),
                role="customer",
                is_active=True,
            )
            db.add(cust_user1)
            db.flush()

            customer1 = Customer(
                user_id=cust_user1.id,
                company_id=company.id,
                external_customer_id="CF_CUST_1001",
                name="Alex Rivera",
                email="customer@resolveai.io",
                phone="+1 (555) 382-9014",
                status="ACTIVE",
            )
            db.add(customer1)
            db.flush()

            # Subscription
            sub1 = Subscription(
                customer_id=customer1.id,
                provider="cashfree",
                external_subscription_id="sub_sb_pro_1001",
                plan="Pro Monthly",
                amount=499.0,
                currency="INR",
                status="ACTIVE",
                next_billing_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=22),
            )
            db.add(sub1)

            # Payment
            pay1 = Payment(
                customer_id=customer1.id,
                provider="cashfree",
                external_payment_id="CF_PAY_994201",
                order_id="order_cf_9942",
                amount=499.0,
                currency="INR",
                status="SUCCESS",
                payment_method="UPI / HDFC Netbanking",
            )
            db.add(pay1)

            # Ticket
            ticket1 = Ticket(
                ticket_number="TK-1024",
                company_id=company.id,
                customer_id=customer1.id,
                title="Delivery transit delay inquiry",
                description="Package tracking indicates 3-day customs delay.",
                priority="normal",
                status="in_progress",
            )
            db.add(ticket1)
            print(f"[+] Created Demo Customer: customer@resolveai.io / password123 (Alex Rivera)")

        # 4. Demo Customer 2 (John Doe)
        cust_user2 = db.query(User).filter(User.email == "john@example.com").first()
        if not cust_user2:
            cust_user2 = User(
                company_id=company.id,
                email="john@example.com",
                password_hash=hash_password("password123"),
                role="customer",
                is_active=True,
            )
            db.add(cust_user2)
            db.flush()

            customer2 = Customer(
                user_id=cust_user2.id,
                company_id=company.id,
                external_customer_id="CF_CUST_1002",
                name="John Doe",
                email="john@example.com",
                phone="+1 (555) 881-2309",
                status="ACTIVE",
            )
            db.add(customer2)
            db.flush()

            sub2 = Subscription(
                customer_id=customer2.id,
                provider="cashfree",
                external_subscription_id="sub_sb_ent_1002",
                plan="Enterprise Annual",
                amount=4999.0,
                currency="INR",
                status="ACTIVE",
                next_billing_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=120),
            )
            db.add(sub2)

            pay2 = Payment(
                customer_id=customer2.id,
                provider="cashfree",
                external_payment_id="CF_PAY_881902",
                order_id="order_cf_8819",
                amount=4999.0,
                currency="INR",
                status="SUCCESS",
                payment_method="Corporate Credit Card",
            )
            db.add(pay2)

            ticket2 = Ticket(
                ticket_number="TK-1025",
                company_id=company.id,
                customer_id=customer2.id,
                title="Refund requested for damaged item",
                description="Item arrived with packaging crushed during transit.",
                priority="high",
                status="open",
            )
            db.add(ticket2)

            # Pending Approval
            approval1 = Approval(
                company_id=company.id,
                customer_id=customer2.id,
                action_type="refund_payment",
                action_data='{"payment_id": "CF_PAY_881902", "amount": 4999.0, "reason": "Damaged goods in transit"}',
                status="pending",
                notes="Customer submitted photo verification of crushed carton.",
            )
            db.add(approval1)
            print(f"[+] Created Demo Customer: john@example.com / password123 (John Doe)")

        # 5. Knowledge Documents Registration
        docs = [
            "refund_policy.txt",
            "cancellation_policy.txt",
            "shipping_policy.txt",
            "warranty_and_repair_policy.txt",
            "billing_and_payment_faq.txt",
            "account_security_and_privacy.txt",
        ]
        for doc_name in docs:
            existing_doc = (
                db.query(KnowledgeDocument)
                .filter(KnowledgeDocument.filename == doc_name, KnowledgeDocument.company_id == company.id)
                .first()
            )
            if not existing_doc:
                db.add(KnowledgeDocument(company_id=company.id, filename=doc_name, status="active"))

        print("[OK] Database seed completed successfully.")


if __name__ == "__main__":
    seed_database()
