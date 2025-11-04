import chromadb
from chromadb.config import Settings
from common.config import CHROMA_DB

def get_chroma_client():
    return chromadb.PersistentClient(path=str(CHROMA_DB), settings=Settings(allow_reset=True))

def get_collection(name="cue_chunks"):
    client = get_chroma_client()
    return client.get_or_create_collection(name)
