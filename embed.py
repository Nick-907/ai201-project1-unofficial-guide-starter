"""
Milestone 4: Embedding + Vector Store
NJIT CS Professor & Course Unofficial Guide

Loads chunks from chunks.json, embeds with all-MiniLM-L6-v2,
stores in ChromaDB, and exposes a retrieve() function.

Usage:
    python embed.py              # Embed all chunks and persist to ./chroma_db/
    python embed.py --reset      # Delete existing collection and re-embed from scratch
"""

import json
import os
import argparse

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings


# ── Configuration ─────────────────────────────────────────────────────────────

CHUNKS_FILE     = "chunks.json"
CHROMA_DIR      = "./chroma_db"        # where ChromaDB persists its files
COLLECTION_NAME = "njit_cs_guide"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K           = 5                    # default number of results to return


# ── Load chunks ───────────────────────────────────────────────────────────────

def load_chunks(path: str = CHUNKS_FILE) -> list[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"'{path}' not found. Run `python ingest.py` first to generate it."
        )
    with open(path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} chunks from {path}")
    return chunks


# ── Embedding model ───────────────────────────────────────────────────────────

def load_model(model_name: str = EMBEDDING_MODEL) -> SentenceTransformer:
    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    print(f"  Model loaded. Max sequence length: {model.max_seq_length} tokens")
    return model


# ── ChromaDB setup ─────────────────────────────────────────────────────────────

def get_chroma_collection(reset: bool = False) -> chromadb.Collection:
    """
    Create (or load) a persistent ChromaDB collection.
    Pass reset=True to wipe and rebuild from scratch.
    """
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"Deleted existing collection: {COLLECTION_NAME}")
        except Exception:
            pass  # collection didn't exist yet

    # get_or_create is idempotent — safe to call on an existing collection
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # cosine similarity (lower = more similar)
    )
    return collection


# ── Embed and store ────────────────────────────────────────────────────────────

def embed_and_store(
    chunks: list[dict],
    model: SentenceTransformer,
    collection: chromadb.Collection,
    batch_size: int = 64,
) -> None:
    """
    Embed each chunk and upsert into ChromaDB.

    ChromaDB requires:
        ids       – unique string ID per document
        documents – the raw text (ChromaDB stores this alongside the embedding)
        embeddings – list of float vectors
        metadatas – list of dicts with arbitrary key/value pairs

    We store: source (filename), char_start, char_end from ingest.py output.
    """
    # Check how many are already stored to allow incremental adds
    existing = collection.count()
    if existing > 0:
        print(f"Collection already has {existing} embeddings.")
        existing_ids = set(collection.get(include=[])["ids"])
        chunks = [c for c in chunks if c["chunk_id"] not in existing_ids]
        if not chunks:
            print("All chunks already embedded. Use --reset to re-embed.")
            return
        print(f"Adding {len(chunks)} new chunks (skipping {existing} already stored).")

    print(f"\nEmbedding {len(chunks)} chunks in batches of {batch_size}...")

    total_batches = (len(chunks) + batch_size - 1) // batch_size
    for batch_num, i in enumerate(range(0, len(chunks), batch_size), 1):
        batch = chunks[i : i + batch_size]

        texts      = [c["text"]     for c in batch]
        ids        = [c["chunk_id"] for c in batch]
        metadatas  = [
            {
                "source":     c["source"],
                "char_start": c.get("char_start", 0),
                "char_end":   c.get("char_end",   0),
            }
            for c in batch
        ]

        # Embed the batch (returns a numpy array of shape [batch_size, 384])
        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        print(f"  Batch {batch_num}/{total_batches} — {len(batch)} chunks stored")

    print(f"\nTotal embeddings in collection: {collection.count()}")


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve(
    query: str,
    model: SentenceTransformer,
    collection: chromadb.Collection,
    k: int = TOP_K,
) -> list[dict]:
    """
    Embed a query string and return the top-k most similar chunks.

    Returns a list of dicts, each with:
        text      – chunk text
        source    – source document filename
        chunk_id  – chunk identifier
        distance  – cosine distance (0 = identical, 2 = opposite; lower is better)
    """
    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    # Unpack the nested ChromaDB response structure
    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "text":     doc,
            "source":   meta.get("source", "unknown"),
            "chunk_id": meta.get("source", "") + f" (dist={dist:.4f})",
            "distance": dist,
        })

    return hits


# ── Pretty-print retrieval results ────────────────────────────────────────────

def print_results(query: str, hits: list[dict]) -> None:
    print(f"\n{'='*65}")
    print(f"QUERY: {query}")
    print(f"{'='*65}")
    for i, hit in enumerate(hits, 1):
        bar = "✓" if hit["distance"] < 0.4 else ("~" if hit["distance"] < 0.6 else "✗")
        print(f"\n  [{i}] {bar} distance={hit['distance']:.4f}  source={hit['source']}")
        # Show first 300 chars of the chunk
        preview = hit["text"][:300].replace("\n", " ")
        if len(hit["text"]) > 300:
            preview += "…"
        print(f"      {preview}")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="NJIT CS Guide — embed chunks and load into ChromaDB"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Delete the existing ChromaDB collection and re-embed everything"
    )
    parser.add_argument(
        "--chunks", default=CHUNKS_FILE,
        help=f"Path to chunks JSON file (default: {CHUNKS_FILE})"
    )
    args = parser.parse_args()

    # ── Step 1: Load chunks
    chunks = load_chunks(args.chunks)

    # ── Step 2: Load model
    model = load_model()

    # ── Step 3: Connect to / create ChromaDB collection
    collection = get_chroma_collection(reset=args.reset)

    # ── Step 4: Embed and store
    embed_and_store(chunks, model, collection)

    print("\nEmbedding complete. Run `python retrieve_test.py` to test retrieval.")
    print(f"ChromaDB persisted to: {CHROMA_DIR}/")


if __name__ == "__main__":
    main()
