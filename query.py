"""
Milestone 5: Grounded Generation
NJIT CS Professor & Course Unofficial Guide

ask(question) → retrieve top-k chunks → build grounded prompt → Groq LLM → answer + sources

The prompt explicitly restricts the model to retrieved context only.
Source attribution is guaranteed programmatically (not left to the LLM).

Usage (standalone test):
    python query.py "Which professor should I take for CS 288?"
    python query.py "What is the weather like in Newark?"   # should decline
"""

import os
import sys
import argparse

from dotenv import load_dotenv
from groq import Groq

from embed import load_model, get_chroma_collection, retrieve

# ── Config ─────────────────────────────────────────────────────────────────────

load_dotenv()   # loads GROQ_API_KEY from .env

GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_K      = 5
MAX_TOKENS = 512


# ── Source name → readable label ───────────────────────────────────────────────

SOURCE_LABELS = {
    "rmp_cs280_professor":          "Rate My Professors — CS 280 (Bassel Arafeh)",
    "rmp_cs288_professor":          "Rate My Professors — CS 288 (Mohit Dale)",
    "rmp_cs332_professor":          "Rate My Professors — CS 332 (Kamlesh Naik)",
    "rmp_cs350_professor":          "Rate My Professors — CS 350 (Itani & Sohn)",
    "reddit_cs288_professor_choice": "Reddit r/NJTech — Itani or Ding for CS 288?",
    "reddit_good_cs_teachers":      "Reddit r/NJTech — Good CS teachers at NJIT",
    "njit_cs_curriculum_bs":        "NJIT Official Catalog — B.S. CS Curriculum",
    "njit_cs_course_catalog":       "NJIT Official Catalog — Undergrad Course Descriptions",
    "njit_cs_graduate_catalog":     "NJIT Official Catalog — Graduate CS Catalog & Faculty",
    "ratemycourses_njit_cs":        "Rate My Courses — NJIT CS Department",
}

def label(source: str) -> str:
    return SOURCE_LABELS.get(source, source)


# ── Prompt builder ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an unofficial student guide for the NJIT Computer Science department. \
Your job is to answer questions about CS professors, courses, and curriculum using ONLY the \
information provided in the retrieved document excerpts below.

Rules you must follow:
1. Answer ONLY from the provided excerpts. Do not use your general training knowledge about \
universities, professors, or CS courses.
2. If the excerpts do not contain enough information to answer the question, respond with: \
"I don't have enough information on that in my documents."
3. Do not invent, guess, or extrapolate beyond what the excerpts say.
4. Be specific — quote or closely paraphrase what students or official sources actually said.
5. Keep answers concise (3–6 sentences) unless the question genuinely requires more detail.
6. Do NOT add a "Sources:" section — that will be added separately."""


def build_user_message(question: str, hits: list[dict]) -> str:
    """Format retrieved chunks as numbered context blocks, then add the question."""
    context_blocks = []
    for i, hit in enumerate(hits, 1):
        context_blocks.append(
            f"[Excerpt {i} — from {label(hit['source'])}]\n{hit['text']}"
        )

    context_str = "\n\n".join(context_blocks)

    return (
        f"Retrieved document excerpts:\n\n"
        f"{context_str}\n\n"
        f"---\n\n"
        f"Question: {question}"
    )


# ── LLM call ──────────────────────────────────────────────────────────────────

def generate_answer(question: str, hits: list[dict]) -> str:
    """Call Groq with the grounded prompt and return the answer text."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_key_here":
        raise ValueError(
            "GROQ_API_KEY not set. Copy .env.example → .env and add your key from "
            "https://console.groq.com"
        )

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system",  "content": SYSTEM_PROMPT},
            {"role": "user",    "content": build_user_message(question, hits)},
        ],
        max_tokens=MAX_TOKENS,
        temperature=0.2,   # low temperature = more faithful, less creative
    )

    return response.choices[0].message.content.strip()


# ── Source deduplication ───────────────────────────────────────────────────────

def dedupe_sources(hits: list[dict]) -> list[str]:
    """Return unique source labels in the order they appear in results."""
    seen = []
    for hit in hits:
        lbl = label(hit["source"])
        if lbl not in seen:
            seen.append(lbl)
    return seen


# ── Main ask() function ────────────────────────────────────────────────────────

# Module-level singletons so Gradio doesn't reload them on every call
_model      = None
_collection = None

def _load_singletons():
    global _model, _collection
    if _model is None:
        _model = load_model()
    if _collection is None:
        _collection = get_chroma_collection(reset=False)
        if _collection.count() == 0:
            raise RuntimeError(
                "ChromaDB collection is empty. "
                "Run `python ingest.py` then `python embed.py` first."
            )


def ask(question: str, k: int = TOP_K) -> dict:
    """
    End-to-end RAG pipeline.

    Returns:
        {
            "answer":   str,          # grounded LLM response
            "sources":  list[str],    # deduplicated readable source labels
            "hits":     list[dict],   # raw retrieval results (for debugging)
        }
    """
    _load_singletons()

    # 1. Retrieve
    hits = retrieve(question, _model, _collection, k=k)

    # 2. Generate (grounded)
    answer = generate_answer(question, hits)

    # 3. Build source list programmatically (not from LLM output)
    sources = dedupe_sources(hits)

    return {
        "answer":  answer,
        "sources": sources,
        "hits":    hits,
    }


# ── CLI test mode ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="NJIT CS Guide — ask a grounded question"
    )
    parser.add_argument("question", nargs="?", help="Question to ask")
    parser.add_argument("--k", type=int, default=TOP_K, help="Number of chunks to retrieve")
    args = parser.parse_args()

    question = args.question
    if not question:
        # Default test question if none provided
        question = "Which professor should I take for CS 288?"

    print(f"\nQuestion: {question}\n")
    print("Retrieving and generating...\n")

    result = ask(question, k=args.k)

    print("=" * 65)
    print("ANSWER:")
    print("=" * 65)
    print(result["answer"])
    print()
    print("SOURCES:")
    for src in result["sources"]:
        print(f"  • {src}")

    # Debug: show retrieval distances
    print("\nRETRIEVAL DISTANCES (for debugging):")
    for i, hit in enumerate(result["hits"], 1):
        print(f"  [{i}] {hit['distance']:.4f}  {hit['source']}")


if __name__ == "__main__":
    main()
