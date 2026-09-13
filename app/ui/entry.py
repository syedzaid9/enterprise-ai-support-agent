"""
ResolveAI AI-Native Entry Screen.
Allows users to launch the Customer Resolution Copilot or the Supervisor AI Operations Center.
"""

import streamlit as st


def render_entry_screen():
    """
    Render the modern AI Operations platform entry screen.
    """
    # Top Minimal Status Bar
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 0; margin-bottom: 30px; border-bottom: 1px solid #e2e8f0;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div class="ai-brand-logo">⚡</div>
            <span style="font-size: 19px; font-weight: 800; color: #0f172a; letter-spacing: -0.4px;">RESOLVE<span style="color: #4f46e5;">AI</span></span>
            <span class="ai-brand-badge">ENTERPRISE</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span class="live-dot"></span>
            <span style="font-size: 12px; font-weight: 700; color: #15803d;">LangGraph Resolution Engine Online</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Hero Center
    st.markdown("""
    <div style="text-align: center; max-width: 760px; margin: 20px auto 40px auto;">
        <div style="display: inline-flex; align-items: center; gap: 6px; background: #ede9fe; color: #4338ca; padding: 6px 14px; border-radius: 30px; font-size: 12px; font-weight: 700; margin-bottom: 16px; border: 1px solid #ddd6fe;">
            <span>🤖 AI INVESTIGATION • RESOLUTION • SUPERVISION</span>
        </div>
        <h1 style="font-size: 42px; font-weight: 800; color: #0f172a; line-height: 1.15; letter-spacing: -1.2px; margin-bottom: 14px;">
            Autonomous Customer Support & Investigation Platform
        </h1>
        <p style="font-size: 16px; color: #64748b; line-height: 1.6; margin: 0 auto;">
            Resolve inquiries, verify real-time Cashfree transactions, query company policy RAG, and authorize sensitive actions with Human-in-the-Loop governance.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Portal Selection Cards
    col_cust, col_admin = st.columns(2, gap="large")

    with col_cust:
        st.markdown("""
        <div class="intelligence-card" style="padding: 30px; height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
                    <div style="width: 48px; height: 48px; background: #ede9fe; color: #4f46e5; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 24px;">
                        🤖
                    </div>
                    <span class="badge-purple">CUSTOMER PORTAL</span>
                </div>
                <h3 style="font-size: 22px; font-weight: 800; color: #0f172a; margin-bottom: 8px;">
                    AI Resolution Copilot
                </h3>
                <p style="font-size: 14px; color: #64748b; line-height: 1.55; margin-bottom: 20px;">
                    Conversational AI resolution workspace for verified customers. Real-time billing lookups, automated refund eligibility checks, and ticket tracking.
                </p>
                <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 24px;">
                    <span class="badge-gray">Cashfree Sandbox</span>
                    <span class="badge-gray">Account Telemetry</span>
                    <span class="badge-gray">Instant Support</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Launch Customer Copilot →", type="primary", use_container_width=True, key="btn_portal_cust"):
            st.session_state.portal_selection = "customer"
            st.rerun()

    with col_admin:
        st.markdown("""
        <div class="intelligence-card" style="padding: 30px; height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
                    <div style="width: 48px; height: 48px; background: #eff6ff; color: #2563eb; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 24px;">
                        🛡️
                    </div>
                    <span class="badge-blue">ADMIN PORTAL</span>
                </div>
                <h3 style="font-size: 22px; font-weight: 800; color: #0f172a; margin-bottom: 8px;">
                    AI Operations Center
                </h3>
                <p style="font-size: 14px; color: #64748b; line-height: 1.55; margin-bottom: 20px;">
                    Supervisor control center to monitor AI resolution agent telemetry, inspect live workflows, approve HITL actions, and index company policies.
                </p>
                <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 24px;">
                    <span class="badge-gray">HITL Supervision</span>
                    <span class="badge-gray">Multi-Tenant RAG</span>
                    <span class="badge-gray">Audit Logs</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Launch AI Operations Center →", type="secondary", use_container_width=True, key="btn_portal_admin"):
            st.session_state.portal_selection = "admin"
            st.rerun()

    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 50px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8;">
        <span>ResolveAI Enterprise</span> • 
        <span>Multi-Tenant Architecture</span> • 
        <span>LangGraph StateGraph</span> • 
        <span>Pure Real PostgreSQL Database</span>
    </div>
    """, unsafe_allow_html=True)

