"""
Admin AI Operations & Supervision Center for ResolveAI.
Modern AI Operations platform: Topbar navigation, live telemetry strip, Human-in-the-Loop supervision floor,
intelligent agent run timeline, customer directory, ticket queue, and policy knowledge vault.
Adheres strictly to Pure Real Data principles and zero-fake-records.
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
    Render modern Supervisor AI Operations Center.
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
        company_name = company.name if company else "ResolveAI Enterprise Corp"

        # Calculate actual metrics from PostgreSQL
        total_customers = db.query(Customer).filter(Customer.company_id == company_id).count()
        open_tickets = db.query(Ticket).filter(Ticket.company_id == company_id, Ticket.status.in_(["open", "in_progress"])).count()
        pending_approvals_count = db.query(Approval).filter(Approval.company_id == company_id, Approval.status == "pending").count()
        active_subscriptions = db.query(Subscription).filter(Subscription.company_id == company_id, Subscription.status == "ACTIVE").count()

        customers = db.query(Customer).filter(Customer.company_id == company_id).order_by(Customer.created_at.desc()).all()
        tickets = db.query(Ticket).filter(Ticket.company_id == company_id).order_by(Ticket.created_at.desc()).all()
        approvals = db.query(Approval).filter(Approval.company_id == company_id).order_by(Approval.created_at.desc()).all()
        agent_runs = db.query(AgentRun).filter(AgentRun.company_id == company_id).order_by(AgentRun.started_at.desc()).limit(30).all()

    # Session state setup
    if "admin_nav" not in st.session_state:
        st.session_state.admin_nav = "ops"

    # =========================================================================
    # TOPBAR: BRANDING, COMPANY SCOPE, TELEMETRY BADGE & USER PROFILE
    # =========================================================================
    st.markdown(f"""
    <div class="ai-topbar">
        <div class="ai-brand-group">
            <div class="ai-brand-logo" style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);">🛡️</div>
            <div>
                <div class="ai-brand-text">RESOLVE<span style="color: #2563eb;">AI</span></div>
                <div style="font-size: 11px; color: #64748b; margin-top: -2px;">AI Operations Center</div>
            </div>
            <span class="badge-blue">SCOPE: {company_name}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="text-align: right; margin-right: 4px;">
                <div style="font-size: 13.5px; font-weight: 700; color: #0f172a;">{admin_user.email}</div>
                <div style="font-size: 11px; color: #64748b;">Supervisor Admin</div>
            </div>
            <span class="live-dot" title="Workforce Telemetry Active"></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top Command Bar Navigation
    col_nav, col_out = st.columns([6.2, 1])
    with col_nav:
        n1, n2, n3, n4, n5, n6 = st.columns(6)
        with n1:
            if st.button("⚡ Operations Floor", type="primary" if st.session_state.admin_nav == "ops" else "secondary", use_container_width=True, key="an_ops"):
                st.session_state.admin_nav = "ops"
                st.rerun()
        with n2:
            app_label = f"⚠️ Approvals ({pending_approvals_count})" if pending_approvals_count > 0 else "✓ Approvals (0)"
            if st.button(app_label, type="primary" if st.session_state.admin_nav == "approvals" else "secondary", use_container_width=True, key="an_app"):
                st.session_state.admin_nav = "approvals"
                st.rerun()
        with n3:
            if st.button(f"🎫 Support Queue ({open_tickets})", type="primary" if st.session_state.admin_nav == "tickets" else "secondary", use_container_width=True, key="an_tkt"):
                st.session_state.admin_nav = "tickets"
                st.rerun()
        with n4:
            if st.button(f"👥 Customers ({total_customers})", type="primary" if st.session_state.admin_nav == "customers" else "secondary", use_container_width=True, key="an_cust"):
                st.session_state.admin_nav = "customers"
                st.rerun()
        with n5:
            if st.button("📚 Policy Vault", type="primary" if st.session_state.admin_nav == "knowledge" else "secondary", use_container_width=True, key="an_know"):
                st.session_state.admin_nav = "knowledge"
                st.rerun()
        with n6:
            if st.button("🔌 Health & Audit", type="primary" if st.session_state.admin_nav in ["health", "audit"] else "secondary", use_container_width=True, key="an_hlth"):
                st.session_state.admin_nav = "health"
                st.rerun()

    with col_out:
        if st.button("🚪 Sign Out", use_container_width=True, key="admin_logout"):
            st.session_state.authenticated_user_id = None
            st.session_state.authenticated_role = None
            st.session_state.portal_selection = None
            st.rerun()

    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # VIEW 1: AI OPERATIONS FLOOR (HERO WORKSPACE)
    # =========================================================================
    if st.session_state.admin_nav == "ops":
        # Hero Telemetry Strip
        st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <div style="font-size: 11.5px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                Live Resolution Pipeline Telemetry
            </div>
        </div>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""
            <div class="telemetry-chip">
                <div class="telemetry-label">Registered Customers</div>
                <div class="telemetry-value">{total_customers}</div>
                <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Verified tenant accounts</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="telemetry-chip">
                <div class="telemetry-label">Active Support Issues</div>
                <div class="telemetry-value">{open_tickets}</div>
                <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Open & in-progress tickets</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            app_color = "#ea580c" if pending_approvals_count > 0 else "#15803d"
            st.markdown(f"""
            <div class="telemetry-chip" style="{ 'border-color: #fed7aa; background: #fffaf5;' if pending_approvals_count > 0 else '' }">
                <div class="telemetry-label" style="color: {app_color};">Pending HITL Approvals</div>
                <div class="telemetry-value" style="color: {app_color};">{pending_approvals_count}</div>
                <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Supervisor authorization queue</div>
            </div>
            """, unsafe_allow_html=True)
        with m4:
            st.markdown(f"""
            <div class="telemetry-chip">
                <div class="telemetry-label">Active Subscriptions</div>
                <div class="telemetry-value">{active_subscriptions}</div>
                <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Cashfree recurring plans</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

        # Operational Grid: AI Resolution Activity (Left) + Human Supervision Floor (Right)
        col_timeline, col_hitl = st.columns([1.4, 1.6], gap="large")

        # Left Column: AI Resolution Activity Stream (Priority #1)
        with col_timeline:
            st.markdown("""
            <div class="intelligence-card">
                <div class="intelligence-card-header">
                    <div class="intelligence-card-title">🤖 AI Resolution Activity Stream</div>
                    <span class="badge-blue">Live Telemetry</span>
                </div>
            """, unsafe_allow_html=True)

            if agent_runs:
                st.markdown("<div class='timeline-container'>", unsafe_allow_html=True)
                for run in agent_runs[:8]:
                    dot_cls = "timeline-dot-success" if run.status == "completed" else ("timeline-dot-warning" if run.status == "pending" else "timeline-dot")
                    ts = run.started_at.strftime("%d %b, %I:%M %p") if run.started_at else "N/A"
                    st.markdown(f"""
                    <div class="timeline-node">
                        <div class="timeline-dot {dot_cls}"></div>
                        <div class="timeline-title">{run.intent or 'AI Customer Investigation Workflow'}</div>
                        <div class="timeline-meta">
                            Status: <b>{run.status.upper()}</b> | Customer ID: {run.customer_id} | Tools: {run.tools_invoked_count or 0} | {ts}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="smart-empty-state">
                    <div class="smart-empty-icon">🤖</div>
                    <div class="smart-empty-title">No Recent AI Workflows</div>
                    <div class="smart-empty-subtitle">AI resolution activity stream will populate as customers interact with the copilot.</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # Quick Policy Status Card
            docs = list_knowledge_documents(company_id)
            st.markdown(f"""
            <div class="intelligence-card">
                <div class="intelligence-card-header">
                    <div class="intelligence-card-title">📚 Company Policy RAG Status</div>
                    <span class="badge-purple">{len(docs)} Documents Indexed</span>
                </div>
                <div style="font-size: 13px; color: #64748b; line-height: 1.6;">
                    FAISS semantic vector store active with tenant company isolation. Policy guidelines are automatically retrieved during agent resolution runs.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Right Column: Human-in-the-Loop Supervision Queue (Priority #2)
        with col_hitl:
            st.markdown("""
            <div class="intelligence-card">
                <div class="intelligence-card-header">
                    <div class="intelligence-card-title">⚠️ Human Supervision & Authorization Floor</div>
                    <span class="badge-orange">HITL Governance</span>
                </div>
            """, unsafe_allow_html=True)

            pending_items = [a for a in approvals if a.status == "pending"]

            if pending_items:
                for a in pending_items:
                    st.markdown(f"""
                    <div style="background: #fffaf5; border: 1px solid #fed7aa; border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <span style="font-size: 14px; font-weight: 800; color: #9a3412;">PROPOSED ACTION: <code>{a.action_type}</code></span>
                            <span class="badge-orange">REQUIRES APPROVAL</span>
                        </div>
                        <div style="font-size: 12.5px; color: #475569; margin: 8px 0; line-height: 1.6;">
                            <div><b>Customer DB ID:</b> {a.customer_id} | <b>Target Ref:</b> <code>{a.target_id or 'N/A'}</code></div>
                            <div><b>AI Investigation Reason:</b> {a.reason or 'Sensitive state change intercepted by LangGraph workflow.'}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.code(a.action_data, language="json")

                    col_ap, col_rej = st.columns(2)
                    with col_ap:
                        app_notes = st.text_input("Authorization Note", value="Approved under enterprise terms", key=f"anotes_{a.id}")
                        if st.button("✅ Authorize & Execute Action", type="primary", key=f"btn_app_{a.id}", use_container_width=True):
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

                                # Mark approval approved
                                with get_db() as db_app:
                                    app_rec = db_app.query(Approval).filter(Approval.id == a.id).first()
                                    if app_rec:
                                        app_rec.status = "approved"
                                        app_rec.approved_by = admin_user.id
                                        app_rec.notes = app_notes
                                        app_rec.resolved_at = datetime.datetime.now(datetime.timezone.utc)
                                        db_app.flush()

                                st.success(f"Action '{a.action_type}' authorized and executed!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Execution error: {str(e)}")

                    with col_rej:
                        rej_notes = st.text_input("Rejection Reason", value="Request does not satisfy policy", key=f"rnotes_{a.id}")
                        if st.button("❌ Deny Action", key=f"btn_rej_{a.id}", use_container_width=True):
                            with get_db() as db_rej:
                                app_rec = db_rej.query(Approval).filter(Approval.id == a.id).first()
                                if app_rec:
                                    app_rec.status = "rejected"
                                    app_rec.rejected_by = admin_user.id
                                    app_rec.notes = rej_notes
                                    app_rec.resolved_at = datetime.datetime.now(datetime.timezone.utc)
                                    db_rej.flush()
                            st.warning(f"Action '{a.action_type}' rejected.")
                            st.rerun()
                    st.markdown("<hr style='margin: 16px 0; border: none; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="smart-empty-state">
                    <div class="smart-empty-icon">✓</div>
                    <div class="smart-empty-title">All Approvals Clear</div>
                    <div class="smart-empty-subtitle">Zero pending AI financial actions currently require supervisor authorization.</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # Support Queue Summary on Ops Floor (Priority #3)
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="intelligence-card">
            <div class="intelligence-card-header">
                <div class="intelligence-card-title">🎫 Urgent Support Issues Requiring Attention</div>
                <span class="badge-blue">Queue Overview</span>
            </div>
        """, unsafe_allow_html=True)

        open_tk_list = [t for t in tickets if t.status in ["open", "in_progress"]]
        if open_tk_list:
            for t in open_tk_list[:3]:
                st.markdown(f"""
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <span style="font-size: 14.5px; font-weight: 700; color: #0f172a;">{t.ticket_number}: {t.title}</span>
                        <span class="badge-orange">{t.status.upper()}</span>
                    </div>
                    <div style="font-size: 12px; color: #64748b; margin-top: 4px;">Priority: <b>{t.priority.upper()}</b> | Customer ID: {t.customer_id} | Created: {t.created_at.strftime('%d %b %Y') if t.created_at else 'N/A'}</div>
                    <div style="font-size: 13px; color: #334155; margin-top: 6px;">{t.description[:120]}...</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="smart-empty-state" style="padding: 24px;">
                <div class="smart-empty-icon">✓</div>
                <div class="smart-empty-title">Support Queue Clear</div>
                <div class="smart-empty-subtitle">No unresolved customer support tickets are currently pending.</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # VIEW 2: DEDICATED APPROVALS CONSOLE
    # =========================================================================
    elif st.session_state.admin_nav == "approvals":
        st.markdown("""
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-bottom: 4px;">⚠️ Human-in-the-Loop Supervision Console</h2>
            <div style="font-size: 13.5px; color: #64748b;">Review intercepted financial refunds, subscription cancellations, and sensitive agent actions.</div>
        </div>
        """, unsafe_allow_html=True)

        if approvals:
            for a in approvals:
                status_badge = "badge-orange" if a.status == "pending" else ("badge-green" if a.status == "approved" else "badge-gray")
                st.markdown("<div class='intelligence-card'>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <h4 style="font-size: 16px; font-weight: 800; color: #0f172a; margin: 0;">Action: <code>{a.action_type}</code></h4>
                    <span class="{status_badge}">{a.status.upper()}</span>
                </div>
                <div style="font-size: 12.5px; color: #64748b; margin: 6px 0 10px 0;">Customer ID: {a.customer_id} | Target: <code>{a.target_id or 'N/A'}</code> | Created: {a.created_at.strftime('%d %b %Y, %I:%M %p') if a.created_at else 'N/A'}</div>
                <p style="font-size: 13.5px; color: #334155;"><b>AI Reason:</b> {a.reason or 'N/A'}</p>
                """, unsafe_allow_html=True)
                st.code(a.action_data, language="json")
                if a.notes:
                    st.caption(f"Supervisor Notes: {a.notes}")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="smart-empty-state">
                <div class="smart-empty-icon">✓</div>
                <div class="smart-empty-title">No Approvals Recorded</div>
                <div class="smart-empty-subtitle">Zero human-in-the-loop approval records exist for this company.</div>
            </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # VIEW 3: SUPPORT TICKETS QUEUE
    # =========================================================================
    elif st.session_state.admin_nav == "tickets":
        st.markdown("""
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-bottom: 4px;">🎫 Support Ticket Resolution Queue</h2>
            <div style="font-size: 13.5px; color: #64748b;">Inspect escalated inquiries, update assignment, and record resolution notes.</div>
        </div>
        """, unsafe_allow_html=True)

        status_filter = st.selectbox("Filter Status", ["All", "open", "in_progress", "resolved", "closed"])

        filtered_tickets = tickets
        if status_filter != "All":
            filtered_tickets = [t for t in tickets if t.status == status_filter]

        if filtered_tickets:
            for t in filtered_tickets:
                t_badge = "badge-orange" if t.status in ["open", "in_progress"] else "badge-green"
                st.markdown("<div class='intelligence-card'>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <h4 style="font-size: 16px; font-weight: 700; color: #0f172a; margin: 0;">{t.ticket_number}: {t.title}</h4>
                    <span class="{t_badge}">{t.status.upper()}</span>
                </div>
                <div style="font-size: 12px; color: #64748b; margin: 4px 0 10px 0;">Priority: <b>{t.priority.upper()}</b> | Customer ID: {t.customer_id}</div>
                <p style="font-size: 13.5px; color: #334155; line-height: 1.5; margin-bottom: 12px;">{t.description}</p>
                """, unsafe_allow_html=True)

                if t.resolution:
                    st.info(f"Current Resolution: {t.resolution}")

                c_st, c_res, c_btn = st.columns([1.2, 2.2, 1.2])
                with c_st:
                    new_st = st.selectbox("Update Status", ["open", "in_progress", "resolved", "closed"], index=["open", "in_progress", "resolved", "closed"].index(t.status), key=f"tst_{t.id}")
                with c_res:
                    new_res = st.text_input("Resolution Note", value=t.resolution or "", key=f"tres_{t.id}")
                with c_btn:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("Save Updates", key=f"tbtn_{t.id}", type="primary", use_container_width=True):
                        update_ticket_status(ticket_id=t.id, status=new_st, resolution=new_res, admin_user_id=admin_user.id, company_id=company_id)
                        st.success(f"Ticket {t.ticket_number} updated!")
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="smart-empty-state">
                <div class="smart-empty-icon">✓</div>
                <div class="smart-empty-title">No Tickets Found</div>
                <div class="smart-empty-subtitle">Zero support tickets match the selected filter criteria.</div>
            </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # VIEW 4: CUSTOMERS DIRECTORY
    # =========================================================================
    elif st.session_state.admin_nav == "customers":
        st.markdown(f"""
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-bottom: 4px;">👥 Customer Directory</h2>
            <div style="font-size: 13.5px; color: #64748b;">Verified customer accounts registered under <b>{company_name}</b>.</div>
        </div>
        """, unsafe_allow_html=True)

        if customers:
            for c in customers:
                st.markdown(f"""
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <h4 style="font-size: 16px; font-weight: 700; color: #0f172a; margin: 0;">{c.name}</h4>
                        <span class="badge-purple">DB ID: {c.id}</span>
                    </div>
                    <div style="font-size: 12.5px; color: #475569; margin-top: 6px; line-height: 1.6;">
                        <div><b>External ID:</b> <code>{c.external_customer_id or 'N/A'}</code> | <b>Status:</b> {c.status}</div>
                        <div><b>Email:</b> {c.email} | <b>Phone:</b> {c.phone or 'N/A'} | <b>Joined:</b> {c.created_at.strftime('%d %b %Y') if c.created_at else 'N/A'}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="smart-empty-state">
                <div class="smart-empty-icon">👥</div>
                <div class="smart-empty-title">No Customers Registered</div>
                <div class="smart-empty-subtitle">No customer profiles currently exist for this company in PostgreSQL.</div>
            </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # VIEW 5: KNOWLEDGE VAULT
    # =========================================================================
    elif st.session_state.admin_nav == "knowledge":
        st.markdown("""
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-bottom: 4px;">📚 Policy Knowledge Vault (Multi-Tenant RAG)</h2>
            <div style="font-size: 13.5px; color: #64748b;">Upload enterprise policy documents (.txt, .pdf, .docx) to index into company-isolated FAISS vector store.</div>
        </div>
        """, unsafe_allow_html=True)

        col_u, col_l = st.columns([1.2, 1.8], gap="large")

        with col_u:
            st.markdown("<div class='intelligence-card'>", unsafe_allow_html=True)
            st.markdown("<div class='intelligence-card-header'><span class='intelligence-card-title'>Upload Knowledge Document</span></div>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Select Policy Document", type=["txt", "pdf", "docx"], key="doc_uploader")
            doc_type_val = st.selectbox("Document Category", ["policy", "faq", "terms", "shipping", "warranty"], key="doc_type_select")
            if uploaded_file:
                if st.button("Index Document into FAISS →", type="primary", use_container_width=True):
                    with st.spinner("Parsing and building semantic FAISS embeddings..."):
                        try:
                            bytes_data = uploaded_file.read()
                            res = save_and_index_document(
                                company_id=company_id,
                                filename=uploaded_file.name,
                                content=bytes_data,
                                uploaded_by_user_id=admin_user.id,
                                doc_type=doc_type_val,
                            )
                            st.success(f"Indexed document successfully ({res.get('chunk_count', 0)} chunks)!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Ingestion failed: {str(e)}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_l:
            st.markdown("<div class='intelligence-card'>", unsafe_allow_html=True)
            st.markdown("<div class='intelligence-card-header'><span class='intelligence-card-title'>Indexed Company Documents</span></div>", unsafe_allow_html=True)
            docs = list_knowledge_documents(company_id)
            if docs:
                for d in docs:
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f1f5f9;">
                        <div>
                            <div style="font-size: 14px; font-weight: 700; color: #0f172a;">📄 {d['filename']}</div>
                            <div style="font-size: 12px; color: #64748b;">Type: {d['doc_type']} | Chunks: {d['chunk_count'] or 'Indexed'} | Status: <b>{d['status']}</b></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"🗑️ Delete {d['filename']}", key=f"del_doc_{d['id']}"):
                        delete_knowledge_document(company_id=company_id, doc_id=d['id'], admin_user_id=admin_user.id)
                        st.success(f"Deleted '{d['filename']}'.")
                        st.rerun()
            else:
                st.markdown("""
                <div class="smart-empty-state">
                    <div class="smart-empty-icon">📚</div>
                    <div class="smart-empty-title">No Documents Indexed</div>
                    <div class="smart-empty-subtitle">Upload your first company policy on the left to activate semantic RAG.</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # VIEW 6: HEALTH & AUDIT TRAIL
    # =========================================================================
    elif st.session_state.admin_nav == "health":
        st.markdown("""
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-bottom: 4px;">🔌 Integrations & Compliance Audit Trail</h2>
            <div style="font-size: 13.5px; color: #64748b;">Live infrastructure connectivity and immutable chronological audit records.</div>
        </div>
        """, unsafe_allow_html=True)

        health = get_integration_health()
        h1, h2, h3 = st.columns(3)

        with h1:
            st.markdown("<div class='intelligence-card'>", unsafe_allow_html=True)
            st.markdown("<div class='intelligence-card-header'><span class='intelligence-card-title'>Database Engine</span><span class='badge-green'>LIVE</span></div>", unsafe_allow_html=True)
            st.write(f"**Type:** {health['database']['type']}")
            st.write(f"**Status:** {health['database']['status']}")
            st.caption(f"URL: {health['database']['url_masked']}")
            st.markdown("</div>", unsafe_allow_html=True)

        with h2:
            st.markdown("<div class='intelligence-card'>", unsafe_allow_html=True)
            st.markdown("<div class='intelligence-card-header'><span class='intelligence-card-title'>Cashfree Sandbox PG</span><span class='badge-blue'>2025-01-01</span></div>", unsafe_allow_html=True)
            st.write(f"**Environment:** {health['cashfree']['environment'].upper()}")
            st.write(f"**Status:** {health['cashfree']['status']}")
            st.caption(f"Client ID: {health['cashfree']['client_id_masked']}")
            st.markdown("</div>", unsafe_allow_html=True)

        with h3:
            st.markdown("<div class='intelligence-card'>", unsafe_allow_html=True)
            st.markdown("<div class='intelligence-card-header'><span class='intelligence-card-title'>Hugging Face Inference</span><span class='badge-purple'>LLM</span></div>", unsafe_allow_html=True)
            st.write(f"**Model:** `{health['huggingface']['model']}`")
            st.write(f"**Status:** {health['huggingface']['status']}")
            st.caption(f"Token: {health['huggingface']['token_masked']}")
            st.markdown("</div>", unsafe_allow_html=True)

        # Audit Logs Section
        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='intelligence-card'>", unsafe_allow_html=True)
        st.markdown("<div class='intelligence-card-header'><span class='intelligence-card-title'>Compliance & Event Audit Stream</span></div>", unsafe_allow_html=True)

        logs = list_audit_logs(company_id, limit=50)
        if logs:
            for l in logs:
                st.markdown(f"""
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <span style="font-size: 13.5px; font-weight: 700; color: #0f172a;">{l['action']}</span>
                        <span class="badge-gray">{l['actor_type'].upper()}</span>
                    </div>
                    <div style="font-size: 12px; color: #64748b; margin-top: 3px;">
                        Target: <code>{l['target_type']}:{l['target_id'] or 'N/A'}</code> | Status: <b>{l['status']}</b> | {l['created_at']}
                    </div>
                    <div style="font-size: 12.5px; color: #334155; margin-top: 4px;">{l['details']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="smart-empty-state">
                <div class="smart-empty-icon">📜</div>
                <div class="smart-empty-title">No Audit Events</div>
                <div class="smart-empty-subtitle">Zero audit log entries recorded for this company.</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
