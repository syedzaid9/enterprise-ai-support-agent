"""
Authentication UI for ResolveAI.
Renders clean, secure Login and Registration forms for both Customer and Admin portals.
"""

import streamlit as st
from app.auth.service import authenticate_user, register_customer, register_admin


def render_auth_screen():
    """
    Render authentication flow depending on selected portal (Customer or Admin).
    """
    portal = st.session_state.get("portal_selection", "customer")
    is_admin = (portal == "admin")

    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("← Back to Portals", key="btn_auth_back"):
            st.session_state.portal_selection = None
            st.session_state.auth_error = None
            st.rerun()

    portal_title = "Admin Portal" if is_admin else "Customer Portal"
    portal_icon = "🛡️" if is_admin else "👤"
    portal_color = "#2563eb" if is_admin else "#4f46e5"

    st.markdown(f"""
    <div style="text-align: center; margin-top: 10px; margin-bottom: 25px;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 50px; height: 50px; background: {portal_color}; border-radius: 14px; color: white; font-size: 24px; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);">
            {portal_icon}
        </div>
        <h2 style="font-size: 26px; font-weight: 800; color: #0f172a; margin-bottom: 4px;">
            {portal_title}
        </h2>
        <div style="font-size: 13px; color: #64748b;">
            {"Secure operations and supervisor console" if is_admin else "Access AI support, track orders, and manage subscriptions"}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Center card layout
    _, col_center, _ = st.columns([1, 2.2, 1])

    with col_center:
        st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔑 Sign In", "✨ Create Account"])

        # ==========================================
        # TAB 1: LOGIN
        # ==========================================
        with tab_login:
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            with st.form("login_form"):
                email = st.text_input("Email Address", placeholder="e.g. alex@example.com" if not is_admin else "admin@resolveai.io")
                password = st.text_input("Password", type="password", placeholder="Enter your password")

                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Sign In →", type="primary", use_container_width=True)

                if submitted:
                    expected_role = "admin" if is_admin else "customer"
                    user, error_msg = authenticate_user(
                        email=email,
                        password=password,
                        expected_role=expected_role,
                    )
                    if user:
                        st.session_state.authenticated_user_id = user.id
                        st.session_state.authenticated_role = user.role
                        st.session_state.auth_error = None
                        st.session_state.messages = []  # Reset session chat
                        st.success(f"Welcome back! Authenticated as {user.role.upper()}.")
                        st.rerun()
                    else:
                        st.error(error_msg or "Invalid email or password.")

            st.caption("New here? Switch to the **✨ Create Account** tab to register.")


        # ==========================================
        # TAB 2: REGISTRATION
        # ==========================================
        with tab_register:
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            if is_admin:
                # Admin Registration Form
                with st.form("admin_register_form"):
                    company_name = st.text_input("Company / Organization Name", placeholder="e.g. Acme Corp")
                    admin_name = st.text_input("Admin Full Name", placeholder="e.g. Sarah Jenkins")
                    email = st.text_input("Work Email Address", placeholder="e.g. sarah@acme.com")
                    c_p1, c_p2 = st.columns(2)
                    with c_p1:
                        password = st.text_input("Password", type="password", placeholder="Min 6 characters")
                    with c_p2:
                        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")

                    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                    submitted_reg = st.form_submit_button("Create Admin Account →", type="primary", use_container_width=True)

                    if submitted_reg:
                        if password != confirm_password:
                            st.error("Passwords do not match.")
                        else:
                            try:
                                user = register_admin(
                                    company_name=company_name,
                                    admin_name=admin_name,
                                    email=email,
                                    password=password,
                                )
                                st.session_state.authenticated_user_id = user.id
                                st.session_state.authenticated_role = "admin"
                                st.session_state.messages = []
                                st.success("Admin account created successfully!")
                                st.rerun()
                            except ValueError as e:
                                st.error(str(e))
            else:
                # Customer Registration Form
                with st.form("customer_register_form"):
                    full_name = st.text_input("Full Name", placeholder="e.g. Alex Rivera")
                    email = st.text_input("Email Address", placeholder="e.g. alex@example.com")
                    phone = st.text_input("Phone Number (Optional)", placeholder="e.g. +1 555-0199")
                    ext_id = st.text_input("External Customer ID (Optional)", placeholder="e.g. CUST-9021")

                    c_p1, c_p2 = st.columns(2)
                    with c_p1:
                        password = st.text_input("Password", type="password", placeholder="Min 6 characters")
                    with c_p2:
                        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")

                    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                    submitted_reg = st.form_submit_button("Create Customer Account →", type="primary", use_container_width=True)

                    if submitted_reg:
                        if password != confirm_password:
                            st.error("Passwords do not match.")
                        else:
                            try:
                                customer = register_customer(
                                    full_name=full_name,
                                    email=email,
                                    password=password,
                                    phone=phone,
                                    external_customer_id=ext_id,
                                )
                                st.session_state.authenticated_user_id = customer.user_id
                                st.session_state.authenticated_role = "customer"
                                st.session_state.messages = []
                                st.success("Customer account registered successfully!")
                                st.rerun()
                            except ValueError as e:
                                st.error(str(e))

        st.markdown("</div>", unsafe_allow_html=True)
