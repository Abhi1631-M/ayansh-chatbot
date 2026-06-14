"""
Vector Database Synchronization Script
======================================
Reads all records from the SQLite knowledge_chunks table
and upserts them into ChromaDB. Run this script once to
build your initial vector index.
"""
from database.db import get_connection
from database.vector_db import upsert_knowledge_chunk

def sync_knowledge_to_vector_db():
    print("Connecting to SQLite database...")
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, title, content, category FROM knowledge_chunks").fetchall()
        
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
