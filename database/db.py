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

        matched_product = None
        for row in rows:
            if _match_keywords(user_query, row.get("keywords") or ""):
                matched_product = dict(row)
                break

        if matched_product is None:
            return None

        # Fetch offer for this product
        cur.execute(
            "SELECT * FROM offers WHERE product_id = %s",
            (matched_product["product_id"],)
        )
        offer_row = cur.fetchone()
        matched_product["offer"] = dict(offer_row) if offer_row else None
        return matched_product

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
