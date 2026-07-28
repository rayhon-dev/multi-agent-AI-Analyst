from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from config import GEMINI_API_KEY, LLM_MODEL_FLASH, PROXY_BASE_URL
from state import AgentState

_llm = ChatOpenAI(model=LLM_MODEL_FLASH, api_key=GEMINI_API_KEY, base_url=PROXY_BASE_URL, temperature=0)


class Verdict(BaseModel):
    ok: bool = Field(description="True only if the answer is correct AND fully supported by the evidence.")
    reason: str = Field(description="Brief justification for the verdict.")


_structured_llm = _llm.with_structured_output(Verdict)


def critic(state: AgentState) -> dict:
    prompt = (
        f"Question: {state['question']}\n\n"
        f"Evidence — documents: {state['documents']}\n"
        f"Evidence — SQL result: {state['sql_result']}\n"
        f"Evidence — code result: {state['code_result']}\n\n"
        f"Drafted answer: {state['answer']}\n\n"
        "Check the answer sentence by sentence. For EVERY factual claim it makes, find where "
        "that exact fact appears — verbatim or as a clear paraphrase — in the evidence above. "
        "If documents/SQL result/code result are empty or missing, no claim can be attributed to "
        "them. Say not ok if even one claim has no matching evidence, if it contradicts the "
        "evidence, or if it fails to answer every part of the question."
    )
    verdict = _structured_llm.invoke(prompt)
    return {
        "revisions": state["revisions"] + (0 if verdict.ok else 1),
        "steps": state["steps"] + [f"critic→{'approved' if verdict.ok else 'revise'} ({verdict.reason})"],
    }
