from common.chroma_utils import get_collection
from common.config import DEFAULT_TOP_K

def retrieve_chunks(account: str, query_vector, top_k=DEFAULT_TOP_K):
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        where={"customer_id": account}
    )
    return results
