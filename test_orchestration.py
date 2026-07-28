from agents.critic import critic
from agents.supervisor import supervisor

BASE_STATE = {
    "question": "",
    "plan": "",
    "documents": [],
    "sql_result": None,
    "code_result": None,
    "answer": "",
    "steps": [],
    "revisions": 0,
}

DATA_QUESTION_STATE = {**BASE_STATE, "question": "How many customers have churned in total?"}
RETRIEVER_QUESTION_STATE = {**BASE_STATE, "question": "Why do customers churn from Northwind Analytics?"}

# Real evidence says 6 churned; the drafted answer deliberately contradicts it.
WRONG_ANSWER_STATE = {
    **BASE_STATE,
    "question": "How many customers have churned in total?",
    "sql_result": "SELECT count(*) FROM customers WHERE status = 'churned';\n→ [(6,)]",
    "answer": "12 customers have churned in total.",
}


def main():
    print("=== supervisor: expect 'data' ===")
    result = supervisor(DATA_QUESTION_STATE)
    print(f"plan: {result['plan']}")
    print(f"steps: {result['steps']}\n")

    print("=== supervisor: expect 'retriever' ===")
    result = supervisor(RETRIEVER_QUESTION_STATE)
    print(f"plan: {result['plan']}")
    print(f"steps: {result['steps']}\n")

    print("=== critic: deliberately wrong answer vs real evidence, expect ok=False ===")
    result = critic(WRONG_ANSWER_STATE)
    print(f"revisions: {WRONG_ANSWER_STATE['revisions']} -> {result['revisions']}")
    print(f"steps: {result['steps']}")


if __name__ == "__main__":
    main()
