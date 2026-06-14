#!/bin/bash
set -e

echo "  [BOOT] Ayansh Infocom Chatbot — Starting..."

# Sync knowledge chunks to ChromaDB vector store
# (reads from Supabase and builds local vector index)
echo "  [BOOT] Syncing vectors from Supabase..."
python -m database.sync_vectors || echo "  [WARN] Vector sync failed — will retry on next boot"

# Start the FastAPI server
echo "  [BOOT] Starting Uvicorn on port 7860..."
exec python -m uvicorn app:app --host 0.0.0.0 --port 7860
