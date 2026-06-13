"""
Milestone 5: Gradio Interface
NJIT CS Professor & Course Unofficial Guide

Run:
    python app.py

Then open http://localhost:7860 in your browser.
"""

import gradio as gr
from query import ask


# ── Core handler ──────────────────────────────────────────────────────────────

def handle_query(question: str):
    """Called by Gradio on every button click or Enter press."""
    question = question.strip()
    if not question:
        return "Please enter a question.", ""

    try:
        result = ask(question)
    except RuntimeError as e:
        return str(e), ""
    except ValueError as e:
        return str(e), ""
    except Exception as e:
        return f"Error: {e}", ""

    answer  = result["answer"]
    sources = "\n".join(f"• {s}" for s in result["sources"])
    return answer, sources


# ── Example questions (shown in the UI) ───────────────────────────────────────

EXAMPLES = [
    "Which professor should I take for CS 288 — Dale or Itani?",
    "What do students say about CS 280's workload?",
    "Which NJIT CS courses are considered the most difficult?",
    "What makes a CS professor receive high ratings at NJIT?",
    "How does CS 280 compare to later CS courses like CS 288?",
    "Is CS 350 hard?",
    "What is the best way to study for NJIT CS exams?",
]


# ── Gradio UI ─────────────────────────────────────────────────────────────────

CSS = """
#title { text-align: center; margin-bottom: 0.25rem; }
#subtitle { text-align: center; color: #666; margin-bottom: 1.5rem; font-size: 0.95rem; }
#answer-box textarea { font-size: 0.95rem; line-height: 1.55; }
"""

with gr.Blocks(css=CSS, title="NJIT CS Unofficial Guide") as demo:

    gr.Markdown("# NJIT CS Unofficial Guide", elem_id="title")
    gr.Markdown(
        "Ask questions about CS professors, courses, and curriculum at NJIT. "
        "Answers are grounded in student reviews and official course catalogs.",
        elem_id="subtitle"
    )

    with gr.Row():
        with gr.Column(scale=3):
            question_box = gr.Textbox(
                label="Your question",
                placeholder="e.g. Which professor should I take for CS 288?",
                lines=2,
            )
            ask_btn = gr.Button("Ask", variant="primary")

        with gr.Column(scale=1):
            gr.Markdown("**Example questions:**")
            example_btns = [
                gr.Button(ex, size="sm", variant="secondary") for ex in EXAMPLES
            ]

    with gr.Row():
        answer_box = gr.Textbox(
            label="Answer",
            lines=8,
            interactive=False,
            elem_id="answer-box",
        )

    with gr.Row():
        sources_box = gr.Textbox(
            label="Retrieved from",
            lines=4,
            interactive=False,
        )

    # Wire up submit actions
    ask_btn.click(
        fn=handle_query,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )
    question_box.submit(
        fn=handle_query,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )

    # Each example button fills the question box and triggers a query
    for btn, ex in zip(example_btns, EXAMPLES):
        btn.click(
            fn=lambda q=ex: q,
            outputs=question_box,
        ).then(
            fn=handle_query,
            inputs=question_box,
            outputs=[answer_box, sources_box],
        )

    gr.Markdown(
        "---\n"
        "*Answers are based only on collected student reviews and NJIT's official catalog. "
        "Always verify important decisions with your academic advisor.*"
    )


# ── Launch ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo.launch()
