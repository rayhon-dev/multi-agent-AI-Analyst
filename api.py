import json
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from graph import graph
from observability import get_callbacks

RECURSION_LIMIT = 15

app = FastAPI(title="Multi-Agent AI Analyst API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str


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


def _stream(question: str):
    config = {"recursion_limit": RECURSION_LIMIT, "callbacks": get_callbacks()}
    state = build_initial_state(question)

    final_state = state
    for snapshot in graph.stream(state, config=config, stream_mode="values"):
        final_state = snapshot
        yield json.dumps({"steps": final_state["steps"], "answer": final_state.get("answer", ""), "done": False}) + "\n"

    yield json.dumps({"steps": final_state["steps"], "answer": final_state["answer"], "done": True}) + "\n"


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(req: ChatRequest):
    return StreamingResponse(_stream(req.question), media_type="application/x-ndjson")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
