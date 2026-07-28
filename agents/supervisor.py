from typing import Literal

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from config import GEMINI_API_KEY, LLM_MODEL_FLASH, PROXY_BASE_URL
from state import AgentState

_llm = ChatOpenAI(model=LLM_MODEL_FLASH, api_key=GEMINI_API_KEY, base_url=PROXY_BASE_URL, temperature=0)


class Route(BaseModel):
    resolved_question: str = Field(
        description="If the question depends on an earlier turn (e.g. 'and last year?', "
        "a pronoun, or an implicit comparison), rewrite it as a fully self-contained "
        "question using the past turns provided. Otherwise copy the question unchanged."
    )
    next: Literal["retriever", "web", "data", "code", "finish"] = Field(
        description="Which specialist should run next, or 'finish' once enough evidence has "
        "been gathered to answer the question."
    )


_structured_llm = _llm.with_structured_output(Route)


def supervisor(state: AgentState) -> dict:
    is_first_call = len(state["steps"]) == 0

    prompt = (
        f"Question: {state['question']}\n"
        f"Relevant past Q&A turns (may be empty): {state['memory']}\n"
        f"Steps taken so far: {state['steps']}\n"
        f"Documents collected: {len(state['documents'])}\n"
        f"SQL result so far: {state['sql_result']}\n"
        f"Code result so far: {state['code_result']}\n\n"
        "First, mentally list each distinct sub-question inside the question above "
        "(a question can ask for more than one thing at once, e.g. a count AND a reason). "
        "Do not choose 'finish' until every sub-question has matching evidence in "
        "documents / SQL result / code result — a sub-question about documents, FAQs, "
        "policies, or 'why' needs retriever evidence; a count/average/aggregate needs SQL "
        "or code evidence.\n\n"
        "Decide the next agent to run:\n"
        "- retriever: search the company's own documents\n"
        "- web: search the internet\n"
        "- data: query the SQL database (counts, aggregates, 'how many' questions)\n"
        "- code: run Python for calculations\n"
        "- finish: every sub-question above already has matching evidence\n"
        "Do not repeat an agent that already ran unless more evidence is genuinely needed."
    )
    route = _structured_llm.invoke(prompt)
    next_agent = route.next

    # gemini-flash-lite sometimes re-picks an agent that already ran despite the
    # prompt stating it did; enforce "each specialist runs at most once" in code
    # rather than trusting the model's self-restraint, so a weak routing call
    # can't turn into an infinite loop.
    already_ran = any(s == next_agent or s.startswith(f"{next_agent}(") for s in state["steps"])
    if next_agent != "finish" and already_ran:
        next_agent = "finish"

    updates = {
        "plan": next_agent,
        "steps": state["steps"] + [f"supervisor→{next_agent}"],
    }
    # Only rewrite the question once, at the start of a run — every later
    # supervisor call in the same run should keep operating on that same
    # resolved question rather than risk it drifting turn to turn.
    if is_first_call:
        updates["question"] = route.resolved_question
    return updates
