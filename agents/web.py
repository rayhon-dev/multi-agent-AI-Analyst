from tavily import TavilyClient

from config import TAVILY_API_KEY
from state import AgentState


def web_agent(state: AgentState) -> dict:
    if not TAVILY_API_KEY:
        return {
            "documents": state["documents"],
            "steps": state["steps"] + ["web(skipped - no TAVILY_API_KEY)"],
        }

    client = TavilyClient(api_key=TAVILY_API_KEY)
    hits = client.search(state["question"])["results"]
    return {
        "documents": state["documents"] + [h["content"] for h in hits],
        "steps": state["steps"] + ["web"],
    }
