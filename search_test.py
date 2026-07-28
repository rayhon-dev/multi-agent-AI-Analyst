from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

from config import EMBEDDING_MODEL, GEMINI_API_KEY, PROXY_BASE_URL
from ingest import COLLECTION_NAME, QDRANT_PATH

QUESTION = "Why do customers churn from Northwind Analytics?"


def main():
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=GEMINI_API_KEY, base_url=PROXY_BASE_URL)
    vectorstore = QdrantVectorStore.from_existing_collection(
        path=QDRANT_PATH,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )

    results = vectorstore.similarity_search(QUESTION, k=3)
    print(f"Top {len(results)} chunks for: {QUESTION!r}\n")
    for i, doc in enumerate(results, 1):
        print(f"--- Result {i} (source: {doc.metadata.get('source')}) ---")
        print(doc.page_content)
        print()


if __name__ == "__main__":
    main()
