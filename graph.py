from langgraph.graph import END, StateGraph

from agents.code_agent import code_agent
from agents.critic import critic
from agents.data_agent import data_agent
from agents.generate import generate_agent
from agents.retriever import retriever_agent
from agents.supervisor import supervisor
from agents.web import web_agent
from state import AgentState

MAX_REVISIONS = 2


def route_after_supervisor(state: AgentState) -> str:
    return "generate" if state["plan"] == "finish" else state["plan"]


def route_after_critic(state: AgentState) -> str:
    if state["revisions"] >= MAX_REVISIONS:
        return "finish"
    return "finish" if state["steps"][-1].startswith("critic→approved") else "revise"


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("supervisor", supervisor)
    g.add_node("retriever", retriever_agent)
    g.add_node("web", web_agent)
    g.add_node("data", data_agent)
    g.add_node("code", code_agent)
    g.add_node("generate", generate_agent)
    g.add_node("critic", critic)

    g.set_entry_point("supervisor")

    g.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "retriever": "retriever",
            "web": "web",
            "data": "data",
            "code": "code",
            "generate": "generate",
        },
    )

    for node in ["retriever", "web", "data", "code"]:
        g.add_edge(node, "supervisor")

    g.add_edge("generate", "critic")

    g.add_conditional_edges("critic", route_after_critic, {"finish": END, "revise": "supervisor"})

    return g.compile()


graph = build_graph()
