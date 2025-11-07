# # D:\CUE_\scripts\generate_brief.py
# import os, re
# from pathlib import Path
# from datetime import datetime, timedelta, timezone
# from openai import OpenAI
# import chromadb

# # ---------- config ----------
# CHROMA_PATH = r"D:\CUE_\chromadb_persist"   # absolute path (matches api/main.py)
# COLLECTION  = "cue_chunks"
# EMBED_MODEL = "text-embedding-3-small"      # 1536-dim (same model used at upsert)

# BRIEFS = Path("data/briefs")
# BRIEFS.mkdir(parents=True, exist_ok=True)

# # ---------- clients ----------
# KEY = os.getenv("OPENAI_API_KEY")
# if not KEY:
#     raise RuntimeError("OPENAI_API_KEY is not set for the server process.")
# OA = OpenAI(api_key=KEY)

# client = chromadb.PersistentClient(path=CHROMA_PATH)
# col = client.get_collection(COLLECTION)

# # ---------- helpers ----------
# def slugify(s: str) -> str:
#     s = (s or "").strip().lower()
#     s = re.sub(r"&", " and ", s)
#     s = re.sub(r"[^a-z0-9]+", "_", s)
#     return re.sub(r"_+", "_", s).strip("_")

# def _embed(text: str):
#     # Use the same model that wrote the collection (1536-d)
#     return OA.embeddings.create(model=EMBED_MODEL, input=[text]).data[0].embedding

# SYS = """You are a rigorous analyst for Customer Success.
# Only make claims that have evidence in CONTEXT.
# Every bullet must include at least one citation like [data/.../file.docx].
# If evidence is missing, omit the claim.
# Keep it concise and actionable.
# """

# TEMPLATE = """# Customer Brief — {label} (last 30 days)

# ## Risk Level: {level}
# {level_reason}

# ## Top Risks
# {risks}

# ## Open Commitments
# {commits}

# ## Recent Escalations
# {escalations}

# ## Highlights
# {highlights}

# ---

# **Citations**  
# {citations}
# """

# # ---------- retrieval ----------
# def _query(field: str, value: str, k: int = 50):
#     """
#     Your Chroma build requires exactly one top-level operator in `where`.
#     Also, we must query with embeddings to match 1536-d collection.
#     """
#     qvec = _embed("customer status last 30 days")
#     return col.query(query_embeddings=[qvec], n_results=k, where={field: value})

# def retrieve_context(label: str, k: int = 60):
#     # Try label variants across both metadata keys
#     variants = {label, label.strip(), label.lower(), slugify(label)}
#     for field in ("account_id", "customer_id"):
#         for v in variants:
#             try:
#                 res = _query(field, v, k=k)
#             except Exception:
#                 continue
#             if res and res.get("documents") and res["documents"][0]:
#                 ctx_lines, cites = [], set()
#                 for i in range(len(res["ids"][0])):
#                     text = res["documents"][0][i]
#                     meta = (res.get("metadatas") or [[]])[0][i] if res.get("metadatas") else {}
#                     sp = (meta or {}).get("source_path", "UNKNOWN")
#                     ctx_lines.append(f"[{sp}] {text}")
#                     cites.add(sp)
#                 return "\n".join(ctx_lines), "\n".join(sorted(cites))

#     # Last resort: semantic search by label, no filter
#     try:
#         qvec = _embed(label)
#         res = col.query(query_embeddings=[qvec], n_results=k)
#         if res and res.get("documents") and res["documents"][0]:
#             ctx_lines, cites = [], set()
#             for i in range(len(res["ids"][0])):
#                 text = res["documents"][0][i]
#                 meta = (res.get("metadatas") or [[]])[0][i] if res.get("metadatas") else {}
#                 sp = (meta or {}).get("source_path", "UNKNOWN")
#                 ctx_lines.append(f"[{sp}] {text}")
#                 cites.add(sp)
#             return "\n".join(ctx_lines), "\n".join(sorted(cites))
#     except Exception:
#         pass

#     return "", ""

# def _bullets(md: str):
#     return [l[2:].strip() for l in md.splitlines() if l.strip().startswith("-")] or []

# # ---------- main entry ----------
# def generate_brief(label: str):
#     ctx, citations = retrieve_context(label)
#     if not ctx.strip():
#         # Let the API return a clean 404 instead of 500
#         return None

#     r = OA.chat.completions.create(
#         model="gpt-4o-mini",
#         temperature=0.2,
#         messages=[
#             {"role": "system", "content": SYS},
#             {"role": "user", "content":
#                 "CONTEXT:\n" + ctx +
#                 "\n\nWrite short bullets for: Top Risks, Open Commitments, Recent Escalations, Highlights. "
#                 "Start with one-line 'Risk Level' and a one-line reason. Each bullet must include at least one [path] citation."
#              },
#         ],
#     )
#     md = r.choices[0].message.content or ""
#     low = md.lower()
#     level = "Medium"
#     if any(x in low for x in ["p0", "sev", "escalation", "outage", "drop", "decrease", "% drop"]):
#         level = "High"
#     if any(x in low for x in ["renewal confirmed", "adoption up", "positive nps", "% increase"]):
#         level = "Low"

#     out = TEMPLATE.format(
#         label=label,
#         level=level,
#         level_reason="_Auto-assessed from evidence._",
#         risks="\n".join(f"- {b}" for b in _bullets(md)),
#         commits="_(see bullets above)_",
#         escalations="_(see bullets above)_",
#         highlights="_(see bullets above)_",
#         citations=citations or "_(citations included in bullets)_",
#     )
#     (BRIEFS / f"{slugify(label)}.md").write_text(out, encoding="utf-8")
#     return {"account": label, "markdown": out}


# D:\CUE_\scripts\generate_brief.py
import os, re, json
from pathlib import Path
from openai import OpenAI
import chromadb

# ---------- config ----------
CHROMA_PATH = r"D:\CUE_\chromadb_persist"   # absolute path (matches api/main.py)
COLLECTION  = "cue_chunks"
EMBED_MODEL = "text-embedding-3-small"      # 1536-dim (same model used at upsert)

BRIEFS = Path("data/briefs")
BRIEFS.mkdir(parents=True, exist_ok=True)

# ---------- clients ----------
KEY = os.getenv("OPENAI_API_KEY")
if not KEY:
    raise RuntimeError("OPENAI_API_KEY is not set for the server process.")
OA = OpenAI(api_key=KEY)

client = chromadb.PersistentClient(path=CHROMA_PATH)
col = client.get_collection(COLLECTION)

# ---------- helpers ----------
def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"&", " and ", s)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")

def _embed(text: str):
    # Use the same model that wrote the collection (1536-d)
    return OA.embeddings.create(model=EMBED_MODEL, input=[text]).data[0].embedding

SYS = """You are a rigorous analyst for Customer Success.
Only make claims that have evidence in CONTEXT.
Every bullet must include at least one citation like [data/.../file.docx].
If evidence is missing, omit the claim.
Keep it concise and actionable.
"""

# risk signals
NEG_SIGNS = [
    r"\bp0\b", r"\bp1\b", "sev", "escalation", "outage",
    "downtime", "sla breach", "churn", "drop", "decrease", "% drop",
]
POS_SIGNS = ["renewal confirmed", "adoption up", "positive nps", "% increase", "resolved", "mitigated"]

def score_risk(text: str):
    t = text.lower()
    neg = sum(bool(re.search(p, t)) for p in NEG_SIGNS)
    pos = sum(s in t for s in POS_SIGNS)
    score = neg - (0.5 * pos)
    if score >= 2:
        return "High", "Multiple strong negative signals detected (e.g., escalations/P0)."
    if score <= 0:
        return "Low", "No strong negatives; some positive/adoption signals."
    return "Medium", "Mixed signals; monitor and follow up on open items."

TEMPLATE = """# Customer Brief — {label} (last 30 days)

## Risk Level: {level}
{level_reason}

## Top Risks
{risks}

## Open Commitments
{commits}

## Recent Escalations
{escalations}

## Highlights
{highlights}

---

**Citations**  
{citations}
"""

# ---------- retrieval ----------
def _query(field: str, value: str, k: int = 50):
    """
    Use embeddings at query time (1536-d) and a SINGLE where condition
    to match your Chroma build's validator.
    """
    qvec = _embed("customer status last 30 days")
    return col.query(query_embeddings=[qvec], n_results=k, where={field: value})

def retrieve_context(label: str, k: int = 60):
    # Try label variants across both metadata keys
    variants = {label, label.strip(), label.lower(), slugify(label)}
    for field in ("account_id", "customer_id"):
        for v in variants:
            try:
                res = _query(field, v, k=k)
            except Exception:
                continue
            if res and res.get("documents") and res["documents"][0]:
                ctx_lines, cites = [], set()
                for i in range(len(res["ids"][0])):
                    text = res["documents"][0][i]
                    meta = (res.get("metadatas") or [[]])[0][i] if res.get("metadatas") else {}
                    sp = (meta or {}).get("source_path", "UNKNOWN")
                    ctx_lines.append(f"[{sp}] {text}")
                    cites.add(sp)
                return "\n".join(ctx_lines), "\n".join(sorted(cites))

    # Last resort: semantic search by label, no filter
    try:
        qvec = _embed(label)
        res = col.query(query_embeddings=[qvec], n_results=k)
        if res and res.get("documents") and res["documents"][0]:
            ctx_lines, cites = [], set()
            for i in range(len(res["ids"][0])):
                text = res["documents"][0][i]
                meta = (res.get("metadatas") or [[]])[0][i] if res.get("metadatas") else {}
                sp = (meta or {}).get("source_path", "UNKNOWN")
                ctx_lines.append(f"[{sp}] {text}")
                cites.add(sp)
            return "\n".join(ctx_lines), "\n".join(sorted(cites))
    except Exception:
        pass

    return "", ""

def _render_section(items):
    if not items:
        return "_None found_"
    return "\n".join(f"- {i['text']}" for i in items if i.get("text"))

# ---------- main entry ----------
def generate_brief(label: str):
    ctx, citations = retrieve_context(label)
    if not ctx.strip():
        # Let the API return a clean 404 instead of 500
        return None

    # Ask model to return structured JSON for clean sections
    SCHEMA_SYS = """Return ONLY valid JSON with this schema:
{
  "risks": [ {"text": "bullet with [path] citation"} ],
  "commitments": [ {"text": "bullet with [path] citation"} ],
  "escalations": [ {"text": "bullet with [path] citation"} ],
  "highlights": [ {"text": "bullet with [path] citation"} ]
}
Do not include keys with empty arrays; keep it concise and evidence-based.
"""

    resp = OA.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYS + "\n" + SCHEMA_SYS},
            {"role": "user", "content": "CONTEXT:\n" + ctx + "\n\nExtract bullets by section with citations."},
        ],
    )

    try:
        obj = json.loads(resp.choices[0].message.content)
    except Exception:
        # Fallback: ask for plain bullets if JSON parse fails
        alt = OA.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYS},
                {"role": "user", "content": "CONTEXT:\n" + ctx + "\n\nWrite concise bullet points with citations for risks, commitments, escalations, highlights."},
            ],
        )
        bullets = [l[2:].strip() for l in (alt.choices[0].message.content or "").splitlines() if l.strip().startswith("-")]
        obj = {"risks": [{"text": b} for b in bullets]}

    # Compute risk from all extracted bullets
    joined = "\n".join(i["text"] for k in ["risks", "commitments", "escalations", "highlights"] for i in obj.get(k, []))
    level, level_reason = score_risk(joined)

    out = TEMPLATE.format(
        label=label,
        level=level,
        level_reason=level_reason,
        risks=_render_section(obj.get("risks")),
        commits=_render_section(obj.get("commitments")),
        escalations=_render_section(obj.get("escalations")),
        highlights=_render_section(obj.get("highlights")),
        citations=citations or "_(citations included in bullets)_",
    )
    (BRIEFS / f"{slugify(label)}.md").write_text(out, encoding="utf-8")
    return {"account": label, "markdown": out, "risk_level": level, "risk_reason": level_reason}
