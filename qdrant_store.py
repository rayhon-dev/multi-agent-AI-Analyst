from qdrant_client import QdrantClient

from ingest import QDRANT_PATH

# Embedded Qdrant locks its storage path per-client, so every collection used
# within the running app (documents, memory, ...) must share this one client
# rather than each opening its own connection to the same path.
_client = QdrantClient(path=QDRANT_PATH)


def get_client() -> QdrantClient:
    return _client
