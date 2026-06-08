# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
Domain : NJIT Computer Science Professors Guide
I choose this domain because it's something that's useful to myself and othhers at my college. This knowledge is hard and valuable to find becasue professors are always changing, or teaching new courses. By gathering scattered information from multiple sources, here it's easier to decide on which CS professor to take. 

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | NJIT CS Curriculum|Classes a student needs to take to graduate as a CS major |https://catalog.njit.edu/undergraduate/computing-sciences/computer-science/bs/|
| 2 | NJIT Course Catalog| List of NJIT courses |https://catalog.njit.edu |
| 3 | Rate My Professors - CS280 Professor| Review link for a CS 280 Professor |https://www.ratemyprofessors.com/professor/2626129 |
| 4 | Rate My Professors - CS288 Professor| Link for 288 Prof| https://www.ratemyprofessors.com/professor/2946192|
| 5 | Rate My Professors - CS332 Professor |CS 332 RMP | https://www.ratemyprofessors.com/professor/2755801|
| 6 |Rate My Professors - CS350 Professor | Reviews for a CS350 Professor|https://www.ratemyprofessors.com/professor/2322213 |
| 7 | Reddit|Discussion about which professor to take for cs288 |https://www.reddit.com/r/NJTech/comments/qtkuhj/itani_or_ding_for_cs288/ |
| 8 | Rate my course|Ratings of NJIT CS courses |https://www.ratemycourses.io/njit/department/cs |
| 9 | NJIT CS Graduate Catalog| Advanced CS courses + faculty + research areas| https://catalog.njit.edu/graduate/computing-sciences/computer-science/|
| 10 | Reddit|Thread about good CS teachers at NJIT |https://www.reddit.com/r/NJTech/comments/ivuujj/any_good_cs_teachers_at_njit/|

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size: 500**

**Overlap: 100**

**Reasoning: Since most of the documents will be about reviews, I feel like 500 character chunk is enough to get the whole context of the review. The 100 chunnks overlap is to make sure details that appear at the boundary of the chunks would not be lost. **

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:sentence-transformers/all-MiniLM-L6-v2**

**Top-k:5**

**Production tradeoff reflection: If this were being deployed for real users and cost wasn't an issue, I would pick a higher performance embedding model such as BAAI/bge-large-en-v1.5 or OpenAI’s text-embedding-3-large since they have a better understanding of semantic. This would really show a difference in a guide like this where sentiment and conntext matters since we're dealing wwith courses and professors. The tradeoff compared to these models is that those stronger models would be more accurate, and be able to understand context better compared to the one I plan to use but they also do come with higher cost, increased latenncy and external API dependecny.**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students feel about CS 288's workload?| CS288 is described as a difficult, time-intensive course with heavy programming assignments and fast-paced lectures.|
| 2 | Which professor is prefferd by most students for CS288?| Many students prefer Professor Dale due to clearer explanations, structured lectures, and more manageable pacing compared to other instructors.|
| 3 |What factors make NJIT CS professors receive high ratings | Some factors that make them recieve high ratings are having clear explanations, fair grading, balanced workload, and good pacing.|
| 4 |Which NJIT CS courses are repeatedly described as most difficult and why? | CS288 and CS350 are described as some of the most diffuclt course. This is due to many reasons such as a lot of topics in a short amount of time, hard exams etc. |
| 5 | How do students generally describe CS280 compared to later CS courses?| CS280 is often described as a foundational but challenging course with a heavy programming workload that prepares students for more advanced CS classes.|

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Student reviews are always inconsistent and subjective. Each student has their own experince with the course and professor which might lead to conflicting information. 

2. Important details such as difficulty of the course may be spread throughout the chunks and nnot all be in one chunk which could lead to an incomplete evaluation. 

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->
[ Documents ]
     ↓
[ Ingestion - Python ]
     ↓
[ Chunking - 500 char + overlap ]
     ↓
[ Embeddings - MiniLM ]
     ↓
[ Vector DB - ChromaDB ]
     ↓
[ Retrieval - Top-k=5 ]
     ↓
[ LLM Generation - Groq ]


---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:
Tool :Claude
Input: The Documents table and Chunking Strategy section from this planning doc. Prompt: "Given these sources and a chunk size of 500 characters with 100-character overlap, implement an ingest_and_chunk() function in Python that fetches or reads each document, cleans the text, and splits it into chunks with metadata (source URL, chunk index)."
Expected output: A Python script with ingest_and_chunk() that returns a list of dicts like {"text": ..., "source": ..., "chunk_id": ...}
Verification: Run the script and confirm each source produces multiple non-empty chunks; manually inspect 2–3 chunks per source to confirm overlap is working and chunk length is near 500 characters.**

**Milestone 4 — Embedding and retrieval:
Tool : Claude
Input: The Retrieval Approach section and the chunk schema output from Milestone 3. Prompt: "Using sentence-transformers/all-MiniLM-L6-v2 and ChromaDB, implement embed_and_store(chunks) to embed each chunk and store it with metadata, and retrieve(query, k=5) to return the top-5 most relevant chunks for a given query string."
Expected output: Two functions — one that populates a ChromaDB collection, and one that returns top-k chunks with their source metadata.
Verification: Run each of your 5 evaluation questions through retrieve() and check that the returned chunks are actually about the right professor/course and not off-topic results.**

**Milestone 5 — Generation and interface:
Tool: Claude
Input: The full Architecture diagram, the Evaluation Plan questions, and the output schema from Milestone 4. Prompt: "Using Groq's LLM API and the retrieved chunks as context, implement a generate_answer(query, chunks) function that formats a prompt with the retrieved context and returns a grounded answer. Then build a simple CLI or Gradio interface that takes a user question, calls retrieve(), passes results to generate_answer(), and prints the response with source citations."
Expected output: A generate_answer() function and a working interface (CLI loop or Gradio app) that ties the full pipeline together end to end.
Verification: Run all 5 evaluation questions from your Evaluation Plan through the full pipeline and compare answers against your expected answers. Check that responses cite specific professors or course names rather than giving generic answers.**
