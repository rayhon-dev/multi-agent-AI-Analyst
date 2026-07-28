import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ragas 0.4.x unconditionally imports ChatVertexAI from
# langchain_community.chat_models.vertexai, a submodule that no longer ships
# in current langchain-community (only llms.vertexai remains). We never use
# Vertex AI, so stub the missing module before ragas imports it.
if "langchain_community.chat_models.vertexai" not in sys.modules:
    _vertexai_stub = types.ModuleType("langchain_community.chat_models.vertexai")
    _vertexai_stub.ChatVertexAI = type("ChatVertexAI", (), {})
    sys.modules["langchain_community.chat_models.vertexai"] = _vertexai_stub

from datasets import Dataset
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_relevancy, context_precision, faithfulness

from config import EMBEDDING_MODEL, GEMINI_API_KEY, LLM_MODEL_LITE, PROXY_BASE_URL
from graph import build_graph

RECURSION_LIMIT = 15

# 10 questions covering all 4 specialist agent types, each with a reference
# answer derived from data/docs and data/company.db ground truth.
TEST_CASES = [
    {
        "question": "What is Northwind Analytics' refund policy?",
        "reference": "Monthly plans can be canceled anytime with no charge for the following "
        "month, but there are no partial refunds for the current billing period. Annual plans "
        "can get a pro-rated refund within the first 60 days.",
        "agent_type": "retriever",
    },
    {
        "question": "What are the most common reasons customers cancel their Northwind "
        "Analytics subscription?",
        "reference": "Poor integration with their e-commerce platform, price too high for their "
        "order volume, hiring an in-house analyst, and low usage (logging in less than once a "
        "month).",
        "agent_type": "retriever",
    },
    {
        "question": "Which e-commerce platforms does Northwind Analytics integrate with natively?",
        "reference": "Shopify, WooCommerce, and BigCommerce.",
        "agent_type": "retriever",
    },
    {
        "question": "How many customers are currently active?",
        "reference": "9 customers are currently active.",
        "agent_type": "data",
    },
    {
        "question": "How many customers are on the Enterprise plan?",
        "reference": "3 customers are on the Enterprise plan.",
        "agent_type": "data",
    },
    {
        "question": "What is the average order amount across all orders, rounded to two decimals?",
        "reference": "About $258.87.",
        "agent_type": "data",
    },
    {
        "question": "How many customers churned in 2024?",
        "reference": "5 customers churned in 2024.",
        "agent_type": "data",
    },
    {
        "question": "What is the sum of the first 100 positive integers?",
        "reference": "5050",
        "agent_type": "code",
    },
    {
        "question": "If a customer pays $199 per month for 14 months, how much do they pay in total?",
        "reference": "$2786",
        "agent_type": "code",
    },
    {
        "question": "What is LangGraph used for?",
        "reference": "LangGraph is a library for building stateful, multi-agent LLM applications "
        "as graphs, used to orchestrate agent workflows, tool use, and cyclic reasoning loops.",
        "agent_type": "web",
    },
]


def always_ok_critic(state: dict) -> dict:
    return {
        "revisions": state["revisions"],
        "steps": state["steps"] + ["critic→approved (critic disabled)"],
    }


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


def gather_contexts(state: dict) -> list:
    contexts = list(state["documents"])
    if state["sql_result"]:
        contexts.append(state["sql_result"])
    if state["code_result"]:
        contexts.append(state["code_result"])
    return contexts or ["(no evidence gathered)"]


def run_test_cases(graph, cases: list) -> list:
    records = []
    for case in cases:
        state = graph.invoke(build_initial_state(case["question"]), config={"recursion_limit": RECURSION_LIMIT})
        records.append(
            {
                "question": case["question"],
                "reference": case["reference"],
                "agent_type": case["agent_type"],
                "answer": state["answer"],
                "contexts": gather_contexts(state),
                "steps": state["steps"],
            }
        )
    return records


_ragas_llm = LangchainLLMWrapper(
    ChatOpenAI(model=LLM_MODEL_LITE, api_key=GEMINI_API_KEY, base_url=PROXY_BASE_URL, temperature=0)
)
_ragas_embeddings = LangchainEmbeddingsWrapper(
    OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=GEMINI_API_KEY, base_url=PROXY_BASE_URL)
)


def run_ragas(records: list):
    dataset = Dataset.from_dict(
        {
            "question": [r["question"] for r in records],
            "answer": [r["answer"] for r in records],
            "contexts": [r["contexts"] for r in records],
            "ground_truth": [r["reference"] for r in records],
        }
    )
    return evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision],
        llm=_ragas_llm,
        embeddings=_ragas_embeddings,
    )


class JudgeScore(BaseModel):
    score: int = Field(
        description="Integer 1-5: how correct and complete the candidate answer is versus the "
        "reference answer. 5 = fully correct and complete, 1 = wrong or irrelevant."
    )


_judge_llm = ChatOpenAI(
    model=LLM_MODEL_LITE, api_key=GEMINI_API_KEY, base_url=PROXY_BASE_URL, temperature=0
).with_structured_output(JudgeScore)


def judge_answer(question: str, answer: str, reference: str) -> int:
    prompt = (
        f"Question: {question}\n"
        f"Reference answer: {reference}\n"
        f"Candidate answer: {answer}\n\n"
        "Score the candidate answer from 1 (wrong/irrelevant) to 5 (fully correct and complete) "
        "against the reference answer."
    )
    return _judge_llm.invoke(prompt).score


def print_table(title: str, records: list, ragas_result) -> None:
    print(f"\n=== {title} ===")
    header = f"{'#':<3} {'Type':<10} {'Judge':<6} Question"
    print(header)
    print("-" * 90)
    for i, r in enumerate(records, 1):
        print(f"{i:<3} {r['agent_type']:<10} {r['judge_score']:<6} {r['question'][:65]}")

    avg_judge = sum(r["judge_score"] for r in records) / len(records)
    print(f"\nAverage LLM-judge score: {avg_judge:.2f}/5")
    print(f"RAGAS scores: {ragas_result}")


def main():
    graph_with_critic = build_graph(use_memory=False)
    graph_without_critic = build_graph(critic_fn=always_ok_critic, use_memory=False)

    print(f"Running {len(TEST_CASES)} test questions WITH critic...")
    records_with = run_test_cases(graph_with_critic, TEST_CASES)
    for r in records_with:
        r["judge_score"] = judge_answer(r["question"], r["answer"], r["reference"])
    ragas_with = run_ragas(records_with)

    print(f"Running {len(TEST_CASES)} test questions WITHOUT critic (always approve)...")
    records_without = run_test_cases(graph_without_critic, TEST_CASES)
    for r in records_without:
        r["judge_score"] = judge_answer(r["question"], r["answer"], r["reference"])
    ragas_without = run_ragas(records_without)

    print_table("WITH CRITIC", records_with, ragas_with)
    print_table("WITHOUT CRITIC (always approve)", records_without, ragas_without)


if __name__ == "__main__":
    main()
