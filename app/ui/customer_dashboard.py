"""
Customer AI Resolution Workspace for ResolveAI.
AI-First customer support interface: Central AI Copilot, contextual intelligence cards,
real-time Cashfree transaction tracking, and ticket management.
Adheres strictly to Pure Real Data and zero-fake-records principles.
"""

import uuid
import datetime
import streamlit as st
import pandas as pd
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.graph.workflow import app_graph
from app.services.customer_context import get_customer_context, create_customer_ticket
from app.services.payment_service import create_customer_payment_order
from app.services.subscription_service import create_customer_subscription


def render_customer_dashboard():
    """
    Render modern AI-First Customer Resolution Workspace.
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
        st.session_state.customer_nav = "copilot"

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"cust_{context['customer_id']}_{str(uuid.uuid4())[:8]}"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "pending_action" not in st.session_state:
        st.session_state.pending_action = None

    # =========================================================================
    # TOPBAR: BRANDING, STATUS, CONTEXTUAL NAVIGATION & USER
    # =========================================================================
    st.markdown(f"""
    <div class="ai-topbar">
        <div class="ai-brand-group">
            <div class="ai-brand-logo">⚡</div>
            <div>
                <div class="ai-brand-text">RESOLVE<span style="color: #4f46e5;">AI</span></div>
                <div style="font-size: 11px; color: #64748b; margin-top: -2px;">Customer Copilot</div>
            </div>
            <span class="badge-purple">ID: {context['external_customer_id'] or f"CUST-{context['customer_id']}"}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="text-align: right; margin-right: 8px;">
                <div style="font-size: 13.5px; font-weight: 700; color: #0f172a;">{context['name']}</div>
                <div style="font-size: 11px; color: #64748b;">{context['email']}</div>
            </div>
            <span class="live-dot" title="Copilot Online"></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top Navigation Switcher
    col_nav, col_out = st.columns([5, 1])
    with col_nav:
        n1, n2, n3, n4 = st.columns(4)
        with n1:
            if st.button("🤖 AI Resolution Copilot", type="primary" if st.session_state.customer_nav == "copilot" else "secondary", use_container_width=True, key="tnav_copilot"):
                st.session_state.customer_nav = "copilot"
                st.rerun()
        with n2:
            if st.button("💳 Billing & Subscriptions", type="primary" if st.session_state.customer_nav == "billing" else "secondary", use_container_width=True, key="tnav_billing"):
                st.session_state.customer_nav = "billing"
                st.rerun()
        with n3:
            ticket_badge = f" ({len(context.get('tickets', []))})" if context.get('tickets') else ""
            if st.button(f"🎫 Support Tickets{ticket_badge}", type="primary" if st.session_state.customer_nav == "tickets" else "secondary", use_container_width=True, key="tnav_tickets"):
                st.session_state.customer_nav = "tickets"
                st.rerun()
        with n4:
            if st.button("👤 Account Profile", type="primary" if st.session_state.customer_nav == "profile" else "secondary", use_container_width=True, key="tnav_profile"):
                st.session_state.customer_nav = "profile"
                st.rerun()

    with col_out:
        if st.button("🚪 Sign Out", use_container_width=True, key="c_logout"):
            st.session_state.authenticated_user_id = None
            st.session_state.authenticated_role = None
            st.session_state.portal_selection = None
            st.session_state.messages = []
            st.rerun()

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # VIEW 1: AI RESOLUTION COPILOT (HERO WORKSPACE)
    # =========================================================================
    if st.session_state.customer_nav == "copilot":
        # Hero Greeting Banner
        st.markdown(f"""
        <div class="ai-hero-banner">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <h2 style="font-size: 26px; font-weight: 800; color: #0f172a; margin-bottom: 6px; letter-spacing: -0.6px;">
                        How can ResolveAI help you today, {context['name'].split()[0]}?
                    </h2>
                    <p style="font-size: 14px; color: #64748b; margin: 0;">
                        AI Copilot is connected to your verified Cashfree transactions, active subscriptions, and company policy RAG.
                    </p>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="badge-green">● Investigation Active</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Suggested Resolution Action Chips
        st.markdown("<div style='font-size: 11px; font-weight: 700; color: #94a3b8; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;'>Quick Suggested Inquiries:</div>", unsafe_allow_html=True)
        q1, q2, q3, q4 = st.columns(4)
        with q1:
            if st.button("🔍 Investigate Recent Payment", use_container_width=True, key="chip_pay"):
                pay_id = context['payments'][0]['payment_id'] if context.get('payments') else "my latest transaction"
                st.session_state.quick_query = f"Can you investigate my payment {pay_id} and check its status in Cashfree?"
        with q2:
            if st.button("💳 Check Subscription Status", use_container_width=True, key="chip_sub"):
                sub_id = context['subscription']['external_subscription_id'] if context.get('subscription') else "my subscription"
                st.session_state.quick_query = f"What is the status of my subscription {sub_id}?"
        with q3:
            if st.button("🔄 Review Refund Policy", use_container_width=True, key="chip_ref"):
                st.session_state.quick_query = "What is the policy for requesting a refund on a charged order?"
        with q4:
            if st.button("🎫 Escalate / Open Ticket", use_container_width=True, key="chip_tkt"):
                st.session_state.quick_query = f"Please open a priority support ticket for customer {context['customer_id']} regarding service issues."

        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

        # Main 2-Column Split: AI Chat Canvas (Left) + Context Intelligence (Right)
        col_chat, col_intel = st.columns([1.8, 1.2], gap="large")

        # Left Column: AI Support Copilot Chat Stream
        with col_chat:
            st.markdown("<div class='chat-container-card'>", unsafe_allow_html=True)
            st.markdown("""
            <div style="display: flex; align-items: center; justify-content: space-between; padding-bottom: 12px; margin-bottom: 16px; border-bottom: 1px solid #f1f5f9;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">💬</span>
                    <span style="font-size: 14px; font-weight: 700; color: #0f172a;">AI Support Conversation</span>
                </div>
                <span class="badge-purple">LangGraph StateGraph</span>
            </div>
            """, unsafe_allow_html=True)

            # Initial Greeting if Empty
            if not st.session_state.messages:
                st.markdown(f"""
                <div style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 16px;">
                    <div style="width: 32px; height: 32px; background: #4f46e5; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-size: 16px; flex-shrink: 0; margin-top: 2px;">⚡</div>
                    <div>
                        <div style="font-size: 12px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">Resolve Copilot</div>
                        <div class="copilot-bubble">
                            Hello <b>{context['name']}</b>! I am your AI Support Copilot. I can investigate your Cashfree transactions, check your subscription renewal, search company policies, or open support tickets. How can I assist you?
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Render Message Stream
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
            user_input = st.chat_input("Ask ResolveAI anything about your account, payment, or policy...")

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

            st.markdown("</div>", unsafe_allow_html=True)

        # Right Column: Context Intelligence Cards
        with col_intel:
            # 1. Payment Intelligence Card
            st.markdown("""
            <div class="intelligence-card">
                <div class="intelligence-card-header">
                    <div class="intelligence-card-title">💰 Payment Intelligence</div>
                    <span class="badge-blue">Cashfree PG</span>
                </div>
            """, unsafe_allow_html=True)

            if context.get("payments"):
                p = context["payments"][0]
                status_badge = "badge-green" if p["status"] == "SUCCESS" else ("badge-orange" if p["status"] in ["PENDING", "INITIALIZED"] else "badge-gray")
                st.markdown(f"""
                <div style="display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 10px;">
                    <div style="font-size: 22px; font-weight: 800; color: #0f172a;">₹{p['amount']} <span style="font-size: 13px; color: #64748b; font-weight: 500;">{p['currency']}</span></div>
                    <span class="{status_badge}">{p['status']}</span>
                </div>
                <div style="font-size: 12px; color: #64748b; line-height: 1.6;">
                    <div><b>Order Ref:</b> <code>{p['order_id']}</code></div>
                    <div><b>Payment ID:</b> <code>{p['payment_id']}</code></div>
                    <div><b>Method:</b> {p['payment_method']}</div>
                    <div><b>Timestamp:</b> {p['date']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="smart-empty-state" style="padding: 20px 12px;">
                    <div class="smart-empty-icon" style="width: 36px; height: 36px; font-size: 16px;">✓</div>
                    <div class="smart-empty-title" style="font-size: 13px;">No Payment Records</div>
                    <div class="smart-empty-subtitle" style="font-size: 12px;">No active charges or transactions found.</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # 2. Subscription Intelligence Card
            st.markdown("""
            <div class="intelligence-card">
                <div class="intelligence-card-header">
                    <div class="intelligence-card-title">💳 Subscription Intelligence</div>
                    <span class="badge-purple">Plan Status</span>
                </div>
            """, unsafe_allow_html=True)

            if context.get("subscription"):
                sub = context["subscription"]
                sub_badge = "badge-green" if sub["status"] == "ACTIVE" else "badge-orange"
                st.markdown(f"""
                <div style="display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 8px;">
                    <div style="font-size: 18px; font-weight: 800; color: #0f172a;">{sub['plan']}</div>
                    <span class="{sub_badge}">{sub['status']}</span>
                </div>
                <div style="font-size: 12px; color: #64748b; line-height: 1.6;">
                    <div><b>Amount:</b> ₹{sub['amount']} {sub['currency']} / month</div>
                    <div><b>Renewal:</b> {sub['next_billing_date']}</div>
                    <div><b>Ref ID:</b> <code>{sub['external_subscription_id']}</code></div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="smart-empty-state" style="padding: 20px 12px;">
                    <div class="smart-empty-icon" style="width: 36px; height: 36px; font-size: 16px;">💳</div>
                    <div class="smart-empty-title" style="font-size: 13px;">No Active Subscription</div>
                    <div class="smart-empty-subtitle" style="font-size: 12px;">Subscribe to an enterprise plan under the Billing tab.</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # 3. Open Issues / Tickets Intelligence
            st.markdown("""
            <div class="intelligence-card">
                <div class="intelligence-card-header">
                    <div class="intelligence-card-title">🎫 Active Resolution Tickets</div>
                </div>
            """, unsafe_allow_html=True)

            open_tks = [t for t in context.get("tickets", []) if t["status"] in ["open", "in_progress"]]
            if open_tks:
                for t in open_tks[:2]:
                    st.markdown(f"""
                    <div style="padding: 10px 0; border-bottom: 1px solid #f1f5f9;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13px; font-weight: 700; color: #0f172a;">{t['ticket_number']}: {t['title'][:28]}...</span>
                            <span class="badge-orange">{t['status'].upper()}</span>
                        </div>
                        <div style="font-size: 11.5px; color: #64748b; margin-top: 2px;">Priority: {t['priority'].upper()} | {t['date']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="smart-empty-state" style="padding: 16px 12px;">
                    <div class="smart-empty-icon" style="width: 32px; height: 32px; font-size: 14px;">✓</div>
                    <div class="smart-empty-title" style="font-size: 12.5px;">All Inquiries Clear</div>
                    <div class="smart-empty-subtitle" style="font-size: 11.5px;">No active support tickets pending resolution.</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # VIEW 2: BILLING & SUBSCRIPTIONS
    # =========================================================================
    elif st.session_state.customer_nav == "billing":
        st.markdown("""
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-bottom: 4px;">💳 Billing & Sandbox Payment Portal</h2>
            <div style="font-size: 13.5px; color: #64748b;">Manage recurring subscriptions, generate real Cashfree Sandbox payment sessions, and view transaction history.</div>
        </div>
        """, unsafe_allow_html=True)

        col_b1, col_b2 = st.columns([1.2, 1.8], gap="large")

        with col_b1:
            st.markdown("<div class='intelligence-card'>", unsafe_allow_html=True)
            st.markdown("<div class='intelligence-card-header'><span class='intelligence-card-title'>Active Subscription Plan</span></div>", unsafe_allow_html=True)
            if context.get("subscription"):
                sub = context["subscription"]
                st.write(f"### {sub['plan']}")
                st.write(f"**₹{sub['amount']} {sub['currency']} / month**")
                st.write(f"**Status:** {sub['status']}")
                st.write(f"**Subscription ID:** `{sub['external_subscription_id']}`")
                st.write(f"**Next Billing Date:** {sub['next_billing_date']}")
            else:
                st.markdown("""
                <div class="smart-empty-state">
                    <div class="smart-empty-icon">💳</div>
                    <div class="smart-empty-title">No Active Subscription</div>
                    <div class="smart-empty-subtitle">Select a plan below to initialize recurring subscription billing via Cashfree.</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_b2:
            st.markdown("<div class='intelligence-card'>", unsafe_allow_html=True)
            st.markdown("<div class='intelligence-card-header'><span class='intelligence-card-title'>Initiate Cashfree Sandbox Subscription</span></div>", unsafe_allow_html=True)
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

        # Payment Transaction History
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='intelligence-card'>", unsafe_allow_html=True)
        st.markdown("<div class='intelligence-card-header'><span class='intelligence-card-title'>Verified Payment Transactions</span></div>", unsafe_allow_html=True)

        if context.get("payments"):
            df_pay = pd.DataFrame(context["payments"])
            display_cols = ["payment_id", "order_id", "amount", "currency", "status", "payment_method", "date"]
            available_cols = [c for c in display_cols if c in df_pay.columns]
            st.dataframe(df_pay[available_cols], use_container_width=True, hide_index=True)
        else:
            st.markdown("""
            <div class="smart-empty-state">
                <div class="smart-empty-icon">✓</div>
                <div class="smart-empty-title">No Payment History</div>
                <div class="smart-empty-subtitle">Zero payment records exist for this customer account.</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Generate One-Time Order
        st.markdown("<div class='intelligence-card'>", unsafe_allow_html=True)
        st.markdown("<div class='intelligence-card-header'><span class='intelligence-card-title'>Generate Real Cashfree Sandbox Payment Order</span></div>", unsafe_allow_html=True)
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
    # VIEW 3: SUPPORT TICKETS
    # =========================================================================
    elif st.session_state.customer_nav == "tickets":
        st.markdown("""
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-bottom: 4px;">🎫 Support & Escalation Tickets</h2>
            <div style="font-size: 13.5px; color: #64748b;">Track open support inquiries and submit formal escalation requests to the support team.</div>
        </div>
        """, unsafe_allow_html=True)

        c_list, c_new = st.columns([1.8, 1.2], gap="large")

        with c_list:
            if context.get("tickets"):
                for t in context["tickets"]:
                    st.markdown("<div class='intelligence-card'>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <h4 style="font-size: 16px; font-weight: 700; color: #0f172a; margin: 0;">{t['ticket_number']}: {t['title']}</h4>
                        <span class="badge-blue">{t['status'].upper()}</span>
                    </div>
                    <div style="font-size: 12px; color: #64748b; margin: 4px 0 10px 0;">Priority: <b>{t['priority'].upper()}</b> | Created: {t['date']}</div>
                    <p style="font-size: 13.5px; color: #334155; line-height: 1.5; margin-bottom: 8px;">{t['description']}</p>
                    """, unsafe_allow_html=True)
                    if t.get("resolution"):
                        st.info(f"Resolution Note: {t['resolution']}")
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="smart-empty-state">
                    <div class="smart-empty-icon">✓</div>
                    <div class="smart-empty-title">No Active Tickets</div>
                    <div class="smart-empty-subtitle">You have no open support tickets. Submit a request using the form on the right if needed.</div>
                </div>
                """, unsafe_allow_html=True)

        with c_new:
            st.markdown("<div class='intelligence-card'>", unsafe_allow_html=True)
            st.markdown("<div class='intelligence-card-header'><span class='intelligence-card-title'>Submit New Support Ticket</span></div>", unsafe_allow_html=True)
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
    # VIEW 4: PROFILE
    # =========================================================================
    elif st.session_state.customer_nav == "profile":
        st.markdown("""
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-bottom: 4px;">👤 Customer Identity & Account Intelligence</h2>
            <div style="font-size: 13.5px; color: #64748b;">Verified customer details stored securely in PostgreSQL.</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='intelligence-card' style='max-width: 650px;'>", unsafe_allow_html=True)
        st.write(f"### {context['name']}")
        st.write(f"**Customer Database ID:** `{context['customer_id']}`")
        st.write(f"**External Customer ID:** `{context['external_customer_id'] or 'N/A'}`")
        st.write(f"**Email Address:** {context['email']}")
        st.write(f"**Phone Number:** {context['phone']}")
        st.write(f"**Account Status:** {context['status']}")
        st.write(f"**Company ID:** `{context['company_id']}`")
        st.markdown("</div>", unsafe_allow_html=True)

