from typing import List, Optional, TypedDict


class AgentState(TypedDict):
    question: str
    plan: str
    documents: List[str]
    sql_result: Optional[str]
    code_result: Optional[str]
    answer: str
    steps: List[str]
    revisions: int
