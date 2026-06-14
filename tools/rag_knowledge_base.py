"""
RAG / Knowledge-Base FAQ Tool — Database-backed
================================================
Queries the SQLite database (ayansh.db) for relevant knowledge
chunks: technical specs, company info, and FAQ policies.

To add/edit knowledge entries, run:  python database/seed.py
or edit the database directly using any SQLite client.
"""

from __future__ import annotations

from database.db import query_knowledge


# ═══════════════════════════════════════════════════════════
#  PUBLIC API — called by the LangGraph tool node
# ═══════════════════════════════════════════════════════════

def query_rag_faq(user_query: str) -> str:
    """
    Query the SQLite knowledge_chunks table for relevant FAQ
    and specification data based on keyword matching.

    Parameters
    ----------
    user_query : str
        The natural-language question from the user.

    Returns
    -------
    str
        Concatenated text chunks most relevant to the query.
    """
    chunks = query_knowledge(user_query)

    if not chunks:
        return (
            "No relevant knowledge-base documents found. "
            "Please contact support@ayanshinfo.com for help."
        )

    separator = "\n\n" + "─" * 60 + "\n\n"
    return separator.join(chunks)
