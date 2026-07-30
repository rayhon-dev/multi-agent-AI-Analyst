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


class SpecialistRoute(BaseModel):
    next: Literal["retriever", "web", "data", "code"] = Field(
        description="Which specialist should run next."
    )


_structured_llm = _llm.with_structured_output(Route)
_structured_llm_specialist_only = _llm.with_structured_output(SpecialistRoute)


def _build_prompt(state: AgentState) -> str:
    return (
        f"Question: {state['question']}\n"
        f"Past Q&A turns retrieved from memory (may be empty, and may be unrelated to this "
        f"question): {state['memory']}\n"
        f"Steps taken so far: {state['steps']}\n"
        f"Documents collected: {len(state['documents'])}\n"
        f"SQL result so far: {state['sql_result']}\n"
        f"Code result so far: {state['code_result']}\n\n"
        "The past Q&A turns above exist only to help you resolve pronouns or implicit "
        "references in the current question (e.g. 'and last year?', 'that customer') via "
        "resolved_question. They are NEVER evidence for the current question, even if one "
        "looks similar or identical to it — always re-verify with a specialist rather than "
        "reusing a past turn's answer.\n\n"
        "First, mentally list each distinct sub-question inside the question above "
        "(a question can ask for more than one thing at once, e.g. a count AND a reason). "
        "Do not choose 'finish' until every sub-question has matching evidence in "
        "documents / SQL result / code result above (not in past Q&A turns) — a sub-question "
        "about documents, FAQs, policies, or 'why' needs retriever evidence; a count/average/"
        "aggregate needs SQL or code evidence.\n\n"
        "Decide the next agent to run:\n"
        "- retriever: search the company's own documents\n"
        "- web: search the internet\n"
        "- data: query the SQL database (counts, aggregates, 'how many' questions)\n"
        "- code: run Python for calculations\n"
        "- finish: every sub-question above already has matching evidence\n"
        "Do not repeat an agent that already ran unless more evidence is genuinely needed."
    )


def supervisor(state: AgentState) -> dict:
    # len(state["steps"]) == 0 would look right but is never true in the memory-enabled
    # graph: recall_agent already appends "memory(recall N turns)" before supervisor's
    # first call. Check for an actual prior routing decision instead.
    is_first_call = not any(s.startswith("supervisor→") for s in state["steps"])

    prompt = _build_prompt(state)
    route = _structured_llm.invoke(prompt)
    next_agent = route.next

    # No specialist has run yet, so there's no real evidence in documents/sql_result/
    # code_result — only recalled memory could have made the model pick "finish" here,
    # which the prompt above explicitly says doesn't count. Force a real specialist
    # choice rather than trusting the model's self-restraint (same reasoning as the
    # "already ran" guard below: the LLM proposes, the code enforces the invariant).
    if is_first_call and next_agent == "finish":
        specialist_route = _structured_llm_specialist_only.invoke(
            prompt + "\n\nAt least one specialist must run before finishing — "
            "choose retriever, web, data, or code."
        )
        next_agent = specialist_route.next

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
