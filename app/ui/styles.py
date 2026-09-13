"""
Shared CSS and Design Tokens for ResolveAI Enterprise Interface.
"""

import streamlit as st


def apply_global_styles():
    """
    Inject global styling into Streamlit page.
    """
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

    <style>
        /* Base typography & colors */
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #1e293b;
        }
        
        .stApp {
            background-color: #f8fafc;
        }

        /* Container padding */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 2.5rem;
            max-width: 100%;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0;
            padding-top: 1.2rem;
        }

        /* Brand Headers */
        .brand-icon-box {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-size: 22px;
            font-weight: 800;
            box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3);
        }
        .brand-title {
            font-size: 20px;
            font-weight: 800;
            color: #0f172a;
            line-height: 1.1;
            letter-spacing: -0.4px;
        }
        .brand-sub {
            font-size: 12px;
            font-weight: 500;
            color: #64748b;
            margin-top: 2px;
        }

        /* Cards & Panels */
        .saas-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }
        .saas-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 15px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 12px;
        }

        /* Metrics */
        .metric-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }
        .metric-label {
            font-size: 12px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: 800;
            color: #0f172a;
            margin-top: 4px;
        }

        /* Chat Bubbles */
        .copilot-bubble {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 16px 18px;
            color: #1e293b;
            font-size: 14px;
            line-height: 1.55;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
            margin-bottom: 14px;
        }
        .user-bubble {
            background: linear-gradient(135deg, #4338ca 0%, #4f46e5 100%);
            color: #ffffff;
            border-radius: 14px 14px 2px 14px;
            padding: 12px 18px;
            font-size: 14px;
            font-weight: 500;
            display: inline-block;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
            margin-bottom: 14px;
        }

        /* Badges */
        .badge-green {
            background: #dcfce7;
            color: #15803d;
            border: 1px solid #bbf7d0;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11.5px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .badge-orange {
            background: #ffedd5;
            color: #c2410c;
            border: 1px solid #fed7aa;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11.5px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .badge-purple {
            background: #ede9fe;
            color: #4f46e5;
            border: 1px solid #ddd6fe;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11.5px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .badge-blue {
            background: #eff6ff;
            color: #2563eb;
            border: 1px solid #bfdbfe;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11.5px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }

        /* Table & Lists */
        .styled-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13.5px;
        }
        .styled-table th {
            background-color: #f1f5f9;
            color: #475569;
            font-weight: 700;
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        .styled-table td {
            padding: 12px 14px;
            border-bottom: 1px solid #f1f5f9;
            color: #1e293b;
        }
        .styled-table tr:hover {
            background-color: #f8fafc;
        }

        /* Tool Notification Box */
        .tool-checked-box {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 12px;
            padding: 12px 16px;
            margin: 10px 0;
        }
    </style>
    """, unsafe_allow_html=True)
