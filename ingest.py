"""
Milestone 3: Document Ingestion and Chunking Pipeline
NJIT CS Professor & Course Unofficial Guide

Pipeline: Load documents → Clean text → Chunk (500 chars, 100 overlap) → Save chunks

Usage:
    python ingest.py              # Run pipeline, print stats and 5 sample chunks
    python ingest.py --verbose    # Print all chunk text
"""

import os
import re
import json
import random
import argparse


# ── Configuration ────────────────────────────────────────────────────────────

DOCUMENTS_DIR = "documents"
CHUNKS_OUTPUT  = "chunks.json"

CHUNK_SIZE    = 500   # characters (matches planning.md spec)
CHUNK_OVERLAP = 100   # characters (matches planning.md spec)
MIN_CHUNK_LEN = 50    # filter out tiny fragments


# ── Text cleaning ─────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Remove boilerplate and normalize whitespace.
    Keeps: substantive content (reviews, course descriptions, curriculum info).
    Removes: HTML artifacts, nav menus, repeated headers, markdown link syntax.
    """
    # Remove markdown-style links but keep the link text: [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Remove bare URLs
    text = re.sub(r'https?://\S+', '', text)

    # Remove HTML entities
    text = text.replace('&amp;', '&').replace('&nbsp;', ' ').replace('&lt;', '<') \
               .replace('&gt;', '>').replace('&#39;', "'").replace('&quot;', '"')

    # Remove lines that are pure navigation/boilerplate
    boilerplate_patterns = [
        r'^Skip to Content$',
        r'^AZ Index$',
        r'^Catalog Home$',
        r'^Search Catalog$',
        r'^Print Options$',
        r'^Catalog Navigation$',
        r'^Back to Top$',
        r'^Cancel$',
        r'^Send Page to Printer$',
        r'^Download Page \(PDF\)',
        r'^Print this page\.',
        r'University Heights Newark',
        r'Contact Us',
        r'Maps & Directions',
        r'NJIT on Facebook',
        r'NJIT on Twitter',
        r'NJIT on YouTube',
        r'NJIT on Flickr',
        r'^\* \[',        # markdown list nav items
        r'^\- \[',        # markdown list nav items
        r'^\+ \[',        # markdown list nav items
        r'^SOURCE:',      # our own source header lines (preserve separately via metadata)
        r'^URL:',
        r'^STATUS:.*MANUAL ENTRY',
        r'^INSTRUCTIONS:',
        r'^PASTE CONTENT HERE:',
        r'^\[Paste ',
        r'^\[to be filled\]',
        r'^Example format',
        r'^---$',
    ]
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append('')
            continue
        skip = False
        for pat in boilerplate_patterns:
            if re.match(pat, stripped, re.IGNORECASE):
                skip = True
                break
        if not skip:
            cleaned_lines.append(stripped)

    text = '\n'.join(cleaned_lines)

    # Collapse multiple blank lines into one
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Normalize whitespace within lines (tabs → space, multiple spaces → one)
    text = re.sub(r'[ \t]+', ' ', text)

    return text.strip()


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_text(text: str, source: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    Split text into overlapping character-level chunks.

    Each chunk dict has:
        text      – the chunk content
        source    – filename the chunk came from
        chunk_id  – "{source}::chunk_{n}"
        char_start – character offset in the cleaned document
        char_end   – character offset end
    """
    chunks = []
    start = 0
    n = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at a sentence boundary (. ! ?) or paragraph (\n\n)
        # to avoid cutting mid-sentence when possible
        if end < len(text):
            # Search backwards up to 80 chars for a good break point
            search_window = text[max(start, end - 80):end]
            # Prefer paragraph break
            para_pos = search_window.rfind('\n\n')
            sent_pos = max(
                search_window.rfind('. '),
                search_window.rfind('! '),
                search_window.rfind('? '),
            )
            if para_pos != -1:
                end = max(start, end - 80) + para_pos + 2
            elif sent_pos != -1:
                end = max(start, end - 80) + sent_pos + 2

        chunk_text_content = text[start:end].strip()

        if len(chunk_text_content) >= MIN_CHUNK_LEN:
            chunks.append({
                "text":       chunk_text_content,
                "source":     source,
                "chunk_id":   f"{source}::chunk_{n}",
                "char_start": start,
                "char_end":   end,
            })
            n += 1

        # Advance by (chunk_size - overlap)
        step = chunk_size - overlap
        start += step

    return chunks


# ── Document loading ──────────────────────────────────────────────────────────

def load_document(filepath: str) -> tuple[str, str]:
    """
    Load a .txt file. Returns (source_name, raw_text).
    Skips placeholder files that haven't been filled in yet.
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        raw = f.read()

    # Skip files that are still just placeholders
    if '[to be filled]' in raw and 'PASTE CONTENT HERE' in raw:
        # Check if there's actual content after the instructions
        marker = 'PASTE CONTENT HERE:'
        idx = raw.find(marker)
        if idx != -1:
            after = raw[idx + len(marker):].strip()
            # Only lines that aren't the example format lines
            real_lines = [
                l for l in after.split('\n')
                if l.strip() and not l.strip().startswith('[') and l.strip() != '---'
            ]
            if not real_lines:
                return None, None  # signal: skip this file

    source_name = os.path.basename(filepath).replace('.txt', '')
    return source_name, raw


def load_all_documents(docs_dir: str) -> list[tuple[str, str]]:
    """Load all .txt files from the documents directory."""
    docs = []
    txt_files = sorted([
        f for f in os.listdir(docs_dir) if f.endswith('.txt') and f != '.gitkeep'
    ])
    for fname in txt_files:
        fpath = os.path.join(docs_dir, fname)
        source, raw = load_document(fpath)
        if source is None:
            print(f"  ⚠  SKIPPED (placeholder not filled): {fname}")
            continue
        docs.append((source, raw))
        print(f"  ✓  Loaded: {fname} ({len(raw):,} chars)")
    return docs


# ── Main pipeline ─────────────────────────────────────────────────────────────

def ingest_and_chunk(docs_dir: str = DOCUMENTS_DIR) -> list[dict]:
    """
    Full pipeline: load → clean → chunk → return list of chunk dicts.
    """
    print(f"\n{'='*60}")
    print("NJIT CS Guide — Document Ingestion & Chunking Pipeline")
    print(f"{'='*60}")
    print(f"\nChunk size:    {CHUNK_SIZE} chars")
    print(f"Overlap:       {CHUNK_OVERLAP} chars")
    print(f"Min chunk len: {MIN_CHUNK_LEN} chars")
    print(f"\nLoading documents from: {docs_dir}/")

    documents = load_all_documents(docs_dir)

    if not documents:
        print("\nNo documents found. Check the documents/ directory.")
        return []

    all_chunks = []
    print(f"\nCleaning and chunking {len(documents)} document(s):")
    print('-' * 60)

    for source, raw_text in documents:
        clean = clean_text(raw_text)
        chunks = chunk_text(clean, source)
        all_chunks.extend(chunks)
        print(f"  {source}")
        print(f"    Raw: {len(raw_text):,} chars → Cleaned: {len(clean):,} chars → {len(chunks)} chunks")

    print(f"\n{'='*60}")
    print(f"TOTAL CHUNKS: {len(all_chunks)}")
    print(f"{'='*60}")

    return all_chunks


def validate_chunks(chunks: list[dict]) -> None:
    """Print diagnostics and 5 random representative chunks."""
    if not chunks:
        print("No chunks to validate.")
        return

    lengths = [len(c['text']) for c in chunks]
    print(f"\nChunk length stats:")
    print(f"  Min:    {min(lengths)} chars")
    print(f"  Max:    {max(lengths)} chars")
    print(f"  Avg:    {sum(lengths)/len(lengths):.0f} chars")

    # Check for problems
    empty     = [c for c in chunks if not c['text'].strip()]
    too_short = [c for c in chunks if len(c['text']) < MIN_CHUNK_LEN]
    html_art  = [c for c in chunks if re.search(r'<[a-zA-Z]+[\s>]', c['text'])]

    print(f"\nQuality checks:")
    print(f"  Empty chunks:     {len(empty)}")
    print(f"  Too-short chunks: {len(too_short)}")
    print(f"  HTML artifacts:   {len(html_art)}")

    if html_art:
        print(f"  ⚠  HTML artifacts found — clean further before embedding")

    # Print 5 representative chunks
    sample_size = min(5, len(chunks))
    samples = random.sample(chunks, sample_size)

    print(f"\n{'='*60}")
    print(f"5 REPRESENTATIVE CHUNKS (random sample)")
    print(f"{'='*60}")
    for i, chunk in enumerate(samples, 1):
        print(f"\n--- Chunk {i} of {sample_size} ---")
        print(f"ID:     {chunk['chunk_id']}")
        print(f"Source: {chunk['source']}")
        print(f"Length: {len(chunk['text'])} chars")
        print(f"Text:\n{chunk['text']}")
        print()


def save_chunks(chunks: list[dict], output_path: str = CHUNKS_OUTPUT) -> None:
    """Save all chunks to a JSON file for use in Milestone 4."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"\nChunks saved to: {output_path} ({len(chunks)} chunks)")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NJIT CS Guide — Ingest and chunk documents")
    parser.add_argument('--verbose', action='store_true', help='Print all chunk text')
    parser.add_argument('--docs-dir', default=DOCUMENTS_DIR, help='Path to documents folder')
    parser.add_argument('--output',   default=CHUNKS_OUTPUT,  help='Output JSON file path')
    args = parser.parse_args()

    random.seed(42)  # reproducible samples

    chunks = ingest_and_chunk(args.docs_dir)

    if chunks:
        validate_chunks(chunks)
        save_chunks(chunks, args.output)

        if args.verbose:
            print(f"\n{'='*60}")
            print("ALL CHUNKS")
            print(f"{'='*60}")
            for c in chunks:
                print(f"\n[{c['chunk_id']}]")
                print(c['text'])
                print()
