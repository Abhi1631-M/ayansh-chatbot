"""
Vector Database Synchronization Script
======================================
Reads all records from the Supabase PostgreSQL knowledge_chunks table
and upserts them into ChromaDB. Run this script once to
build your initial vector index.
"""
import sys
import io
from pathlib import Path

# Fix Unicode on Windows terminals
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Load .env so DATABASE_URL is available
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from database.db import get_connection, _dict_cursor
from database.vector_db import upsert_knowledge_chunk

def sync_knowledge_to_vector_db():
    print("Connecting to Supabase PostgreSQL database...")
    conn = get_connection()
    try:
        cur = _dict_cursor(conn)
        cur.execute("SELECT id, title, content, category FROM knowledge_chunks")
        rows = cur.fetchall()
        
        print(f"Found {len(rows)} knowledge chunks. Generating embeddings...")
        for row in rows:
            print(f"  -> Embedding: {row['title']}")
            upsert_knowledge_chunk(
                chunk_id=row['id'],
                title=row['title'],
                content=row['content'],
                category=row['category']
            )
        
        print("Done! All knowledge chunks are now in the Vector DB.")
    finally:
        conn.close()

if __name__ == "__main__":
    sync_knowledge_to_vector_db()
