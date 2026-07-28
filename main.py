import sys

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


def main():
    if len(sys.argv) < 2:
        print('Usage: python main.py "<question>"')
        sys.exit(1)

    question = sys.argv[1]
    initial_state = build_initial_state(question)

    config = {"recursion_limit": RECURSION_LIMIT, "callbacks": get_callbacks()}
    final_state = graph.invoke(initial_state, config=config)

    print("=== Steps ===")
    for step in final_state["steps"]:
        print(f"  - {step}")

    print("\n=== Answer ===")
    print(final_state["answer"])


if __name__ == "__main__":
    main()
