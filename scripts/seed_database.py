"""
ResolveAI — Development Database Seed Script.
Populates initial development records (companies, demo users, demo customers, subscriptions, tickets)
into PostgreSQL.
Run manually when setting up a fresh development environment:
    python scripts/seed_database.py
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.seed import seed_database

if __name__ == "__main__":
    print("[*] Starting ResolveAI database seed script...")
    seed_database()
    print("[+] Database seeding complete.")
