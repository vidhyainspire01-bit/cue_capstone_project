# common/chroma_utils.py (helper, if missing)
import chromadb
from chromadb.config import Settings
from .config import CHROMA_DB

_client = None
def _client_singleton():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=str(CHROMA_DB), settings=Settings(anonymized_telemetry=False)
        )
    return _client

def get_or_create_collection(name: str):
    return _client_singleton().get_or_create_collection(name)
