"""
Shared CSS and Design Tokens for ResolveAI AI-Native Enterprise Interface.
Modern AI Operations styling: Topbar navigation, intelligence cards, timeline nodes, and sleek surfaces.
"""

import streamlit as st


def apply_global_styles():
    """
    Inject modern AI-native design system into Streamlit.
    """
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">

    <style>
        /* Base typography & resets */
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #0f172a;
            letter-spacing: -0.01em;
        }
        
        .stApp {
            background-color: #f8fafc;
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.04) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(59, 130, 246, 0.04) 0px, transparent 50%),
                radial-gradient(at 50% 100%, rgba(241, 245, 249, 0.5) 0px, transparent 50%);
            background-attachment: fixed;
        }

        /* Container padding */
        .main .block-container {
            padding-top: 0.8rem;
            padding-bottom: 3rem;
            max-width: 1400px;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* Hide Streamlit default sidebar when using topbar */
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        button[data-testid="baseButton-header"] {
            display: none !important;
        }

        /* ================================================================= */
        /* TOP NAVIGATION & COMMAND BAR                                      */
        /* ================================================================= */
        .ai-topbar {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 12px 20px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.04), 0 2px 6px -1px rgba(15, 23, 42, 0.02);
            backdrop-filter: blur(8px);
        }
        
        .ai-brand-group {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .ai-brand-logo {
            width: 38px;
            height: 38px;
            background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-size: 18px;
            font-weight: 800;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        }

        .ai-brand-text {
            font-size: 18px;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .ai-brand-badge {
            font-size: 11px;
            font-weight: 700;
            background: #ede9fe;
            color: #6366f1;
            padding: 2px 8px;
            border-radius: 6px;
            letter-spacing: 0.2px;
        }

        /* ================================================================= */
        /* INTELLIGENCE HERO & CARDS                                         */
        /* ================================================================= */
        .ai-hero-banner {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            padding: 28px 32px;
            margin-bottom: 24px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 20px -4px rgba(0, 0, 0, 0.03);
        }
        
        .ai-hero-banner::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #4f46e5, #3b82f6, #06b6d4);
        }

        .intelligence-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
            transition: all 0.2s ease-in-out;
            position: relative;
        }

        .intelligence-card:hover {
            border-color: #cbd5e1;
            box-shadow: 0 8px 24px -4px rgba(15, 23, 42, 0.06);
        }

        .intelligence-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 14px;
            padding-bottom: 12px;
            border-bottom: 1px solid #f1f5f9;
        }

        .intelligence-card-title {
            font-size: 13px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* Metrics Chips */
        .telemetry-chip {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 16px 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 100%;
        }

        .telemetry-label {
            font-size: 12px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .telemetry-value {
            font-size: 26px;
            font-weight: 800;
            color: #0f172a;
            margin-top: 4px;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }

        /* ================================================================= */
        /* AI SUPPORT COPILOT & CHAT CANVAS                                  */
        /* ================================================================= */
        .chat-container-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            padding: 24px;
            box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.03);
            margin-bottom: 24px;
        }

        .copilot-bubble {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 16px 20px;
            color: #1e293b;
            font-size: 14.5px;
            line-height: 1.6;
            margin-bottom: 16px;
            position: relative;
        }

        .user-bubble {
            background: linear-gradient(135deg, #4338ca 0%, #4f46e5 100%);
            color: #ffffff;
            border-radius: 16px 16px 4px 16px;
            padding: 14px 20px;
            font-size: 14.5px;
            font-weight: 500;
            line-height: 1.5;
            display: inline-block;
            box-shadow: 0 4px 14px rgba(79, 70, 229, 0.2);
            margin-bottom: 16px;
        }

        /* ================================================================= */
        /* AI RESOLUTION TIMELINE                                            */
        /* ================================================================= */
        .timeline-container {
            position: relative;
            padding-left: 28px;
            margin: 16px 0;
        }

        .timeline-container::before {
            content: "";
            position: absolute;
            top: 6px;
            bottom: 6px;
            left: 8px;
            width: 2px;
            background: #e2e8f0;
        }

        .timeline-node {
            position: relative;
            margin-bottom: 18px;
        }

        .timeline-dot {
            position: absolute;
            left: -28px;
            top: 2px;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #ffffff;
            border: 3px solid #6366f1;
            box-shadow: 0 0 0 3px #ede9fe;
        }

        .timeline-dot-success {
            border-color: #10b981;
            box-shadow: 0 0 0 3px #d1fae5;
        }

        .timeline-dot-warning {
            border-color: #f59e0b;
            box-shadow: 0 0 0 3px #fef3c7;
        }

        .timeline-title {
            font-size: 13.5px;
            font-weight: 700;
            color: #0f172a;
        }

        .timeline-meta {
            font-size: 12px;
            color: #64748b;
            margin-top: 2px;
        }

        /* ================================================================= */
        /* POLISHED SMART EMPTY STATES                                       */
        /* ================================================================= */
        .smart-empty-state {
            background: #ffffff;
            border: 1px dashed #cbd5e1;
            border-radius: 16px;
            padding: 36px 24px;
            text-align: center;
            margin: 12px 0;
        }

        .smart-empty-icon {
            width: 48px;
            height: 48px;
            background: #f1f5f9;
            color: #64748b;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            margin-bottom: 12px;
        }

        .smart-empty-title {
            font-size: 15px;
            font-weight: 700;
            color: #334155;
            margin-bottom: 4px;
        }

        .smart-empty-subtitle {
            font-size: 13px;
            color: #64748b;
            max-width: 400px;
            margin: 0 auto;
            line-height: 1.5;
        }

        /* ================================================================= */
        /* BADGES & PILLS                                                    */
        /* ================================================================= */
        .badge-green {
            background: #dcfce7;
            color: #15803d;
            border: 1px solid #bbf7d0;
            padding: 3px 10px;
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
            padding: 3px 10px;
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
            padding: 3px 10px;
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
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11.5px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .badge-gray {
            background: #f1f5f9;
            color: #475569;
            border: 1px solid #e2e8f0;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11.5px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }

        /* Pulse Dot Animation */
        .live-dot {
            width: 8px;
            height: 8px;
            background-color: #10b981;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
            animation: pulse-green 2s infinite;
        }

        @keyframes pulse-green {
            0% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
            }
            70% {
                transform: scale(1);
                box-shadow: 0 0 0 6px rgba(16, 185, 129, 0);
            }
            100% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
            }
        }
    </style>
    """, unsafe_allow_html=True)

