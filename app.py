import gradio as gr

from graph import graph
from observability import get_callbacks

RECURSION_LIMIT = 15


def build_initial_state(question: str) -> dict:
    return {
        "question": question,
        "plan": "",
        "documents": [],
        "sql_result": None,
        "code_result": None,
        "answer": "",
        "steps": [],
        "revisions": 0,
        "memory": [],
    }


def format_steps(steps: list) -> str:
    return "\n".join(f"- {s}" for s in steps)


def respond(message, history):
    config = {"recursion_limit": RECURSION_LIMIT, "callbacks": get_callbacks()}
    state = build_initial_state(message)

    final_state = state
    for snapshot in graph.stream(state, config=config, stream_mode="values"):
        final_state = snapshot
        yield f"**Steps so far:**\n{format_steps(final_state['steps'])}\n\n_(working...)_"

    yield (
        f"**Steps:**\n{format_steps(final_state['steps'])}\n\n"
        f"**Answer:**\n{final_state['answer']}"
    )


demo = gr.ChatInterface(
    fn=respond,
    title="Multi-Agent AI Analyst",
    description=(
        "Ask a question. A supervisor routes it to document retrieval, web search, "
        "SQL, and/or Python agents, then a critic verifies the answer before it's returned."
    ),
    examples=[
        "How many customers churned in 2024, and what does the FAQ say about why?",
        "What is Northwind Analytics' refund policy?",
        "What is the sum of the first 100 positive integers?",
    ],
)

if __name__ == "__main__":
    demo.launch()
