from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import EMBEDDING_MODEL, GEMINI_API_KEY, PROXY_BASE_URL

DOCS_DIR = "data/docs"
QDRANT_PATH = "qdrant_storage"
COLLECTION_NAME = "documents"


def load_and_split():
    loader = DirectoryLoader(
        DOCS_DIR, glob="*.txt", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}
    )
    docs = loader.load()
    if not docs:
        raise FileNotFoundError(f"No .txt documents found in {DOCS_DIR}/")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    return splitter.split_documents(docs)


def main():
    chunks = load_and_split()
    print(f"Loaded and split into {len(chunks)} chunks.")

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=GEMINI_API_KEY, base_url=PROXY_BASE_URL)

    QdrantVectorStore.from_documents(
        chunks,
        embedding=embeddings,
        path=QDRANT_PATH,
        collection_name=COLLECTION_NAME,
    )
    print(f"Stored {len(chunks)} chunks in Qdrant collection '{COLLECTION_NAME}' at ./{QDRANT_PATH}/")


if __name__ == "__main__":
    main()
