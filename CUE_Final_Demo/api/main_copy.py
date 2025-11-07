# D:\CUE_\api\main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from urllib.parse import unquote
import chromadb, traceback, os, re

app = FastAPI(title="CUE Iteration-1 API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CHROMA_PATH = r"D:\CUE_\chromadb_persist"   # absolute, avoids CWD issues
COLLECTION  = "cue_chunks"

def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_collection(COLLECTION)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/accounts")
def accounts():
    col = get_collection()
    res = col.get(include=["metadatas"], limit=100000)
    labels = sorted({
        (m.get("account_id") or m.get("customer_id"))
        for m in res["metadatas"]
        if (m.get("account_id") or m.get("customer_id"))
    })
    return {"accounts": labels}

@app.get("/brief/{label}")
def brief(label: str):
    # import here to avoid circular imports during app startup
    from scripts.generate_brief import generate_brief

    label = unquote(label)
    try:
        print(f"⚙️ Generating brief for: {label}")
        data = generate_brief(label)  # your function renamed correctly
        if not data or not data.get("markdown"):
            raise HTTPException(status_code=404, detail=f"No recent evidence for '{label}'.")
        print("✅ Brief generation complete.")
        return data
    except HTTPException:
        raise
    except Exception as e:
        print("❌ ERROR in /brief:")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": f"{e.__class__.__name__}: {e}"}
        )
