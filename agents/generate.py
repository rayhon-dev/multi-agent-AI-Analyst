from langchain_openai import ChatOpenAI

from config import GEMINI_API_KEY, LLM_MODEL_LITE, PROXY_BASE_URL
from state import AgentState

_llm = ChatOpenAI(model=LLM_MODEL_LITE, api_key=GEMINI_API_KEY, base_url=PROXY_BASE_URL, temperature=0)


def generate_agent(state: AgentState) -> dict:
    prompt = (
        f"Question: {state['question']}\n\n"
        f"Evidence — documents:\n{state['documents']}\n\n"
        f"Evidence — SQL result: {state['sql_result']}\n"
        f"Evidence — code result: {state['code_result']}\n\n"
        "Write a clear, direct answer to the question using only the evidence above. "
        "If evidence is missing for part of the question, say so explicitly rather than guessing."
    )
    answer = _llm.invoke(prompt).content
    return {
        "answer": answer,
        "steps": state["steps"] + ["generate"],
    }
