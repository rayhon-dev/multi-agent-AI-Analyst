from agents.code_agent import code_agent
from agents.data_agent import data_agent
from agents.retriever import retriever_agent
from agents.web import web_agent

FAKE_STATE = {
    "question": "Why do customers churn from Northwind Analytics?",
    "plan": "",
    "documents": [],
    "sql_result": None,
    "code_result": None,
    "answer": "",
    "steps": [],
    "revisions": 0,
}

DATA_STATE = {**FAKE_STATE, "question": "How many customers have churned in total?"}
CODE_STATE = {**FAKE_STATE, "question": "What is the sum of the first 50 positive integers?"}


def main():
    print("=== retriever_agent ===")
    result = retriever_agent(FAKE_STATE)
    print(f"steps: {result['steps']}")
    for i, doc in enumerate(result["documents"], 1):
        print(f"--- chunk {i} ---\n{doc[:300]}\n")

    print("=== web_agent ===")
    result = web_agent(FAKE_STATE)
    print(f"steps: {result['steps']}")
    for i, doc in enumerate(result["documents"], 1):
        print(f"--- result {i} ---\n{doc[:300]}\n")

    print("=== data_agent ===")
    result = data_agent(DATA_STATE)
    print(f"steps: {result['steps']}")
    print(result["sql_result"])
    print()

    print("=== code_agent ===")
    result = code_agent(CODE_STATE)
    print(f"steps: {result['steps']}")
    print(result["code_result"])


if __name__ == "__main__":
    main()
