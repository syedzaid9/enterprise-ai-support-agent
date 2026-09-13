"""
Customer Dashboard for ResolveAI.
Provides authenticated customer support chat connected to LangGraph,
live subscription details, payment history, and ticket management.
Adheres strictly to the Pure Real Data principle.
"""

import uuid
import datetime
import streamlit as st
import pandas as pd
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.types import Command
from app.graph.workflow import app_graph
from app.services.customer_context import get_customer_context, create_customer_ticket
from app.services.payment_service import create_customer_payment_order
from app.services.subscription_service import create_customer_subscription


def render_customer_dashboard():
    """
    Render authenticated customer portal.
    """
    user_id = st.session_state.get("authenticated_user_id")
    context = get_customer_context(user_id)

    if not context:
        st.error("Unable to load customer profile. Please log in again.")
        if st.button("Return to Login"):
            st.session_state.authenticated_user_id = None
            st.session_state.authenticated_role = None
            st.rerun()
        return

    # Session state setup
    if "customer_nav" not in st.session_state:
        st.session_state.customer_nav = "overview"

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"cust_{context['customer_id']}_{str(uuid.uuid4())[:8]}"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "pending_action" not in st.session_state:
        st.session_state.pending_action = None

    # =========================================================================
    # SIDEBAR: NAVIGATION & LIVE CUSTOMER INFO
    # =========================================================================
    with st.sidebar:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
            <div class="brand-icon-box">⚡</div>
            <div>
                <div class="brand-title">ResolveAI</div>
                <div class="brand-sub">Customer Portal</div>
            </div>
        </div>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; margin-bottom: 20px;">
            <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase;">Logged In As</div>
            <div style="font-size: 14px; font-weight: 800; color: #0f172a; margin-top: 2px;">{context['name']}</div>
            <div style="font-size: 12px; color: #64748b;">{context['email']}</div>
            <div style="margin-top: 8px;">
                <span class="badge-purple">ID: {context['external_customer_id'] or context['customer_id']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='font-size: 11.5px; font-weight: 700; color: #94a3b8; margin-bottom: 8px; text-transform: uppercase;'>Navigation</div>", unsafe_allow_html=True)

        nav_items = {
            "overview": ("📊 Overview", "primary" if st.session_state.customer_nav == "overview" else "secondary"),
            "chat": ("🤖 AI Support Copilot", "primary" if st.session_state.customer_nav == "chat" else "secondary"),
            "subscription": ("💳 Subscription", "primary" if st.session_state.customer_nav == "subscription" else "secondary"),
            "payments": ("💰 Payment History", "primary" if st.session_state.customer_nav == "payments" else "secondary"),
            "tickets": ("🎫 My Tickets", "primary" if st.session_state.customer_nav == "tickets" else "secondary"),
            "account": ("👤 Profile", "primary" if st.session_state.customer_nav == "account" else "secondary"),
        }

        for nav_k, (nav_lbl, btn_t) in nav_items.items():
            if st.button(nav_lbl, type=btn_t, use_container_width=True, key=f"cnav_{nav_k}"):
                st.session_state.customer_nav = nav_k
                st.rerun()

        st.markdown("<hr style='margin: 20px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.authenticated_user_id = None
            st.session_state.authenticated_role = None
            st.session_state.portal_selection = None
            st.session_state.messages = []
            st.rerun()

    # =========================================================================
    # VIEW 0: OVERVIEW
    # =========================================================================
    if st.session_state.customer_nav == "overview":
        st.markdown("### 📊 Account Overview")
        st.markdown(f"Welcome back, **{context['name']}**! Here is your current account snapshot.")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            sub_title = context["subscription"]["plan"] if context.get("subscription") else "No Subscription"
            st.metric(label="Active Plan", value=sub_title)
        with m2:
            sub_status = context["subscription"]["status"] if context.get("subscription") else "None"
            st.metric(label="Subscription Status", value=sub_status)
        with m3:
            total_payments = len(context.get("payments", []))
            st.metric(label="Total Payments", value=str(total_payments))
        with m4:
            open_tickets = len([t for t in context.get("tickets", []) if t["status"] in ["open", "in_progress"]])
            st.metric(label="Open Tickets", value=str(open_tickets))

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        c_sub, c_pay = st.columns(2, gap="medium")
        with c_sub:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='saas-card-header'><span>Subscription Snapshot</span></div>", unsafe_allow_html=True)
            if context.get("subscription"):
                sub = context["subscription"]
                st.write(f"**Plan:** {sub['plan']}")
                st.write(f"**Amount:** ₹{sub['amount']} {sub['currency']} / month")
                st.write(f"**Status:** {sub['status']}")
                st.write(f"**Next Renewal:** {sub['next_billing_date']}")
            else:
                st.info("No active subscription found.")
            st.markdown("</div>", unsafe_allow_html=True)

        with c_pay:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='saas-card-header'><span>Recent Transaction</span></div>", unsafe_allow_html=True)
            if context.get("payments"):
                p = context["payments"][0]
                st.write(f"**Payment ID:** `{p['payment_id']}`")
                st.write(f"**Amount:** ₹{p['amount']} {p['currency']}")
                st.write(f"**Status:** {p['status']}")
                st.write(f"**Date:** {p['date']}")
            else:
                st.info("No payment history.")
            st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # VIEW 1: AI SUPPORT CHAT
    # =========================================================================
    elif st.session_state.customer_nav == "chat":
        col_chat, col_info = st.columns([2.2, 1], gap="large")

        with col_chat:
            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 40px; height: 40px; background: #4f46e5; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px;">🤖</div>
                    <div>
                        <div style="font-size: 18px; font-weight: 800; color: #0f172a;">AI Support Copilot</div>
                        <div style="font-size: 12.5px; color: #64748b;">Connected to verified account of <b>{context['name']}</b></div>
                    </div>
                </div>
                <div class="badge-green">● Ready to assist</div>
            </div>
            """, unsafe_allow_html=True)

            # Quick Prompt Chips
            st.markdown("<div style='font-size: 11px; font-weight: 700; color: #94a3b8; margin-bottom: 6px; text-transform: uppercase;'>Suggested Inquiries:</div>", unsafe_allow_html=True)
            q1, q2, q3, q4 = st.columns(4)
            with q1:
                if st.button("💳 Subscription Status", use_container_width=True):
                    sub_val = context['subscription']['external_subscription_id'] if context.get('subscription') else "my current plan"
                    st.session_state.quick_query = f"Can you check my subscription status for {sub_val}?"
            with q2:
                if st.button("📄 Payment Verification", use_container_width=True):
                    pay_val = context['payments'][0]['payment_id'] if context.get('payments') else "my recent payment"
                    st.session_state.quick_query = f"What is the status of my payment {pay_val}?"
            with q3:
                if st.button("🔄 Refund Policy", use_container_width=True):
                    st.session_state.quick_query = "What is the policy for refunds on damaged or delayed items?"
            with q4:
                if st.button("🎫 Open Ticket", use_container_width=True):
                    st.session_state.quick_query = f"Please create a support ticket for customer {context['customer_id']} regarding delivery delay."

            st.markdown("<hr style='margin: 14px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

            # Initial greeting if empty
            if not st.session_state.messages:
                st.markdown(f"""
                <div style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 16px;">
                    <div style="width: 32px; height: 32px; background: #4f46e5; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-size: 16px; flex-shrink: 0; margin-top: 2px;">⚡</div>
                    <div>
                        <div style="font-size: 12px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">Resolve Copilot</div>
                        <div class="copilot-bubble">
                            Hello <b>{context['name']}</b>! I am your AI Support Copilot. I have access to your verified account details, subscriptions, and Cashfree transactions. How can I assist you today?
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Render message stream
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div style="text-align: right; margin-bottom: 14px;">
                        <div style="font-size: 11.5px; color: #64748b; margin-bottom: 4px;"><b>You ({context['name']})</b></div>
                        <div class="user-bubble">{msg['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif msg["role"] == "assistant":
                    st.markdown(f"""
                    <div style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 16px;">
                        <div style="width: 32px; height: 32px; background: #4f46e5; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-size: 16px; flex-shrink: 0; margin-top: 2px;">⚡</div>
                        <div>
                            <div style="font-size: 12px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">Resolve Copilot</div>
                            <div class="copilot-bubble">
                                {msg['content']}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Pending Supervisor Action Alert
            if st.session_state.pending_action:
                act = st.session_state.pending_action
                st.warning(f"⏳ SUPERVISOR AUTHORIZATION PENDING: The AI Agent prepared a sensitive action: `{act.get('tool_name')}`. A support supervisor has been notified.")

            # Chat Input
            user_input = st.chat_input("Ask a question about your account, payment, or policy...")

            if "quick_query" in st.session_state and st.session_state.quick_query:
                user_input = st.session_state.quick_query
                st.session_state.quick_query = None

            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                config = {"configurable": {"thread_id": st.session_state.thread_id}}

                with st.spinner("AI Copilot investigating and checking records..."):
                    try:
                        result = app_graph.invoke(
                            {
                                "messages": [HumanMessage(content=user_input)],
                                "customer_id": context["customer_id"],
                                "company_id": context["company_id"],
                            },
                            config=config,
                        )

                        state = app_graph.get_state(config)
                        if state.tasks and state.tasks[0].interrupts:
                            interrupt_val = state.tasks[0].interrupts[0].value
                            st.session_state.pending_action = interrupt_val
                            agent_msg = (
                                f"I have verified your request and eligibility. Because `{interrupt_val.get('tool_name')}` is a financial/sensitive action, "
                                f"it has been paused for Human Supervisor Authorization. You will be updated once approved."
                            )
                        else:
                            st.session_state.pending_action = None
                            final_turn = result["messages"][-1]
                            agent_msg = final_turn.content if isinstance(final_turn, AIMessage) else str(final_turn)

                        st.session_state.messages.append({"role": "assistant", "content": agent_msg})
                    except Exception as e:
                        st.session_state.messages.append({"role": "assistant", "content": f"Unable to process request: {str(e)}"})

                st.rerun()

        # Right Column: Live Context Panel
        with col_info:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='saas-card-header'><span>Active Subscription</span><span class='badge-purple'>Cashfree Sandbox</span></div>", unsafe_allow_html=True)
            if context.get("subscription"):
                sub = context["subscription"]
                st.write(f"**Plan:** {sub['plan']}")
                st.write(f"**Amount:** ₹{sub['amount']} {sub['currency']} / month")
                st.write(f"**Status:** {sub['status']}")
                st.write(f"**Next Renewal:** {sub['next_billing_date']}")
                st.caption(f"Ref: {sub['external_subscription_id']}")
            else:
                st.info("No active subscription found.")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='saas-card-header'><span>Recent Payment</span></div>", unsafe_allow_html=True)
            if context.get("payments"):
                p = context["payments"][0]
                st.write(f"**Amount:** ₹{p['amount']} {p['currency']}")
                st.write(f"**Status:** {p['status']}")
                st.write(f"**Date:** {p['date']}")
                st.caption(f"ID: {p['payment_id']}")
            else:
                st.info("No payment history.")
            st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # VIEW 2: SUBSCRIPTION
    # =========================================================================
    elif st.session_state.customer_nav == "subscription":
        st.markdown("### 💳 Subscription Management")
        st.markdown("Review your active plan, billing dates, and subscribe in Cashfree Sandbox.")

        col1, col2 = st.columns([1.2, 1.8], gap="large")
        with col1:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='saas-card-header'><span>Current Plan</span></div>", unsafe_allow_html=True)
            if context.get("subscription"):
                sub = context["subscription"]
                st.write(f"### {sub['plan']}")
                st.write(f"**₹{sub['amount']} {sub['currency']} / month**")
                st.write(f"**Status:** {sub['status']}")
                st.write(f"**Subscription ID:** `{sub['external_subscription_id']}`")
                st.write(f"**Next Renewal:** {sub['next_billing_date']}")
            else:
                st.info("No active subscription recorded.")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='saas-card-header'><span>Initiate Cashfree Sandbox Subscription</span></div>", unsafe_allow_html=True)
            st.write("Subscribe or change plan using the real Cashfree Sandbox gateway:")

            with st.form("sub_sandbox_form"):
                selected_plan = st.selectbox("Select Plan", ["Basic Monthly (₹199)", "Pro Monthly (₹499)", "Enterprise Annual (₹4999)"])
                sub_submit = st.form_submit_button("Initiate Sandbox Subscription Session →", type="primary")

                if sub_submit:
                    plan_name = selected_plan.split(" (")[0]
                    amount_val = 199.0 if "199" in selected_plan else (4999.0 if "4999" in selected_plan else 499.0)
                    try:
                        res = create_customer_subscription(
                            customer_id=context["customer_id"],
                            plan_name=plan_name,
                            amount=amount_val,
                        )
                        st.success(f"Subscription order initialized in Cashfree Sandbox! Ref: `{res['external_subscription_id']}` (Status: {res['status']})")
                        if res.get("subscription_url"):
                            st.markdown(f"[Open Cashfree Sandbox Authorization URL →]({res['subscription_url']})")
                        st.info("Note: Subscription remains INITIALIZED until provider authorization confirms it.")
                    except Exception as e:
                        st.error(f"Subscription initiation failed: {str(e)}")
            st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # VIEW 3: PAYMENTS
    # =========================================================================
    elif st.session_state.customer_nav == "payments":
        st.markdown("### 💰 Payment & Transaction History")
        st.markdown("Verified billing records from Cashfree Gateway Sandbox and PostgreSQL.")

        # Payment history table rendered with native Streamlit DataFrame
        if context.get("payments"):
            df_pay = pd.DataFrame(context["payments"])
            display_cols = ["payment_id", "order_id", "amount", "currency", "status", "payment_method", "date"]
            available_cols = [c for c in display_cols if c in df_pay.columns]
            st.dataframe(df_pay[available_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No payment records found for this customer account.")

        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
        st.markdown("<div class='saas-card-header'><span>Create Sandbox Payment Order</span></div>", unsafe_allow_html=True)
        st.write("Generate a real Cashfree Sandbox payment order session:")

        with st.form("new_payment_session_form"):
            p_amount = st.number_input("Payment Amount (INR)", min_value=1.0, value=499.0, step=10.0)
            p_submit = st.form_submit_button("Generate Cashfree Sandbox Order Link →", type="primary")

            if p_submit:
                try:
                    order_res = create_customer_payment_order(
                        customer_id=context["customer_id"],
                        amount=float(p_amount),
                    )
                    st.success(f"Payment order generated! Order ID: `{order_res['order_id']}` (Status: {order_res['status']})")
                    if order_res.get("payment_link"):
                        st.markdown(f"[Proceed to Cashfree Sandbox Checkout / QR Stage →]({order_res['payment_link']})")
                    st.info("Provider state remains INITIALIZED/PENDING until real transaction completes.")
                except Exception as e:
                    st.error(f"Payment order initialization error: {str(e)}")
        st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # VIEW 4: TICKETS
    # =========================================================================
    elif st.session_state.customer_nav == "tickets":
        st.markdown("### 🎫 My Support Tickets")
        st.markdown("Track and manage your inquiries and escalation requests.")

        c_list, c_new = st.columns([1.8, 1.2], gap="large")

        with c_list:
            if context.get("tickets"):
                for t in context["tickets"]:
                    st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
                    st.write(f"**{t['ticket_number']}: {t['title']}**")
                    st.caption(f"Status: {t['status'].upper()} | Priority: {t['priority'].upper()} | Created: {t['date']}")
                    st.write(t["description"])
                    if t.get("resolution"):
                        st.info(f"Resolution: {t['resolution']}")
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("You have no active support tickets.")

        with c_new:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='saas-card-header'><span>Submit New Ticket</span></div>", unsafe_allow_html=True)
            with st.form("new_ticket_form"):
                t_title = st.text_input("Issue Summary", placeholder="e.g. Package damaged in transit")
                t_desc = st.text_area("Detailed Description", placeholder="Describe the issue in detail...")
                t_priority = st.selectbox("Priority Level", ["normal", "low", "high", "urgent"])
                t_submit = st.form_submit_button("Submit Ticket →", type="primary", use_container_width=True)

                if t_submit:
                    if not t_title or not t_desc:
                        st.error("Please enter both summary and description.")
                    else:
                        new_t = create_customer_ticket(
                            customer_id=context["customer_id"],
                            title=t_title,
                            description=t_desc,
                            priority=t_priority,
                        )
                        st.success(f"Ticket {new_t.ticket_number} created successfully!")
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # VIEW 5: ACCOUNT PROFILE
    # =========================================================================
    elif st.session_state.customer_nav == "account":
        st.markdown("### 👤 Account Profile")
        st.markdown("<div class='saas-card' style='max-width: 600px;'>", unsafe_allow_html=True)
        st.write(f"### {context['name']}")
        st.write(f"**Customer Database ID:** `{context['customer_id']}`")
        st.write(f"**External Customer ID:** `{context['external_customer_id'] or 'N/A'}`")
        st.write(f"**Email Address:** {context['email']}")
        st.write(f"**Phone:** {context['phone']}")
        st.write(f"**Account Status:** {context['status']}")
        st.markdown("</div>", unsafe_allow_html=True)
