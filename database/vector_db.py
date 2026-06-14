"""
Vector Database Logic for Ayansh Infocom
=========================================
Handles initializing the ChromaDB persistent client, creating
the knowledge collection, and running semantic vector searches.
"""
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

# Keep the chroma data locally in the database folder
_CHROMA_DIR = Path(__file__).resolve().parent / "chroma_data"

# Create a persistent client that stores vectors to disk
_client = chromadb.PersistentClient(path=str(_CHROMA_DIR))

# Use explicit sentence-transformers for English embeddings (smaller 90MB model fits in Render free tier)
_embed_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Get or create the collection for our knowledge chunks
_collection = _client.get_or_create_collection(
    name="knowledge_chunks",
    embedding_function=_embed_func
)

def query_vector_knowledge(user_query: str, n_results: int = 3) -> list[str]:
    """
    Search the vector database for chunks semantically similar to the query.
    Returns a list of formatted strings (Title + Content).
    """
    results = _collection.query(
        query_texts=[user_query],
        n_results=n_results
    )
    
    # Results is a dict with 'documents' and 'distances' as lists of lists
    if not results or not results['documents'] or not results['documents'][0]:
        return []
    
    filtered_docs = []
    # Filter out results that are semantically too far (L2 distance > 1.1)
    for doc, dist in zip(results['documents'][0], results['distances'][0]):
        if dist < 1.1:
            filtered_docs.append(doc)
            
    return filtered_docs

def upsert_knowledge_chunk(chunk_id: int, title: str, content: str, category: str):
    """
    Insert or update a chunk in the vector database.
    The ID must match the SQLite primary key to keep them in sync.
    """
    # We combine title and content for better semantic retrieval
    combined_text = f"**{title}**\n{content}"
    
    _collection.upsert(
        ids=[str(chunk_id)],
        documents=[combined_text],
        metadatas=[{"title": title, "category": category}]
    )

def delete_knowledge_chunk(chunk_id: int):
    """
    Delete a chunk from the vector database.
    """
    try:
        _collection.delete(ids=[str(chunk_id)])
    except ValueError:
        pass # If ID doesn't exist, ignore
