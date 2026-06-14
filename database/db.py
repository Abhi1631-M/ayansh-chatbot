"""
Database Helper Module — Supabase PostgreSQL
=============================================
Provides connection and query utilities for the Ayansh Infocom
PostgreSQL database hosted on Supabase.

Usage
-----
from database.db import query_product, query_knowledge
"""

from __future__ import annotations

import os
import psycopg2
import psycopg2.extras


def _get_db_url() -> str:
    """Build the database URL from env vars."""
    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set!")
    return url


def get_connection():
    """Return a psycopg2 connection with RealDictCursor for dict-like rows."""
    conn = psycopg2.connect(_get_db_url())
    return conn


def _dict_cursor(conn):
    """Return a cursor that returns rows as dicts."""
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# ── Keyword matching helpers ─────────────────────────────────

def _match_keywords(query: str, keywords_csv: str) -> bool:
    """Return True if any keyword from keywords_csv appears in query."""
    if not keywords_csv:
        return False
    query_lower = query.lower()
    for kw in keywords_csv.split(","):
        kw = kw.strip()
        if kw and kw in query_lower:
            return True
    return False


# ═══════════════════════════════════════════════════════════
#  PUBLIC QUERY FUNCTIONS
# ═══════════════════════════════════════════════════════════

def query_product(user_query: str) -> dict | None:
    """
    Search the products table for the best keyword match.
    Returns the product row as a dict (including its offer if any),
    or None if no match is found.
    """
    conn = get_connection()
    try:
        cur = _dict_cursor(conn)
        cur.execute("SELECT * FROM products")
        rows = cur.fetchall()

        best_product = None
        best_score = 0
        
        query_lower = user_query.lower()

        for row in rows:
            keywords_csv = row.get("keywords") or ""
            score = 0
            
            # Count how many of this product's keywords appear in the user's query
            for kw in keywords_csv.split(","):
                kw = kw.strip()
                if kw and kw in query_lower:
                    # Give higher weight to longer keywords (e.g. "airtel router" > "router")
                    score += len(kw)
                    
            if score > best_score:
                best_score = score
                best_product = dict(row)

        if best_product is None:
            return None

        # Fetch offer for this product
        cur.execute(
            "SELECT * FROM offers WHERE product_id = %s",
            (best_product["product_id"],)
        )
        offer_row = cur.fetchone()
        best_product["offer"] = dict(offer_row) if offer_row else None
        return best_product

    finally:
        conn.close()


def query_knowledge(user_query: str) -> list[str]:
    """
    Search the knowledge_chunks table using semantic Vector Search.
    """
    from database.vector_db import query_vector_knowledge

    matched_chunks = query_vector_knowledge(user_query, n_results=3)

    # Fallback to SQL if Chroma is empty
    if not matched_chunks:
        conn = get_connection()
        try:
            cur = _dict_cursor(conn)
            cur.execute(
                "SELECT * FROM knowledge_chunks WHERE category IN ('general_faq','company_info') LIMIT 2"
            )
            fallback = cur.fetchall()
            matched_chunks = [f"**{r['title']}**\n{r['content']}" for r in fallback]
        finally:
            conn.close()

    return matched_chunks


def get_all_products() -> list[dict]:
    """Return all products from the database (admin use)."""
    conn = get_connection()
    try:
        cur = _dict_cursor(conn)
        cur.execute("SELECT * FROM products ORDER BY category, name")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def save_lead(customer_name: str, contact_info: str, product_interest: str) -> bool:
    """Save a captured lead into the PostgreSQL database."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO leads (customer_name, contact_info, product_interest) VALUES (%s, %s, %s)",
            (customer_name, contact_info, product_interest)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving lead: {e}")
        return False
    finally:
        conn.close()


def get_all_leads() -> list[dict]:
    """Fetch all leads for the Admin portal."""
    conn = get_connection()
    try:
        cur = _dict_cursor(conn)
        cur.execute("SELECT id, customer_name, contact_info, product_interest, status, TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at FROM leads ORDER BY created_at DESC")
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()
