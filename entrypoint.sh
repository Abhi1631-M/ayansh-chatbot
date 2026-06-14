#!/bin/bash
set -e

echo "  [BOOT] Ayansh Infocom Chatbot — Starting..."

# Seed the Supabase database (safe to re-run — it replaces data)
echo "  [BOOT] Seeding Supabase PostgreSQL database..."
python -m database.seed

# Sync knowledge chunks to ChromaDB vector store
echo "  [BOOT] Syncing vectors..."
python -m database.sync_vectors

# Start the FastAPI server
echo "  [BOOT] Starting Uvicorn on port 7860..."
exec python -m uvicorn app:app --host 0.0.0.0 --port 7860
