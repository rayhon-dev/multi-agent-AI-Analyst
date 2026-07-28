import multiprocessing
import re

from langchain_experimental.tools import PythonREPLTool
from langchain_openai import ChatOpenAI

from config import GEMINI_API_KEY, LLM_MODEL_LITE, PROXY_BASE_URL
from state import AgentState

TIMEOUT_SECONDS = 5

_llm = ChatOpenAI(model=LLM_MODEL_LITE, api_key=GEMINI_API_KEY, base_url=PROXY_BASE_URL, temperature=0)


def _strip_fences(text: str) -> str:
    return re.sub(r"^```(?:python)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE).strip()


def _run_in_process(code: str, queue: multiprocessing.Queue) -> None:
    tool = PythonREPLTool()
    try:
        queue.put(("ok", tool.run(code)))
    except Exception as exc:
        queue.put(("error", str(exc)))


def _run_sandboxed(code: str, timeout: int = TIMEOUT_SECONDS) -> str:
    queue: multiprocessing.Queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=_run_in_process, args=(code, queue))
    process.start()
    process.join(timeout)

    if process.is_alive():
        process.terminate()
        process.join()
        return f"[timed out after {timeout}s]"

    if queue.empty():
        return "[process crashed with no output]"

    status, output = queue.get()
    return output.strip() if status == "ok" else f"[error] {output}"


def code_agent(state: AgentState) -> dict:
    prompt = (
        f"Write Python code that answers this question:\n{state['question']}\n\n"
        "The code must end by calling print() on the final computed answer. "
        "Return Python code only, no explanation, no markdown fences."
    )
    code = _strip_fences(_llm.invoke(prompt).content)

    result = _run_sandboxed(code)

    return {
        "code_result": result,
        "steps": state["steps"] + ["code"],
    }
