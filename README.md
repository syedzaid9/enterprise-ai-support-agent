# ResolveAI — Multi-Tenant Enterprise AI Support & Resolution Platform

**ResolveAI** is a multi-tenant AI customer-support resolution platform designed to investigate and resolve real customer-support issues.

ResolveAI adheres to the principle:
> **Answering questions is not the same as resolving customer issues.**

Instead of returning generic FAQ answers, ResolveAI combines **authenticated customer identity**, **PostgreSQL database state**, **real Cashfree Sandbox transactions**, **tenant-isolated RAG company policies**, **LangGraph decision workflows**, and **Human-in-the-Loop (HITL) supervisor authorization** to deliver verified resolutions.

---

## 1. System Architecture

```
                    ┌────────────────────────┐
                    │   Customer / Admin     │
                    └───────────┬────────────┘
                                │ Authenticate (JWT / Role)
                                ▼
                    ┌────────────────────────┐
                    │  Customer Context      │
                    │  (PostgreSQL + Tenant) │
                    └───────────┬────────────┘
                                │ User Query
                                ▼
                    ┌────────────────────────┐
                    │  LangGraph Resolution  │
                    │        Workflow        │
                    └───────────┬────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
 ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
 │  PostgreSQL  │        │   FAISS RAG  │        │   Cashfree   │
 │   Database   │        │   Policies   │        │  PG Sandbox  │
 └──────┬───────┘        └──────┬───────┘        └──────┬───────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │   Investigation &      │
                    │   Policy Evaluation    │
                    └───────────┬────────────┘
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
        ┌─────────────────┐           ┌─────────────────┐
        │ Safe / Read-Only│           │ Sensitive Action│
        │   Execution     │           │ (Refund/Cancel) │
        └────────┬────────┘           └────────┬────────┘
                 │                             │ Pauses with Interrupt
                 │                             ▼
                 │                    ┌─────────────────┐
                 │                    │  Admin Approval │
                 │                    │  (HITL Portal)  │
                 │                    └────────┬────────┘
                 │                             │ Resumes & Executes
                 └──────────────┬──────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │ Verification, DB Sync, │
                    │ Audit Logging, Reply   │
                    └────────────────────────┘
```

---

## 2. Core Features & Capabilities

- **Pure Real Data Architecture**: Zero fake customers, zero fake fallback IDs, and zero simulated billing records on signup.
- **Multi-Tenant Isolation**: Complete `company_id` segregation across database models, AI tools, vector store queries, and support ticket queues.
- **Real Cashfree Sandbox PG Integration**: Creates payment sessions, orders, and recurring subscription authorizations without faking payment completion.
- **Tenant-Isolated RAG**: Document parsing, semantic chunking, and FAISS vector retrieval filtered strictly by `company_id`.
- **Human-in-the-Loop (HITL) Governance**: High-impact financial actions (`refund_payment`, `cancel_subscription_tool`) automatically pause with LangGraph `interrupt()`, alerting supervisors in the Admin Console.
- **Automated Escalation & Ticketing**: Automatically opens and tracks tickets in PostgreSQL when issues cannot be safely resolved.
- **Comprehensive Audit Trail**: Cryptographically timestamped, immutable compliance logs in PostgreSQL.
- **Dual Interface**:
  - **FastAPI REST API**: Clean RESTful endpoints (`/api/auth`, `/api/customer`, `/api/chat`, `/api/payments`, `/api/tickets`, `/api/admin`, `/api/webhook`).
  - **Streamlit Enterprise UI**: Multi-portal interface for Customers and Admin Supervisors.

---

## 3. Technology Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, Pydantic, python-dotenv, bcrypt, PyJWT / HMAC-SHA256
- **Database**: PostgreSQL (with SQLite zero-config local development support)
- **AI Agent & Workflow**: LangChain, LangGraph, Hugging Face Hub (Inference API)
- **RAG & Embeddings**: FAISS, `sentence-transformers/all-MiniLM-L6-v2`, `RecursiveCharacterTextSplitter`
- **Payment Gateway**: Cashfree Payment Gateway Sandbox (2025-01-01 API)
- **Frontend / Dashboard**: Streamlit

---

## 4. Project Structure

```
enterprise-ai-support-agent/
├── app/
│   ├── main.py                     # FastAPI Application Backend
│   ├── config.py                   # Centralized Configuration & Health Checks
│   ├── prompts.py                  # Agent System Instructions
│   ├── agent/
│   │   └── agent.py                # Agent Definition & Tool Registry
│   ├── auth/
│   │   ├── security.py             # Password Hashing & JWT Utilities
│   │   └── service.py              # User & Customer Registration/Auth
│   ├── db/
│   │   ├── database.py             # SQLAlchemy Engine & Session Management
│   │   ├── models.py               # Multi-Tenant Relational Schema
│   │   └── seed.py                 # Development Seeder
│   ├── graph/
│   │   └── workflow.py             # LangGraph Resolution StateGraph
│   ├── integrations/
│   │   ├── payment/
│   │   │   ├── base.py             # BasePaymentProvider Interface
│   │   │   └── cashfree.py         # Cashfree Sandbox PG Client
│   │   └── subscription/
│   │       ├── base.py             # BaseSubscriptionProvider Interface
│   │       └── cashfree.py         # Cashfree Subscriptions Client
│   ├── rag/
│   │   ├── ingestion.py            # Document Loaders & Splitters
│   │   ├── vectorstore.py          # Tenant-Isolated FAISS Vector Stores
│   │   └── retriever.py            # Company-Scoped Policy Retrievers
│   ├── services/
│   │   ├── customer_service.py     # Customer Lookup
│   │   ├── customer_context.py     # Real Context Aggregation
│   │   ├── payment_service.py      # Payment Orders & Refunds
│   │   ├── subscription_service.py # Recurring Subscriptions
│   │   ├── ticket_service.py       # Support Tickets
│   │   ├── conversation_service.py # Message Persistence
│   │   ├── agent_run_service.py    # Agent Run Logs
│   │   ├── audit_service.py        # Audit Trail
│   │   └── knowledge_service.py    # Knowledge Base Document Management
│   ├── tools/
│   │   ├── customer_tools.py       # Customer Profile Tools
│   │   ├── billing_tools.py        # Cashfree & Payment Tools
│   │   ├── ticket_tools.py         # Ticket Creation & Status Tools
│   │   └── knowledge_tools.py      # Policy Search Tools
│   ├── api/
│   │   ├── auth.py                 # Auth Endpoints
│   │   ├── customer.py             # Customer Context Endpoints
│   │   ├── chat.py                 # LangGraph Chat Endpoints
│   │   ├── payment.py              # Cashfree Order & Refund Endpoints
│   │   ├── tickets.py              # Ticket Management Endpoints
│   │   ├── admin.py                # Admin Operations Endpoints
│   │   └── webhook.py              # Cashfree Webhook Handler
│   └── ui/
│       ├── styles.py               # Enterprise CSS Tokens
│       ├── entry.py                # Landing Portal Selector
│       ├── auth.py                 # Login / Registration Forms
│       ├── customer_dashboard.py   # Customer Dashboard & Copilot
│       └── admin_dashboard.py      # Admin Console & Approval Queue
├── data/
│   └── knowledge_base/             # Base Company Policy Documents
├── scripts/
│   └── seed_database.py            # Manual Dev Database Seeder
├── streamlit_app.py                # Streamlit Entrypoint Controller
├── requirements.txt                # Python Dependencies
├── .env.example                    # Configuration Template
└── README.md                       # Comprehensive Guide
```

---

## 5. Setup & Installation

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone https://github.com/syedzaid9/enterprise-ai-support-agent.git
cd enterprise-ai-support-agent

python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

| Variable | Description | Required | Example |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection URL | Yes | `postgresql://user:pass@localhost:5432/resolveai_db` |
| `CASHFREE_CLIENT_ID` | Cashfree Sandbox App/Client ID | Yes | `TEST100234...` |
| `CASHFREE_CLIENT_SECRET` | Cashfree Sandbox Secret Key | Yes | `cfsk_ma_test_...` |
| `CASHFREE_ENVIRONMENT` | Gateway mode (`sandbox` or `production`) | Yes | `sandbox` |
| `HUGGINGFACEHUB_API_TOKEN` | Hugging Face Access Token | Yes | `hf_...` |
| `JWT_SECRET` | Secret key for JWT signing | Yes | `random_32_byte_string` |

---

## 6. Running the Application

### A. Run the Streamlit Multi-Portal UI
```bash
streamlit run streamlit_app.py
```
Open your browser at `http://localhost:8501`.

### B. Run the FastAPI Backend Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger API documentation will be available at `http://localhost:8000/docs`.

---

## 7. Security & Compliance

- **Zero Secret Exposure**: API keys, tokens, and database passwords are never logged, sent to the browser, or exposed in tool outputs.
- **Tenant Isolation**: Every database query, vector search, ticket list, and conversation record is filtered by `company_id`.
- **Supervisor Authorization**: Financial transactions (refunds, order cancellations, subscription cancellations) cannot execute autonomously without explicit approval from a human admin.