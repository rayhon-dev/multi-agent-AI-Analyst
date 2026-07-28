from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

from config import EMBEDDING_MODEL, GEMINI_API_KEY, PROXY_BASE_URL
from ingest import COLLECTION_NAME, QDRANT_PATH
from state import AgentState

_embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=GEMINI_API_KEY, base_url=PROXY_BASE_URL)
_vectorstore = QdrantVectorStore.from_existing_collection(
    path=QDRANT_PATH,
    collection_name=COLLECTION_NAME,
    embedding=_embeddings,
)


def retriever_agent(state: AgentState) -> dict:
    docs = _vectorstore.as_retriever(search_kwargs={"k": 4}).invoke(state["question"])
    return {
        "documents": state["documents"] + [d.page_content for d in docs],
        "steps": state["steps"] + ["retriever"],
    }
