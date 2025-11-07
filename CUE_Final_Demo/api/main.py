# # from fastapi import FastAPI, HTTPException
# # from fastapi.middleware.cors import CORSMiddleware
# # from fastapi.responses import JSONResponse
# # from urllib.parse import unquote
# # from pathlib import Path
# # import chromadb, traceback

# # app = FastAPI(title="CUE Iteration-1 API")

# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )

# # CHROMA_PATH = r"D:\CUE_\chromadb_persist"
# # COLLECTION = "cue_chunks"

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
# #     from scripts.generate_brief import generate_brief

# #     label = unquote(label)
# #     try:
# #         print(f"⚙️ Generating brief for: {label}")
# #         data = generate_brief(label)
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

# # @app.get("/trends")
# # def trends():
# #     """Expose aggregated trends.json for the UI Trends tab."""
# #     root = Path(__file__).resolve().parents[1]
# #     trends_path = root / "data" / "metrics" / "trends.json"
# #     if not trends_path.exists():
# #         return {"trends": []}
# #     try:
# #         data = trends_path.read_text(encoding="utf-8")
# #         return {"trends": json.loads(data)}
# #     except Exception as e:
# #         return JSONResponse(
# #             status_code=500,
# #             content={"detail": f"Failed to read trends: {e}"}
# #         )



# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from urllib.parse import unquote
# from pathlib import Path
# import chromadb, traceback, json  # 👈 add json here

# app = FastAPI(title="CUE Iteration-1 API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# CHROMA_PATH = r"D:\CUE_\chromadb_persist"
# COLLECTION = "cue_chunks"

# def get_collection():
#     client = chromadb.PersistentClient(path=CHROMA_PATH)
#     return client.get_collection(COLLECTION)

# @app.get("/health")
# def health():
#     return {"ok": True}

# @app.get("/accounts")
# def accounts():
#     col = get_collection()
#     res = col.get(include=["metadatas"], limit=100000)
#     labels = sorted({
#         (m.get("account_id") or m.get("customer_id"))
#         for m in res["metadatas"]
#         if (m.get("account_id") or m.get("customer_id"))
#     })
#     return {"accounts": labels}

# @app.get("/brief/{label}")
# def brief(label: str):
#     from scripts.generate_brief import generate_brief

#     label = unquote(label)
#     try:
#         print(f"⚙️ Generating brief for: {label}")
#         data = generate_brief(label)
#         if not data or not data.get("markdown"):
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"No recent evidence for '{label}'."
#             )
#         print("✅ Brief generation complete.")
#         return data
#     except HTTPException:
#         raise
#     except Exception as e:
#         print("❌ ERROR in /brief:")
#         traceback.print_exc()
#         return JSONResponse(
#             status_code=500,
#             content={"detail": f"{e.__class__.__name__}: {e}"}
#         )

# @app.get("/trends")
# def trends():
#     """Expose aggregated trends.json for the UI Trends tab."""
#     try:
#         # project root (.. from /api/main.py)
#         root = Path(__file__).resolve().parent.parent
#         trends_path = root / "data" / "metrics" / "trends.json"

#         print(f"[TRENDS] Looking for: {trends_path}")
#         print(f"[TRENDS] Exists? {trends_path.exists()}")

#         if not trends_path.exists():
#             # No trends yet -> empty list, UI shows friendly text
#             return {"trends": []}

#         with trends_path.open("r", encoding="utf-8") as f:
#             data = json.load(f)

#         # Normalize shapes
#         if isinstance(data, dict):
#             data = [data]
#         if not isinstance(data, list):
#             raise ValueError("trends.json must be a JSON array or object")

#         return {"trends": data}

#     except Exception as e:
#         traceback.print_exc()
#         return JSONResponse(
#             status_code=500,
#             content={"detail": f"Failed to read trends: {e}"}
#         )


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from urllib.parse import unquote
from pathlib import Path
from pydantic import BaseModel
from openai import OpenAI

import chromadb
import traceback
import json
import os

app = FastAPI(title="CUE Iteration-1 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CHROMA_PATH = r"D:\CUE_\chromadb_persist"
COLLECTION = "cue_chunks"


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
    from scripts.generate_brief import generate_brief

    label = unquote(label)
    try:
        print(f"⚙️ Generating brief for: {label}")
        data = generate_brief(label)
        if not data or not data.get("markdown"):
            raise HTTPException(
                status_code=404,
                detail=f"No recent evidence for '{label}'."
            )
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


@app.get("/trends")
def trends():
    """Expose aggregated trends.json for the UI Trends tab."""
    try:
        root = Path(__file__).resolve().parent.parent
        trends_path = root / "data" / "metrics" / "trends.json"

        print(f"[TRENDS] Looking for: {trends_path}")
        print(f"[TRENDS] Exists? {trends_path.exists()}")

        if not trends_path.exists():
            return {"trends": []}

        with trends_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            raise ValueError("trends.json must be a JSON array or object")

        return {"trends": data}

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to read trends: {e}"}
        )

@app.post("/ask_portfolio")
def ask_portfolio(req: dict):
    """
    Handles portfolio-level questions like:
    - "Which of our accounts are at risk?"
    - "Who is high risk this week?"
    """
    import json
    from pathlib import Path

    try:
        trends_path = Path(__file__).resolve().parents[1] / "data" / "metrics" / "trends.json"
        data = json.loads(trends_path.read_text(encoding="utf-8"))

        # Identify high/medium risk accounts
        risky = [r for r in data if r.get("risk_level", "").lower() in ["high", "medium"]]

        if not risky:
            return {"answer": "All accounts are currently stable. No high-risk clients detected."}

        lines = [f"- {r['account']}: {r['risk_level']}" for r in risky]
        summary = (
            f"There are {len(risky)} accounts showing elevated risk:\n" +
            "\n".join(lines)
        )

        return {
            "answer": summary,
            "high_risk_accounts": risky
        }

    except Exception as e:
        return {"answer": f"Failed to analyze portfolio: {e}"}









# ---------- ALERTS (for 'Which accounts are at risk?') ----------

@app.get("/alerts")
def alerts():
    """
    Return accounts that look risky based on trends.json.
    Used to quickly answer: 'Which key accounts are at risk, and why?'.
    """
    try:
        root = Path(__file__).resolve().parent.parent
        trends_path = root / "data" / "metrics" / "trends.json"

        if not trends_path.exists():
            return {"alerts": []}

        with trends_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            data = [data]

        alerts = []
        for row in data:
            level = (row.get("risk_level") or "").lower()
            if level in ("high", "medium"):
                alerts.append({
                    "account": row.get("account"),
                    "risk_level": row.get("risk_level"),
                    "coverage_ratio": row.get("coverage_ratio"),
                    "guardrails_ok": row.get("guardrails_ok"),
                    "ts": row.get("ts"),
                })

        return {"alerts": alerts}

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to read alerts: {e}"}
        )


# ---------- Ask CUE (chat-style Q&A, grounded in context) ----------

class AskRequest(BaseModel):
    account: str
    question: str


@app.post("/ask")
def ask_cue(req: AskRequest):
    """
    Q&A endpoint for the Ask CUE panel.
    Answers ONLY from retrieved context for the given account,
    with an exec-facing explanation.
    """
    from scripts.generate_brief import retrieve_context

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not set on the server."
        )

    ctx, _ = retrieve_context(req.account)
    if not ctx.strip():
        raise HTTPException(
            status_code=404,
            detail=f"No context found for '{req.account}'."
        )

    system_msg = (
        "You are CUE, an executive assistant for customer health. "
        "Answer ONLY using the CONTEXT provided. "
        "Be concise, tie your answer to: (1) risk, (2) actions/commitments, "
        "or (3) trend direction. Include file-style citations in [..]."
    )

    client = OpenAI(api_key=openai_key)

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_msg},
                {
                    "role": "user",
                    "content": f"CONTEXT:\n{ctx}\n\nQUESTION:\n{req.question}",
                },
            ],
        )
        answer = completion.choices[0].message.content.strip()
        return {"answer": answer}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Ask CUE failed: {e}"
        )



