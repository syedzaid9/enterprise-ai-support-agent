"""
Admin Dashboard for ResolveAI.
Provides company-scoped metrics, customer directory, ticket management,
Human-in-the-Loop approvals execution, knowledge base uploader, integrations health, and audit logs.
"""

import json
import datetime
import streamlit as st
import pandas as pd
from app.db.database import get_db
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
    AgentRun,
)
from app.services.ticket_service import update_ticket_status
from app.services.knowledge_service import save_and_index_document, delete_knowledge_document, list_knowledge_documents
from app.services.audit_service import list_audit_logs, log_audit_event
from app.services.payment_service import create_refund
from app.services.subscription_service import cancel_customer_subscription
from app.config import get_integration_health


def render_admin_dashboard():
    """
    Render authenticated Admin operations portal.
    """
    user_id = st.session_state.get("authenticated_user_id")

    with get_db() as db:
        admin_user = db.query(User).filter(User.id == user_id).first()
        if not admin_user or admin_user.role != "admin":
            st.error("Unauthorized access. Admin privileges required.")
            if st.button("Return to Login"):
                st.session_state.authenticated_user_id = None
                st.session_state.authenticated_role = None
                st.rerun()
            return

        company_id = admin_user.company_id
        company = db.query(Company).filter(Company.id == company_id).first()
        company_name = company.name if company else "ResolveAI Enterprise"

        # Calculate actual metrics from PostgreSQL
        total_customers = db.query(Customer).filter(Customer.company_id == company_id).count()
        open_tickets = db.query(Ticket).filter(Ticket.company_id == company_id, Ticket.status.in_(["open", "in_progress"])).count()
        pending_approvals_count = db.query(Approval).filter(Approval.company_id == company_id, Approval.status == "pending").count()
        active_subscriptions = db.query(Subscription).filter(Subscription.company_id == company_id, Subscription.status == "ACTIVE").count()

        customers = db.query(Customer).filter(Customer.company_id == company_id).order_by(Customer.created_at.desc()).all()
        tickets = db.query(Ticket).filter(Ticket.company_id == company_id).order_by(Ticket.created_at.desc()).all()
        approvals = db.query(Approval).filter(Approval.company_id == company_id).order_by(Approval.created_at.desc()).all()
        agent_runs = db.query(AgentRun).filter(AgentRun.company_id == company_id).order_by(AgentRun.started_at.desc()).limit(25).all()

    # Session state setup
    if "admin_nav" not in st.session_state:
        st.session_state.admin_nav = "overview"

    # =========================================================================
    # SIDEBAR: ADMIN BRAND & NAVIGATION
    # =========================================================================
    with st.sidebar:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
            <div style="width: 44px; height: 44px; background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; font-size: 22px; font-weight: 800; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3);">🛡️</div>
            <div>
                <div class="brand-title">ResolveAI</div>
                <div class="brand-sub">Admin Console</div>
            </div>
        </div>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; margin-bottom: 20px;">
            <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase;">Company Scope</div>
            <div style="font-size: 14px; font-weight: 800; color: #0f172a; margin-top: 2px;">{company_name}</div>
            <div style="font-size: 12px; color: #64748b;">{admin_user.email}</div>
            <div style="margin-top: 8px;">
                <span class="badge-blue">🛡️ SUPERVISOR ADMIN</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='font-size: 11.5px; font-weight: 700; color: #94a3b8; margin-bottom: 8px; text-transform: uppercase;'>Operations</div>", unsafe_allow_html=True)

        admin_nav_items = {
            "overview": ("📊 Overview & Metrics", "primary" if st.session_state.admin_nav == "overview" else "secondary"),
            "customers": ("👥 Customer Directory", "primary" if st.session_state.admin_nav == "customers" else "secondary"),
            "tickets": ("🎫 Ticket Queue", "primary" if st.session_state.admin_nav == "tickets" else "secondary"),
            "approvals": (f"⚠️ Pending Approvals ({pending_approvals_count})", "primary" if st.session_state.admin_nav == "approvals" else "secondary"),
            "knowledge": ("📚 Knowledge Base", "primary" if st.session_state.admin_nav == "knowledge" else "secondary"),
            "integrations": ("🔌 Integrations & Health", "primary" if st.session_state.admin_nav == "integrations" else "secondary"),
            "audit": ("📜 Audit Logs", "primary" if st.session_state.admin_nav == "audit" else "secondary"),
        }

        for nav_k, (nav_lbl, btn_t) in admin_nav_items.items():
            if st.button(nav_lbl, type=btn_t, use_container_width=True, key=f"admin_nav_{nav_k}"):
                st.session_state.admin_nav = nav_k
                st.rerun()

        st.markdown("<hr style='margin: 20px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

        if st.button("🚪 Log Out", use_container_width=True, key="admin_logout"):
            st.session_state.authenticated_user_id = None
            st.session_state.authenticated_role = None
            st.session_state.portal_selection = None
            st.rerun()

    # =========================================================================
    # VIEW 1: OVERVIEW & METRICS
    # =========================================================================
    if st.session_state.admin_nav == "overview":
        st.markdown(f"### 📊 Supervisor Operations: {company_name}")
        st.markdown("Real-time telemetry and resolution pipeline metrics from PostgreSQL.")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric(label="Total Customers", value=str(total_customers))
        with c2:
            st.metric(label="Open Support Tickets", value=str(open_tickets))
        with c3:
            st.metric(label="Pending HITL Approvals", value=str(pending_approvals_count))
        with c4:
            st.metric(label="Active Subscriptions", value=str(active_subscriptions))

        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

        col_left, col_right = st.columns([1.5, 1.5], gap="large")

        with col_left:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='saas-card-header'><span>⚠️ Pending Approval Queue</span></div>", unsafe_allow_html=True)
            pending_list = [a for a in approvals if a.status == "pending"]
            if pending_list:
                for a in pending_list:
                    st.write(f"**Action:** `{a.action_type}` on target `{a.target_id or 'N/A'}`")
                    st.write(f"**Customer ID:** {a.customer_id}")
                    st.write(f"**Reason:** {a.reason}")
                    st.caption(f"Requested: {a.created_at.strftime('%d %b %Y, %I:%M %p') if a.created_at else 'N/A'}")
                    st.markdown("---")
            else:
                st.info("No pending supervisor approvals.")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_right:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='saas-card-header'><span>🎫 Recent Tickets</span></div>", unsafe_allow_html=True)
            if tickets:
                for t in tickets[:4]:
                    st.write(f"**{t.ticket_number}: {t.title}**")
                    st.caption(f"Status: {t.status.upper()} | Priority: {t.priority.upper()}")
            else:
                st.info("No support tickets recorded.")
            st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # VIEW 2: CUSTOMERS
    # =========================================================================
    elif st.session_state.admin_nav == "customers":
        st.markdown("### 👥 Customer Directory")
        st.markdown(f"Verified customer accounts registered under **{company_name}**.")

        if customers:
            cust_data = []
            for c in customers:
                cust_data.append({
                    "DB ID": c.id,
                    "External ID": c.external_customer_id or "N/A",
                    "Full Name": c.name,
                    "Email Address": c.email,
                    "Phone": c.phone or "N/A",
                    "Status": c.status,
                    "Created": c.created_at.strftime("%d %b %Y") if c.created_at else "N/A",
                })
            df_cust = pd.DataFrame(cust_data)
            st.dataframe(df_cust, use_container_width=True, hide_index=True)
        else:
            st.info("No customer accounts found for this company.")

    # =========================================================================
    # VIEW 3: TICKETS
    # =========================================================================
    elif st.session_state.admin_nav == "tickets":
        st.markdown("### 🎫 Support Ticket Queue")
        st.markdown("Manage escalated support tickets and update resolution notes.")

        status_filter = st.selectbox("Filter Status", ["All", "open", "in_progress", "resolved", "closed"])

        filtered_tickets = tickets
        if status_filter != "All":
            filtered_tickets = [t for t in tickets if t.status == status_filter]

        if filtered_tickets:
            for t in filtered_tickets:
                with st.expander(f"{t.ticket_number}: {t.title} ({t.status.upper()})"):
                    st.write(f"**Description:** {t.description}")
                    st.write(f"**Priority:** {t.priority.upper()} | **Customer ID:** {t.customer_id}")
                    if t.resolution:
                        st.write(f"**Resolution:** {t.resolution}")

                    c_st, c_res, c_btn = st.columns([1, 2, 1])
                    with c_st:
                        new_st = st.selectbox("New Status", ["open", "in_progress", "resolved", "closed"], index=["open", "in_progress", "resolved", "closed"].index(t.status), key=f"tst_{t.id}")
                    with c_res:
                        new_res = st.text_input("Resolution Note", value=t.resolution or "", key=f"tres_{t.id}")
                    with c_btn:
                        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                        if st.button("Update Ticket", key=f"tbtn_{t.id}"):
                            update_ticket_status(ticket_id=t.id, status=new_st, resolution=new_res, admin_user_id=admin_user.id, company_id=company_id)
                            st.success(f"Ticket {t.ticket_number} updated!")
                            st.rerun()
        else:
            st.info("No tickets match the selected criteria.")

    # =========================================================================
    # VIEW 4: PENDING APPROVALS
    # =========================================================================
    elif st.session_state.admin_nav == "approvals":
        st.markdown("### ⚠️ Human-in-the-Loop Approvals")
        st.markdown("Authorize or reject sensitive AI financial operations and cancellations.")

        pending_items = [a for a in approvals if a.status == "pending"]

        if pending_items:
            for a in pending_items:
                st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
                st.write(f"### Proposed Action: `{a.action_type}`")
                st.write(f"**Target Reference:** `{a.target_id or 'N/A'}` | **Customer ID:** {a.customer_id}")
                st.write(f"**AI Reasoning:** {a.reason or 'N/A'}")
                st.code(a.action_data, language="json")

                col_ap, col_rej = st.columns(2)
                with col_ap:
                    app_notes = st.text_input("Approval Notes", value="Approved under standard 30-day guarantee", key=f"anotes_{a.id}")
                    if st.button("✅ Authorize & Execute Action", type="primary", key=f"btn_app_{a.id}"):
                        # Execute the approved action
                        try:
                            payload = json.loads(a.action_data) if a.action_data else {}
                            if a.action_type == "refund_payment":
                                create_refund(
                                    payment_id=payload.get("payment_id") or a.target_id,
                                    amount=payload.get("amount"),
                                    reason=app_notes,
                                    admin_user_id=admin_user.id,
                                )
                            elif a.action_type == "cancel_subscription":
                                cancel_customer_subscription(
                                    subscription_id=payload.get("subscription_id") or a.target_id,
                                    admin_user_id=admin_user.id,
                                )

                            with get_db() as db:
                                app_rec = db.query(Approval).filter(Approval.id == a.id).first()
                                if app_rec:
                                    app_rec.status = "approved"
                                    app_rec.approved_by = admin_user.id
                                    app_rec.notes = app_notes
                                    app_rec.resolved_at = datetime.datetime.now(datetime.timezone.utc)
                                    db.flush()

                            st.success(f"Action '{a.action_type}' authorized and executed successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Execution error: {str(e)}")

                with col_rej:
                    rej_reason = st.text_input("Rejection Reason", value="Exceeds eligible policy refund window", key=f"rnotes_{a.id}")
                    if st.button("❌ Deny Action", key=f"btn_rej_{a.id}"):
                        with get_db() as db:
                            app_rec = db.query(Approval).filter(Approval.id == a.id).first()
                            if app_rec:
                                app_rec.status = "rejected"
                                app_rec.approved_by = admin_user.id
                                app_rec.notes = rej_reason
                                app_rec.resolved_at = datetime.datetime.now(datetime.timezone.utc)
                                db.flush()

                        log_audit_event(
                            company_id=company_id,
                            user_id=admin_user.id,
                            customer_id=a.customer_id,
                            actor_type="admin",
                            action="APPROVAL_DENIED",
                            target_type="approval",
                            target_id=str(a.id),
                            details=f"Supervisor rejected action '{a.action_type}'. Reason: {rej_reason}",
                            status="DENIED",
                        )
                        st.warning(f"Action '{a.action_type}' was denied.")
                        st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No pending supervisor approvals. All resolution requests are clear.")

    # =========================================================================
    # VIEW 5: KNOWLEDGE BASE
    # =========================================================================
    elif st.session_state.admin_nav == "knowledge":
        st.markdown("### 📚 Knowledge Base & Policy Management")
        st.markdown("Upload company policy documents to index into the tenant-isolated RAG vector store.")

        c_up, c_list = st.columns([1.2, 1.8], gap="large")

        with c_up:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='saas-card-header'><span>Upload Policy Document</span></div>", unsafe_allow_html=True)

            uploaded_file = st.file_uploader("Upload Policy Document (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"])
            doc_type_val = st.selectbox("Document Category", ["policy", "faq", "terms", "shipping", "warranty"])

            if uploaded_file is not None:
                doc_bytes = uploaded_file.read()
                doc_filename = uploaded_file.name

                if st.button("Index Document into RAG Vector Store →", type="primary"):
                    try:
                        res = save_and_index_document(
                            company_id=company_id,
                            filename=doc_filename,
                            content=doc_bytes,
                            uploaded_by_user_id=admin_user.id,
                            doc_type=doc_type_val,
                        )
                        st.success(f"Document '{doc_filename}' successfully indexed into {res['chunk_count']} vector chunks!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to index document: {str(e)}")
            st.markdown("</div>", unsafe_allow_html=True)

        with c_list:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("<div class='saas-card-header'><span>Indexed Company Documents</span></div>", unsafe_allow_html=True)
            docs = list_knowledge_documents(company_id=company_id)

            if docs:
                for d in docs:
                    c_info, c_del = st.columns([3, 1])
                    with c_info:
                        st.write(f"**{d['filename']}** ({d['doc_type']})")
                        st.caption(f"Chunks: {d['chunk_count']} | Status: {d['status']} | Uploaded: {d['created_at']}")
                    with c_del:
                        st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                        if st.button("🗑️ Delete", key=f"del_doc_{d['id']}"):
                            delete_knowledge_document(company_id=company_id, doc_id=d['id'], admin_user_id=admin_user.id)
                            st.success(f"Deleted {d['filename']}")
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("No company knowledge documents indexed yet.")
            st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # VIEW 6: INTEGRATIONS & HEALTH
    # =========================================================================
    elif st.session_state.admin_nav == "integrations":
        st.markdown("### 🔌 Integrations & Health Diagnostics")
        st.markdown("Live health status of external billing, database, and LLM services without exposing credentials.")

        health = get_integration_health()

        c_db, c_cf, c_hf = st.columns(3)
        with c_db:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.write("### 🗄️ Database")
            st.write(f"**Type:** {health['database']['type']}")
            st.write(f"**Status:** {health['database']['status']}")
            st.caption(f"Host: {health['database']['url_masked']}")
            st.markdown("</div>", unsafe_allow_html=True)

        with c_cf:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.write("### 💳 Cashfree Gateway")
            st.write(f"**Environment:** {health['cashfree']['environment'].upper()}")
            st.write(f"**Status:** {health['cashfree']['status']}")
            st.caption(f"Client ID: {health['cashfree']['client_id_masked']}")
            st.markdown("</div>", unsafe_allow_html=True)

        with c_hf:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.write("### 🧠 LLM / Hugging Face")
            st.write(f"**Model:** {health['huggingface']['model']}")
            st.write(f"**Status:** {health['huggingface']['status']}")
            st.caption(f"Token: {health['huggingface']['token_masked']}")
            st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # VIEW 7: AUDIT LOGS
    # =========================================================================
    elif st.session_state.admin_nav == "audit":
        st.markdown("### 📜 Immutable Audit Logs")
        st.markdown("Cryptographically timestamped compliance and activity logs from PostgreSQL.")

        logs = list_audit_logs(company_id=company_id, limit=50)

        if logs:
            df_logs = pd.DataFrame(logs)
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
        else:
            st.info("No audit logs recorded for this company.")
