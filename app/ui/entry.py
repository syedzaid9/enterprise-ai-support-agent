"""
ResolveAI Entry Screen.
Allows users to select between the Customer Portal and the Admin Portal.
"""

import streamlit as st


def render_entry_screen():
    """
    Render the clean enterprise landing page for portal selection.
    """
    st.markdown("""
    <div style="text-align: center; margin-top: 30px; margin-bottom: 35px;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 64px; height: 64px; background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); border-radius: 18px; color: white; font-size: 32px; font-weight: 800; box-shadow: 0 8px 24px rgba(79, 70, 229, 0.35); margin-bottom: 16px;">
            ⚡
        </div>
        <h1 style="font-size: 34px; font-weight: 800; color: #0f172a; margin-bottom: 6px; letter-spacing: -0.8px;">
            RESOLVEAI
        </h1>
        <div style="font-size: 16px; font-weight: 600; color: #4f46e5; margin-bottom: 8px;">
            Enterprise AI Customer Support & Resolution Platform
        </div>
        <p style="font-size: 14px; color: #64748b; max-width: 540px; margin: 0 auto;">
            Intelligent resolution copilot with real-time billing integration, policy RAG, and supervisor authorization.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; margin-bottom: 24px;">
        <span style="font-size: 13px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;">
            Select Access Portal
        </span>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown("""
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 18px; padding: 28px 24px; text-align: center; box-shadow: 0 4px 16px rgba(0,0,0,0.03); height: 100%;">
            <div style="width: 52px; height: 52px; background: #ede9fe; color: #4f46e5; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 26px; margin: 0 auto 16px auto;">
                👤
            </div>
            <div style="font-size: 20px; font-weight: 800; color: #0f172a; margin-bottom: 6px;">
                Customer Portal
            </div>
            <div style="font-size: 13px; color: #64748b; line-height: 1.5; margin-bottom: 24px;">
                Get instant support from AI Copilot, check Cashfree subscription status, verify transaction records, and manage tickets.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Continue as Customer →", type="primary", use_container_width=True, key="btn_portal_cust"):
            st.session_state.portal_selection = "customer"
            st.session_state.auth_tab = "login"
            st.rerun()

    with c2:
        st.markdown("""
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 18px; padding: 28px 24px; text-align: center; box-shadow: 0 4px 16px rgba(0,0,0,0.03); height: 100%;">
            <div style="width: 52px; height: 52px; background: #eff6ff; color: #2563eb; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 26px; margin: 0 auto 16px auto;">
                🛡️
            </div>
            <div style="font-size: 20px; font-weight: 800; color: #0f172a; margin-bottom: 6px;">
                Admin Portal
            </div>
            <div style="font-size: 13px; color: #64748b; line-height: 1.5; margin-bottom: 24px;">
                Oversee customer inquiries, authorize sensitive financial refunds (Human-in-the-Loop), monitor agent activity, and manage policies.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Continue as Admin →", type="secondary", use_container_width=True, key="btn_portal_admin"):
            st.session_state.portal_selection = "admin"
            st.session_state.auth_tab = "login"
            st.rerun()

    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; font-size: 12px; color: #94a3b8;">
        <span>⚡ ResolveAI Platform v1.0</span> • 
        <span>PostgreSQL / SQLite Database</span> • 
        <span>Cashfree Sandbox Ready</span>
    </div>
    """, unsafe_allow_html=True)
