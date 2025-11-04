# # common/retriever.py
# from typing import List, Dict, Any, Optional
# import chromadb
# from chromadb.config import Settings

# from .config import CHROMA_DB, DEFAULT_TOP_K
# from .chroma_utils import get_or_create_collection  # if you already have it; see note below


# class SemanticRetriever:
#     """
#     Query ChromaDB for semantically relevant chunks.
#     Expects you’ve already embedded and upserted chunks with useful metadata
#     like account/customer identifiers and source paths.
#     """

#     def __init__(self, collection_name: str = "cue_chunks"):
#         # Reuse your helper if you have one; otherwise, create a client directly.
#         try:
#             self.collection = get_or_create_collection(collection_name)
#         except Exception:
#             client = chromadb.PersistentClient(
#                 path=str(CHROMA_DB),
#                 settings=Settings(anonymized_telemetry=False),
#             )
#             self.collection = client.get_or_create_collection(collection_name)

#     def _account_where(self, account: Optional[str]) -> Optional[Dict[str, Any]]:
#         if not account:
#             return None
#         # Be tolerant of different metadata keys used during preprocessing
#         return {
#             "$or": [
#                 {"account": account},
#                 {"account_id": account},
#                 {"customer": account},
#                 {"customer_id": account},
#                 {"doc_account": account},
#             ]
#         }

#     def query(
#         self,
#         query: str,
#         account: Optional[str] = None,
#         top_k: int = DEFAULT_TOP_K,
#     ) -> List[Dict[str, Any]]:
#         """
#         Returns a list of hits: {text, metadata, score}
#         """
#         where = self._account_where(account)

#         results = self.collection.query(
#             query_texts=[query],
#             n_results=top_k,
#             where=where,
#             include=["documents", "metadatas", "distances"],
#         )

#         hits: List[Dict[str, Any]] = []
#         if not results or not results.get("documents"):
#             return hits

#         docs = results["documents"][0]
#         metas = results["metadatas"][0]
#         dists = results.get("distances", [[None] * len(docs)])[0]

#         for doc, meta, dist in zip(docs, metas, dists):
#             hits.append(
#                 {
#                     "text": doc,
#                     "metadata": meta or {},
#                     "score": float(dist) if dist is not None else None,
#                 }
#             )
#         return hits



# common/retriever.py
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from openai import OpenAI

from .config import CHROMA_DB, DEFAULT_TOP_K, EMBED_MODEL, COLLECTION_NAME
from .chroma_utils import get_or_create_collection  # if present; else we'll fallback

_client_oa = OpenAI()

class SemanticRetriever:
    """
    Query ChromaDB for semantically relevant chunks.
    Ensures query embeddings use the SAME model as the indexed docs.
    """

    def __init__(self, collection_name: str = COLLECTION_NAME):
        try:
            self.collection = get_or_create_collection(collection_name)
        except Exception:
            client = chromadb.PersistentClient(
                path=str(CHROMA_DB),
                settings=Settings(anonymized_telemetry=False),
            )
            self.collection = client.get_or_create_collection(collection_name)

    def _embed(self, text: str) -> list[float]:
        resp = _client_oa.embeddings.create(model=EMBED_MODEL, input=[text])
        return resp.data[0].embedding  # 1536-dim for text-embedding-3-small

    def _account_where(self, account: Optional[str]) -> Optional[Dict[str, Any]]:
        if not account:
            return None
        return {
            "$or": [
                {"account": account},
                {"account_id": account},
                {"customer": account},
                {"customer_id": account},
                {"doc_account": account},
            ]
        }

    def query(
        self,
        query: str,
        account: Optional[str] = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> List[Dict[str, Any]]:
        where = self._account_where(account)
        q_vec = self._embed(query)

        results = self.collection.query(
            query_embeddings=[q_vec],            # ✅ use embeddings, not query_texts
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        hits: List[Dict[str, Any]] = []
        if not results or not results.get("documents"):
            return hits

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results.get("distances", [[None] * len(docs)])[0]

        for doc, meta, dist in zip(docs, metas, dists):
            hits.append(
                {
                    "text": doc,
                    "metadata": meta or {},
                    "score": float(dist) if dist is not None else None,
                }
            )
        return hits
