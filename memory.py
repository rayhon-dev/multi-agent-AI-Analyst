from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client.http.models import Distance, VectorParams

from config import EMBEDDING_MODEL, GEMINI_API_KEY, PROXY_BASE_URL
from qdrant_store import get_client
from state import AgentState

COLLECTION_NAME = "memory"
TOP_K = 3

_embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=GEMINI_API_KEY, base_url=PROXY_BASE_URL)
_client = get_client()

if not _client.collection_exists(COLLECTION_NAME):
    _dimension = len(_embeddings.embed_query("dimension probe"))
    _client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=_dimension, distance=Distance.COSINE),
    )

_vectorstore = QdrantVectorStore(client=_client, collection_name=COLLECTION_NAME, embedding=_embeddings)


def retrieve_past_turns(question: str, k: int = TOP_K) -> list:
    if _client.count(COLLECTION_NAME).count == 0:
        return []
    return [doc.page_content for doc in _vectorstore.similarity_search(question, k=k)]


def add_turn(question: str, answer: str) -> None:
    _vectorstore.add_texts([f"Q:{question}\nA:{answer}"])


def recall_agent(state: AgentState) -> dict:
    turns = retrieve_past_turns(state["question"])
    return {
        "memory": turns,
        "steps": state["steps"] + [f"memory(recall {len(turns)} turns)"],
    }


def remember_agent(state: AgentState) -> dict:
    add_turn(state["question"], state["answer"])
    return {"steps": state["steps"] + ["memory(store)"]}
