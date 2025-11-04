# # # D:\CUE_\api\main.py
# # from fastapi import FastAPI, HTTPException
# # from fastapi.middleware.cors import CORSMiddleware
# # from fastapi.responses import JSONResponse
# # from urllib.parse import unquote
# # import chromadb, traceback, os, re

# # app = FastAPI(title="CUE Iteration-1 API")
# # app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# # CHROMA_PATH = r"D:\CUE_\chromadb_persist"   # absolute, avoids CWD issues
# # COLLECTION  = "cue_chunks"

# # def get_collection():
# #     client = chromadb.PersistentClient(path=CHROMA_PATH)
# #     return client.get_collection(COLLECTION)

# # @app.get("/health")
# # def health():
# #     return {"ok": True}

# # @app.get("/accounts")
# # def accounts():
# #     col = get_collection()
# #     res = col.get(include=["metadatas"], limit=100000)
# #     labels = sorted({
# #         (m.get("account_id") or m.get("customer_id"))
# #         for m in res["metadatas"]
# #         if (m.get("account_id") or m.get("customer_id"))
# #     })
# #     return {"accounts": labels}

# # @app.get("/brief/{label}")
# # def brief(label: str):
# #     # import here to avoid circular imports during app startup
# #     from scripts.generate_brief import generate_brief

# #     label = unquote(label)
# #     try:
# #         print(f"⚙️ Generating brief for: {label}")
# #         data = generate_brief(label)  # your function renamed correctly
# #         if not data or not data.get("markdown"):
# #             raise HTTPException(status_code=404, detail=f"No recent evidence for '{label}'.")
# #         print("✅ Brief generation complete.")
# #         return data
# #     except HTTPException:
# #         raise
# #     except Exception as e:
# #         print("❌ ERROR in /brief:")
# #         traceback.print_exc()
# #         return JSONResponse(
# #             status_code=500,
# #             content={"detail": f"{e.__class__.__name__}: {e}"}
# #         )



# from fastapi import FastAPI, Query
# from pydantic import BaseModel
# from typing import List
# from common.retriever import retrieve_chunks
# from common.summarizer import generate_summary
# from common.risk_logic import assess_risk_level
# from openai import OpenAI
# from common.config import LLM_MODEL, OPENAI_API_KEY

# app = FastAPI(title="CUE Iteration 2 API")
# client = OpenAI(api_key=OPENAI_API_KEY)

# class BriefResponse(BaseModel):
#     summary: str
#     risk_level: str
#     sources: List[str]

# @app.get("/brief/{account}", response_model=BriefResponse)
# async def get_brief(account: str, query: str = Query(..., description="User question")):
#     """
#     Retrieve relevant chunks for the given account and query,
#     summarize them, and assess risk level.
#     """
#     try:
#         # 🔍 Step 1: Embed query for semantic retrieval
#         query_embed = client.embeddings.create(
#             model="text-embedding-3-small",
#             input=query
#         ).data[0].embedding

#         # 🧠 Step 2: Retrieve top chunks
#         results = retrieve_chunks(account, query_embed, top_k=10)
#         context_chunks = results.get("documents", [[]])[0]
#         sources = results.get("metadatas", [[]])[0]
#         source_paths = [s.get("source_path") for s in sources if s]

#         if not context_chunks:
#             return {"summary": "No relevant information found.", "risk_level": "Low", "sources": []}

#         # ✍️ Step 3: Summarize retrieved chunks
#         summary = generate_summary(context_chunks)

#         # ⚖️ Step 4: Assess risk
#         risk_level = assess_risk_level(summary)

#         return {"summary": summary, "risk_level": risk_level, "sources": source_paths}

#     except Exception as e:
#         return {"summary": f"⚠️ Error: {e}", "risk_level": "Unknown", "sources": []}

# api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict

from common.retriever import SemanticRetriever
from common.summarizer import summarize_answer_v2
from common.config import DEFAULT_TOP_K
from common import risk_logic  # optional, if you want to score risk from the answer
from common.config import CUE_ITERATION, describe
app = FastAPI(title="CUE API – Iteration 2", version="2.0")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "iteration": CUE_ITERATION,
        "config": describe(),
    }

# CORS for local Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = SemanticRetriever(collection_name="cue_chunks")

class AskRequest(BaseModel):
    query: str
    account: Optional[str] = None
    top_k: int = DEFAULT_TOP_K

class AskResponse(BaseModel):
    answer: str
    hits: List[Dict]
    risk: Optional[str] = None

def _norm_account(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    return s.lower().strip().replace(" ", "_")    

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    if not req.query:
        raise HTTPException(status_code=422, detail="query is required")

    hits = retriever.query(query=req.query, account=req.account, top_k=req.top_k)

    # Defensive: if nothing found, say so explicitly.
    if not hits:
        return AskResponse(
            answer="I couldn't find evidence for that in the indexed documents.",
            hits=[],
            risk=None,
        )

    answer = summarize_answer_v2(req.query, hits)

    # Optional: very simple risk score using your existing heuristics (can be improved)
    try:
        risk = risk_logic.score_text(answer)
    except Exception:
        risk = None

    return AskResponse(answer=answer, hits=hits, risk=risk)
