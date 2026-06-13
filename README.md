# NJIT CS Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

## Quick Start

```bash
# 1. Activate virtual environment
d:/AI201/.venv/Scripts/Activate.ps1        # Windows PowerShell
# source d:/AI201/.venv/bin/activate       # Mac/Linux

# 2. Install dependencies (first time only)
pip install -r requirements.txt

# 3. Add your Groq API key
copy .env.example .env   # then edit .env and set GROQ_API_KEY=gsk_...

# 4. Build the pipeline
python ingest.py          # chunk documents → chunks.json
python embed.py           # embed → ChromaDB

# 5. Launch the UI
python app.py             # opens http://localhost:7860
```

## Architecture

```
[ 10 source documents in documents/ ]
              ↓
[ ingest.py — clean + chunk (500 chars, 100 overlap) ]
              ↓
[ chunks.json ]
              ↓
[ embed.py — sentence-transformers/all-MiniLM-L6-v2 → ChromaDB ]
              ↓
[ query.py — retrieve top-5 chunks → Groq llama-3.3-70b-versatile ]
              ↓
[ app.py — Gradio web UI at localhost:7860 ]
```

---

## Domain

This system covers the NJIT Computer Science department — specifically CS professors, course difficulty, workload, and curriculum requirements. This knowledge is valuable because official sources like the NJIT catalog only describe course content, not what it's actually like to take those courses. Student experiences (professor grading style, how lectures are paced, which exams are brutal, which professors are approachable) are scattered across Reddit threads, Rate My Professors, and informal word-of-mouth. This guide aggregates all of it in one searchable place.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | NJIT B.S. CS Curriculum | Official catalog | https://catalog.njit.edu/undergraduate/computing-sciences/computer-science/bs/ |
| 2 | NJIT Undergrad Course Catalog | Official catalog | https://catalog.njit.edu/undergraduate/computing-sciences/computer-science/ |
| 3 | NJIT Graduate CS Catalog | Official catalog | https://catalog.njit.edu/graduate/computing-sciences/computer-science/ |
| 4 | Rate My Courses — NJIT CS | Course ratings | https://www.ratemycourses.io/njit/department/cs |
| 5 | Rate My Professors — CS 280 (Bassel Arafeh) | Professor reviews | https://www.ratemyprofessors.com/professor/2626129 |
| 6 | Rate My Professors — CS 288 (Mohit Dale) | Professor reviews | https://www.ratemyprofessors.com/professor/2946192 |
| 7 | Rate My Professors — CS 332 (Kamlesh Naik) | Professor reviews | https://www.ratemyprofessors.com/professor/2755801 |
| 8 | Rate My Professors — CS 350 (Itani & Sohn) | Professor reviews | https://www.ratemyprofessors.com/professor/2322213 |
| 9 | Reddit r/NJTech — Itani or Ding for CS 288? | Student forum | https://www.reddit.com/r/NJTech/comments/qtkuhj/ |
| 10 | Reddit r/NJTech — Any good CS teachers at NJIT? | Student forum | https://www.reddit.com/r/NJTech/comments/ivuujj/ |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 500 characters

**Overlap:** 100 characters

**Why these choices fit your documents:** Most of the documents are composed of individual student reviews — each one being a short, self-contained opinion. A 500-character chunk is large enough to capture the full sentiment of a single review (rating + comment) without bundling unrelated reviews together. The 100-character overlap ensures that key details appearing near a chunk boundary — like a professor's name at the end of one chunk and their course code at the start of the next — are preserved in both chunks and won't be lost during retrieval. Before chunking, documents were cleaned to remove HTML tags, markdown link syntax, and boilerplate navigation lines that don't carry useful information.

**Final chunk count:** Run `python ingest.py` to see the exact count printed to the terminal after processing. Approximately 300–450 chunks depending on document lengths.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `sentence-transformers/all-MiniLM-L6-v2` — a compact, fast model that runs locally with no API cost. It produces 384-dimensional embeddings and handles sentence-level semantic similarity well, which suits short review text.

**Production tradeoff reflection:** If this were deployed for real users and cost wasn't a constraint, I would switch to a higher-capacity model like `BAAI/bge-large-en-v1.5` or OpenAI's `text-embedding-3-large`. These models better capture nuanced sentiment and domain-specific vocabulary — important here because the difference between "tough but fair" and "unfair grader" matters for a professor guide. The tradeoffs are higher latency, larger embedding dimensions (increasing storage and query time), and in the case of OpenAI, an external API dependency. For a low-volume internal tool, the accuracy gain is likely worth those costs.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:** The system prompt instructs the model: *"Answer ONLY from the provided excerpts. Do not use your general training knowledge about universities, professors, or CS courses. If the excerpts do not contain enough information to answer the question, respond with: 'I don't have enough information on that in my documents.' Do not invent, guess, or extrapolate beyond what the excerpts say."* Retrieved chunks are passed as numbered, labeled blocks (e.g., `[Excerpt 1 — from Rate My Professors — CS 288 (Mohit Dale)]`) so the model can see exactly which source each passage comes from.

**How source attribution is surfaced in the response:** Source labels are extracted **programmatically** from the retrieved chunk metadata using `dedupe_sources()` in `query.py` — the LLM does not generate the source list. This guarantees attribution is always accurate and matches what was actually retrieved, regardless of what the model outputs. Sources are displayed in a separate "Retrieved from" panel in the Gradio UI.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students feel about CS 288's workload? | Heavy programming assignments, fast-paced lectures | *[Run the system and paste a short summary here]* | | |
| 2 | Which professor is preferred by most students for CS 288? | Professor Dale — clearer explanations, structured pacing | *[Run the system and paste a short summary here]* | | |
| 3 | What factors make NJIT CS professors receive high ratings? | Clear explanations, fair grading, responsive to students | *[Run the system and paste a short summary here]* | | |
| 4 | Which NJIT CS courses are repeatedly described as most difficult and why? | CS 288 and CS 350 — heavy content coverage, hard exams | *[Run the system and paste a short summary here]* | | |
| 5 | How do students generally describe CS 280 compared to later CS courses? | Foundational but challenging; prepares for advanced work | *[Run the system and paste a short summary here]* | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** "What do other students in the comments say about taking Itani for CS 288?"

**What the system returned:** A response about Itani's overall ratings and general sentiment, but without any specific comments from the Reddit discussion thread.

**Root cause (tied to a specific pipeline stage):** The Reddit thread on Itani vs. Ding for CS 288 was behind a login wall — only the original post was recoverable, not the 8 replies. As a result, the `reddit_cs288_professor_choice.txt` document has almost no content from the comment section. At the **ingestion stage**, very little meaningful text was chunked from this file. At the **retrieval stage**, queries about that thread's discussion pull from RMP reviews instead, which have broader coverage. The gap is a source collection problem, not a pipeline bug.

**What you would change to fix it:** Access Reddit while logged in to capture full comment threads, or supplement with additional Reddit threads about Itani from other semesters. Alternatively, add a `reddit_cs288_itani_reviews.txt` file with manually collected posts from r/NJTech that discuss him directly.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** Having the chunking strategy written down before coding — chunk size 500, overlap 100, with a rationale tied to review-length documents — meant I could give Claude a precise, unambiguous spec when generating `ingest.py`. The output matched exactly what I needed without back-and-forth. The spec also included the chunk schema (`{text, source, chunk_id, char_start, char_end}`), which carried through to `embed.py` and `query.py` without needing to redesign the data structure mid-project.

**One way your implementation diverged from the spec, and why:** The spec listed Rate My Professors and Reddit as standard web sources. In practice, both are JavaScript-rendered or require authentication, making automated fetching impossible. The ingestion pipeline had to be adapted to skip placeholder files (files containing `PASTE CONTENT HERE`) and those sources were filled in manually. The `load_document()` function in `ingest.py` checks for placeholder text and skips incomplete files gracefully, which wasn't part of the original spec but became necessary once source access issues emerged.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1 — Generating `ingest.py`**

- *What I gave the AI:* The Documents table and Chunking Strategy section from `planning.md`, plus a description of the desired output schema (`{text, source, chunk_id, char_start, char_end}`).
- *What it produced:* A complete `ingest.py` with `clean_text()`, `chunk_text()`, `load_document()`, `load_all_documents()`, `ingest_and_chunk()`, `validate_chunks()`, and `save_chunks()`. The cleaning step stripped HTML tags, markdown link syntax, and short boilerplate navigation lines.
- *What I changed or overrode:* Added a check in `load_document()` to skip files containing placeholder text (`PASTE CONTENT HERE` / `[to be filled]`), because several sources couldn't be fetched automatically. This wasn't in the original spec but was necessary once source access limitations became clear.

**Instance 2 — Generating `query.py` grounding logic**

- *What I gave the AI:* The full architecture diagram from `planning.md`, the `retrieve()` function signature from `embed.py`, and the requirement that source attribution must be programmatic (not left to the LLM).
- *What it produced:* A `query.py` with a strict system prompt, numbered excerpt blocks in the user message, and a `dedupe_sources()` function that extracts source labels from chunk metadata rather than from LLM output. Also included a `SOURCE_LABELS` dict mapping file stems to human-readable names.
- *What I changed or overrode:* The initial system prompt was slightly too permissive — it said "prefer the documents" rather than "only use the documents." Updated it to explicitly say "Do not use your general training knowledge" and added the fallback response phrase ("I don't have enough information on that in my documents.") to make refusal behavior consistent.
