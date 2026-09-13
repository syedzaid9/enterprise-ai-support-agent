"""
ResolveAI — Enterprise AI Customer Support & Resolution Platform
Main Streamlit Application Controller.
Manages database initialization, secure authentication routing, and portal rendering.
"""

import sys
from pathlib import Path
import streamlit as st

# Add project root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db.database import init_db
from app.auth.service import get_user_by_id
from app.ui.styles import apply_global_styles
from app.ui.entry import render_entry_screen
from app.ui.auth import render_auth_screen
from app.ui.customer_dashboard import render_customer_dashboard
from app.ui.admin_dashboard import render_admin_dashboard

# Page Configuration
st.set_page_config(
    page_title="ResolveAI — Enterprise AI Resolution Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# Apply global CSS design system
apply_global_styles()


# Initialize Database tables on first launch
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# Session State Keys
if "authenticated_user_id" not in st.session_state:
    st.session_state.authenticated_user_id = None

if "authenticated_role" not in st.session_state:
    st.session_state.authenticated_role = None

if "portal_selection" not in st.session_state:
    st.session_state.portal_selection = None


def main():
    """
    Main application routing based on verified database role and authentication state.
    """
    user_id = st.session_state.authenticated_user_id

    # 1. Unauthenticated Flow
    if not user_id:
        if not st.session_state.portal_selection:
            render_entry_screen()
        else:
            render_auth_screen()
        return

    # 2. Authenticated Flow — Validate user and role directly against database
    user = get_user_by_id(user_id)
    if not user or not user.is_active:
        st.session_state.authenticated_user_id = None
        st.session_state.authenticated_role = None
        st.session_state.portal_selection = None
        st.error("Session expired or invalid user account. Please log in again.")
        st.rerun()
        return

    # 3. Route to Verified Role Portal
    if user.role == "admin":
        render_admin_dashboard()
    elif user.role == "customer":
        render_customer_dashboard()
    else:
        st.error(f"Unrecognized role: '{user.role}'. Access denied.")
        st.session_state.authenticated_user_id = None
        st.rerun()


if __name__ == "__main__":
    main()
