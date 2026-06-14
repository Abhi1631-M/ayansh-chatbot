"""
Database Helper Module
======================
Provides connection and query utilities for the Ayansh Infocom
SQLite database (ayansh.db).

On Hugging Face Spaces, data is stored in /data for persistence
across restarts. On first boot, the seed database is copied there.

Usage
-----
from database.db import query_product, query_knowledge
"""

from __future__ import annotations

import os
import shutil
import sqlite3
from pathlib import Path

# ── Resolve database paths ─────────────────────────────────────
# The seed database is baked into the Docker image at build time
_SEED_DB_PATH = Path(__file__).resolve().parent / "ayansh.db"

# For persistence, we prefer /data (HF Spaces persistent volume)
_PERSISTENT_DIR = Path("/data")

if _PERSISTENT_DIR.exists() and os.access(str(_PERSISTENT_DIR), os.W_OK):
    _DB_PATH = _PERSISTENT_DIR / "ayansh.db"
    # On first boot, copy the seed DB to persistent storage
    if not _DB_PATH.exists():
        shutil.copy2(str(_SEED_DB_PATH), str(_DB_PATH))
        print(f"  [PERSIST] Copied seed DB to {_DB_PATH}")
    else:
        print(f"  [PERSIST] Using existing persistent DB at {_DB_PATH}")
else:
    # Local development or no persistent volume — use the original path
    _DB_PATH = _SEED_DB_PATH
    print(f"  [LOCAL] Using local DB at {_DB_PATH}")


def get_connection() -> sqlite3.Connection:
    """Return a sqlite3 connection with row_factory set to Row."""
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ── Keyword matching helpers ─────────────────────────────────

def _tokenize(text: str) -> list[str]:
    """Lowercase and split text into words for keyword matching."""
    return text.lower().split()


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
        # Fetch all products + their keywords
        rows = conn.execute(
            "SELECT * FROM products"
        ).fetchall()

        matched_product = None
        for row in rows:
            if _match_keywords(user_query, row["keywords"] or ""):
                matched_product = dict(row)
                break

        if matched_product is None:
            return None

        # Fetch offer for this product
        offer_row = conn.execute(
            "SELECT * FROM offers WHERE product_id = ?",
            (matched_product["product_id"],)
        ).fetchone()

        matched_product["offer"] = dict(offer_row) if offer_row else None
        return matched_product

    finally:
        conn.close()


def query_knowledge(user_query: str) -> list[str]:
    """
    Search the knowledge_chunks table using semantic Vector Search.
    """
    from database.vector_db import query_vector_knowledge
    
    # We query the Chroma vector store instead of SQL keywords
    matched_chunks = query_vector_knowledge(user_query, n_results=3)
    
    # If Chroma is completely empty (e.g., they haven't run sync_vectors.py),
    # fallback to general FAQ from SQLite as a safety net
    if not matched_chunks:
        conn = get_connection()
        try:
            fallback = conn.execute(
                "SELECT * FROM knowledge_chunks WHERE category IN ('general_faq','company_info') LIMIT 2"
            ).fetchall()
            matched_chunks = [f"**{r['title']}**\n{r['content']}" for r in fallback]
        finally:
            conn.close()

    return matched_chunks


def get_all_products() -> list[dict]:
    """Return all products from the database (admin use)."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM products ORDER BY category, name").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
