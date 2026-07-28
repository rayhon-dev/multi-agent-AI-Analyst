import re

from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI

from config import GEMINI_API_KEY, LLM_MODEL_LITE, PROXY_BASE_URL
from state import AgentState

DB_URI = "sqlite:///data/company.db"

_db = SQLDatabase.from_uri(DB_URI)
_llm = ChatOpenAI(model=LLM_MODEL_LITE, api_key=GEMINI_API_KEY, base_url=PROXY_BASE_URL, temperature=0)


def _strip_fences(text: str) -> str:
    return re.sub(r"^```(?:sql)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE).strip()


def data_agent(state: AgentState) -> dict:
    prompt = (
        f"You are a SQLite expert. Schema:\n{_db.get_table_info()}\n\n"
        f"Relevant past Q&A turns (may be empty): {state['memory']}\n\n"
        "Write ONE read-only SQLite SELECT query that answers this question:\n"
        f"{state['question']}\n\n"
        "If the question depends on a past turn above (e.g. 'and last year?' refers back "
        "to a metric and time period asked about earlier), resolve that dependency yourself "
        "before writing the query.\n\n"
        "Rules:\n"
        "- Only select real columns from the schema above. Never invent, hardcode, or fabricate "
        "a string literal to stand in for data that isn't actually stored in a column.\n"
        "- If part of the question asks for something this schema cannot answer (e.g. a "
        "qualitative reason, an opinion, or free text not stored in any column), write a query "
        "that answers only the part the schema CAN answer and ignore the rest — never invent "
        "an answer for the part you can't query.\n"
        "Return SQL only, no explanation, no markdown fences."
    )
    sql = _strip_fences(_llm.invoke(prompt).content)

    # Read-only guard: never run anything but a SELECT against this database.
    if not sql.lower().startswith("select"):
        return {
            "sql_result": f"REJECTED (query was not a read-only SELECT): {sql}",
            "steps": state["steps"] + ["data(sql)-rejected"],
        }

    try:
        result = _db.run(sql)
    except Exception as exc:
        return {
            "sql_result": f"{sql}\n→ ERROR: {exc}",
            "steps": state["steps"] + ["data(sql)-error"],
        }

    return {
        "sql_result": f"{sql}\n→ {result}",
        "steps": state["steps"] + ["data(sql)"],
    }
