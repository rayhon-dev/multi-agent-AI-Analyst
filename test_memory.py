from graph import graph

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


def run(question: str) -> dict:
    return graph.invoke(build_initial_state(question), config={"recursion_limit": RECURSION_LIMIT})


def main():
    print("=== First question ===")
    first = run("How many customers churned in 2024?")
    print(f"asked: How many customers churned in 2024?")
    print(f"steps: {first['steps']}")
    print(f"answer: {first['answer']}\n")

    print("=== Follow-up question (depends on the first turn) ===")
    second = run("And last year?")
    print(f"asked: And last year?")
    print(f"memory recalled: {second['memory']}")
    print(f"resolved question used: {second['question']}")
    print(f"steps: {second['steps']}")
    print(f"answer: {second['answer']}")


if __name__ == "__main__":
    main()
