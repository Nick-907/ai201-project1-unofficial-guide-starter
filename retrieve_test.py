"""
Milestone 4: Retrieval Testing
NJIT CS Professor & Course Unofficial Guide

Tests the vector store against 3 of the 5 evaluation plan queries.
Run this AFTER embed.py has populated the ChromaDB collection.

Usage:
    python retrieve_test.py           # Run all 3 test queries
    python retrieve_test.py --k 3     # Change top-k results per query
    python retrieve_test.py --query "your own question here"
"""

import argparse
import sys

# Re-use the helpers from embed.py
from embed import load_model, get_chroma_collection, retrieve, print_results, TOP_K


# ── 3 of the 5 eval-plan queries ──────────────────────────────────────────────
# (from planning.md Evaluation Plan section)

TEST_QUERIES = [
    # Q1 — tests retrieval from RMP CS288 + Reddit sources
    "What do students feel about CS 288's workload?",

    # Q2 — tests professor comparison retrieval (Dale vs Itani)
    "Which professor is preferred by most students for CS 288?",

    # Q4 — tests cross-source retrieval about difficult courses
    "Which NJIT CS courses are repeatedly described as most difficult and why?",
]


# ── Diagnostic helpers ────────────────────────────────────────────────────────

def diagnose(hits: list[dict]) -> str:
    """Return a short diagnostic string about retrieval quality."""
    if not hits:
        return "⚠  No results returned."
    best = hits[0]["distance"]
    avg  = sum(h["distance"] for h in hits) / len(hits)

    if best > 0.6:
        return (
            f"⚠  WEAK — best distance {best:.3f} is above 0.6. "
            "Chunks may be too short or the topic isn't well-covered in your documents."
        )
    elif best > 0.4:
        return (
            f"~  MODERATE — best distance {best:.3f}. "
            "Results are on-topic but not tightly matching. "
            "Consider adding more review content for this topic."
        )
    else:
        return (
            f"✓  GOOD — best distance {best:.3f}, avg {avg:.3f}. "
            "Top results are semantically close to the query."
        )


def full_chunk_view(hits: list[dict], top_n: int = 1) -> None:
    """Print the full text of the top N results for manual inspection."""
    for i, hit in enumerate(hits[:top_n], 1):
        print(f"\n  ── Full text of result [{i}] (source: {hit['source']}) ──")
        print(hit["text"])
        print()


# ── Main test loop ─────────────────────────────────────────────────────────────

def run_tests(queries: list[str], k: int) -> None:
    print("\nLoading model and collection...")
    model      = load_model()
    collection = get_chroma_collection(reset=False)

    count = collection.count()
    if count == 0:
        print(
            "\n⚠  ChromaDB collection is empty.\n"
            "   Run `python ingest.py` then `python embed.py` first.\n"
        )
        sys.exit(1)

    print(f"Collection loaded: {count} embeddings | k={k}\n")

    all_passed = True
    for query in queries:
        hits = retrieve(query, model, collection, k=k)
        print_results(query, hits)
        diag = diagnose(hits)
        print(f"  Diagnosis: {diag}")

        # Show the full top-1 chunk so you can read and judge it manually
        full_chunk_view(hits, top_n=1)

        if hits and hits[0]["distance"] > 0.6:
            all_passed = False

    print("=" * 65)
    if all_passed:
        print("✓  All queries returned a top result with distance < 0.6.")
        print("   Retrieval looks healthy — proceed to Milestone 5.")
    else:
        print("⚠  One or more queries returned weak results (distance > 0.6).")
        print("   Before moving on, check:")
        print("   1. Is the topic covered in your documents/? If not, add more text.")
        print("   2. Are your chunks too short? Try increasing CHUNK_SIZE in ingest.py.")
        print("   3. Run `python ingest.py && python embed.py --reset` after any changes.")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(
        description="NJIT CS Guide — test retrieval against evaluation queries"
    )
    parser.add_argument(
        "--k", type=int, default=TOP_K,
        help=f"Number of results to retrieve per query (default: {TOP_K})"
    )
    parser.add_argument(
        "--query", type=str, default=None,
        help="Run a single custom query instead of the 3 test queries"
    )
    args = parser.parse_args()

    queries = [args.query] if args.query else TEST_QUERIES
    run_tests(queries, k=args.k)


if __name__ == "__main__":
    main()
