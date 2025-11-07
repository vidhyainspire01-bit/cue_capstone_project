
# # import os
# # import re
# # import json
# # import logging
# # from pathlib import Path
# # from typing import Tuple, List, Dict, Any
# # from datetime import datetime

# # import chromadb
# # from openai import OpenAI

# # import opik
# # from opik import track
# # from opik.integrations.openai import track_openai

# # # ---------- LOGGING ----------

# # logging.basicConfig(
# #     level=logging.DEBUG,
# #     format="%(asctime)s [%(levelname)s] %(message)s"
# # )

# # # ---------- CONFIG ----------

# # CHROMA_PATH = r"D:\CUE_\chromadb_persist"   # adjust if needed
# # COLLECTION = "cue_chunks"
# # EMBED_MODEL = "text-embedding-3-small"

# # ROOT = Path(__file__).resolve().parents[1]

# # # briefs for history / memory
# # BRIEFS = ROOT / "data" / "briefs"
# # BRIEFS.mkdir(parents=True, exist_ok=True)

# # # metrics for Trends tab
# # METRICS = ROOT / "data" / "metrics"
# # METRICS.mkdir(parents=True, exist_ok=True)
# # METRICS_FILE = METRICS / "brief_runs.jsonl"

# # OPENAI_KEY = os.getenv("OPENAI_API_KEY")
# # if not OPENAI_KEY:
# #     raise RuntimeError("OPENAI_API_KEY is not set for the server process.")

# # # Opik env (set these in your shell)
# # OPIK_API_KEY = os.getenv("OPIK_API_KEY")
# # # OPIK_WORKSPACE = os.getenv("OPIK_WORKSPACE")  # optional but recommended

# # # ---------- OPIK CONFIG ----------

# # if OPIK_API_KEY:
# #     opik.configure(
# #         api_key=OPIK_API_KEY,
# #         workspace="vidhya-thiruvenkadam",
# #         use_local=False,  # send traces to Opik Cloud
# #     )
# #     logging.info("Opik configured for remote tracing (workspace auto-detected for API key).")
# # else:
# #     opik.configure(use_local=True)
# #     logging.info("OPIK_API_KEY not set; Opik running in local/no-remote mode.")


# # # Wrap OpenAI client so all LLM calls are traced in Opik
# # OA = track_openai(OpenAI(api_key=OPENAI_KEY))

# # # Chroma client
# # client = chromadb.PersistentClient(path=CHROMA_PATH)
# # col = client.get_collection(COLLECTION)


# # # ---------- HELPERS ----------

# # def slugify(s: str) -> str:
# #     s = (s or "").strip().lower()
# #     s = re.sub(r"&", " and ", s)
# #     s = re.sub(r"[^a-z0-9]+", "_", s)
# #     return re.sub(r"_+", "_", s).strip("_")

# # def _embed(text: str) -> List[float]:
# #     return OA.embeddings.create(
# #         model=EMBED_MODEL,
# #         input=[text],
# #     ).data[0].embedding

# # def _query_with_where(field: str, value: str, k: int = 60):
# #     """Query Chroma using metadata filter + embedding."""
# #     qvec = _embed(f"{value} last 30 days customer signals")
# #     return col.query(
# #         query_embeddings=[qvec],
# #         n_results=k,
# #         where={field: value},
# #     )

# # @track()  # this whole retrieval step becomes a span/trace in Opik
# # def retrieve_context(label: str, k: int = 60) -> Tuple[str, str]:
# #     """
# #     Try metadata-constrained search first, then semantic fallback.
# #     Returns (context_text, citations_block).
# #     """
# #     variants = {label, label.strip(), label.lower(), slugify(label)}

# #     # 1) metadata-filtered search
# #     for field in ("account_id", "customer_id", "account", "customer", "client"):
# #         for v in variants:
# #             try:
# #                 res = _query_with_where(field, v, k=k)
# #             except Exception as e:
# #                 logging.warning(f"Chroma query failed for {field}={v}: {e}")
# #                 continue

# #             docs = res.get("documents", [[]])[0]
# #             metas = (res.get("metadatas") or [[]])[0]

# #             if docs:
# #                 ctx_lines: List[str] = []
# #                 cites: set[str] = set()
# #                 for i, txt in enumerate(docs):
# #                     meta = metas[i] if i < len(metas) else {}
# #                     sp = (meta or {}).get("source_path", meta.get("source", "UNKNOWN"))
# #                     ctx_lines.append(f"[{sp}] {txt}")
# #                     if sp:
# #                         cites.add(sp)
# #                 return "\n".join(ctx_lines), "\n".join(sorted(cites))

# #     # 2) pure semantic fallback
# #     try:
# #         qvec = _embed(label)
# #         res = col.query(query_embeddings=[qvec], n_results=k)
# #         docs = res.get("documents", [[]])[0]
# #         metas = (res.get("metadatas") or [[]])[0]
# #         if docs:
# #             ctx_lines = []
# #             cites = set()
# #             for i, txt in enumerate(docs):
# #                 meta = metas[i] if i < len(metas) else {}
# #                 sp = (meta or {}).get("source_path", meta.get("source", "UNKNOWN"))
# #                 ctx_lines.append(f"[{sp}] {txt}")
# #                 if sp:
# #                     cites.add(sp)
# #             return "\n".join(ctx_lines), "\n".join(sorted(cites))
# #     except Exception as e:
# #         logging.error(f"Chroma semantic fallback failed: {e}")

# #     # 3) nothing found
# #     return "", ""

# # # ---------- SIMPLE GUARDRAILS & RISK ----------

# # NEG_SIGNS = [
# #     r"\bp0\b", r"\bp1\b", "sev", "escalation", "outage",
# #     "downtime", "sla breach", "churn", "drop", "decrease", "% drop",
# # ]
# # POS_SIGNS = [
# #     "renewal confirmed", "adoption up", "positive nps",
# #     "% increase", "resolved", "mitigated",
# # ]

# # def score_risk(text: str) -> Tuple[str, str]:
# #     t = text.lower()
# #     neg = sum(bool(re.search(p, t)) for p in NEG_SIGNS)
# #     pos = sum(p in t for p in POS_SIGNS)
# #     score = neg - 0.5 * pos
# #     if score >= 2:
# #         return "High", "Multiple strong negative signals detected."
# #     if score <= 0:
# #         return "Low", "No strong negatives; some positive/adoption signals."
# #     return "Medium", "Mixed signals; monitor closely."

# # CITATION_PATTERN = re.compile(r"\[[^\]]+\]")

# # def _render_section(items: List[Dict[str, Any]]) -> str:
# #     if not items:
# #         return "_None found_"
# #     return "\n".join(f"- {i['text']}" for i in items if i.get("text"))

# # def _ensure_cited(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
# #     """
# #     Drop bullets without [..] citations to avoid hallucinated claims.
# #     Normalize to {'text': ...}.
# #     """
# #     safe: List[Dict[str, Any]] = []
# #     for it in items or []:
# #         txt = (it.get("text") or it.get("summary") or "").strip()
# #         if txt and CITATION_PATTERN.search(txt):
# #             safe.append({"text": txt})
# #     return safe

# # def check_usage_consistency(items: List[Dict[str, Any]]) -> Dict[str, Any]:
# #     ups = downs = 0
# #     for it in items or []:
# #         txt = (it.get("text") or "").lower()
# #         if any(k in txt for k in ["usage up", "increase in usage", "+% usage"]):
# #             ups += 1
# #         if any(k in txt for k in ["usage down", "decrease in usage", "-% usage"]):
# #             downs += 1
# #     conflict = ups > 0 and downs > 0
# #     return {
# #         "usage_conflict": conflict,
# #         "usage_ups": ups,
# #         "usage_downs": downs,
# #     }

# # # ---------- METRICS (local) ----------

# # def log_eval(run: Dict[str, Any]) -> None:
# #     try:
# #         payload = {
# #             "ts": datetime.utcnow().isoformat() + "Z",
# #             "account": run.get("account"),
# #             "risk_level": run.get("risk_level"),
# #             "guardrails_ok": run.get("guardrails", {}).get("ok", True),
# #             "coverage_ratio": run.get("coverage", {}).get("ratio", 0.0),
# #         }
# #         with METRICS_FILE.open("a", encoding="utf-8") as f:
# #             f.write(json.dumps(payload) + "\n")
# #     except Exception as e:
# #         logging.warning(f"Could not write metrics JSONL: {e}")

# # # ---------- TEMPLATE ----------

# # TEMPLATE = """CUE — Signal Unification & Citable Summaries (Iteration 3)

# # Customer Brief — {label} (last 30 days)

# # Risk Level: {level}
# # {level_reason}

# # Top Risks
# # {risks}

# # Open Commitments
# # {commits}

# # Recent Escalations
# # {escalations}

# # Highlights
# # {highlights}

# # Citations
# # {citations}
# # """

# # # ---------- MAIN: generate_brief ----------
# # from opik import log_metadata
# # @track()  # whole pipeline becomes a trace in Opik

# # def generate_brief(label: str) -> Dict[str, Any]:
# #     log_metadata("account", label)
# #     log_metadata("pipeline", "cue-iter3")
# #     logging.info(f"Generating brief for '{label}'")

# #     # 1) retrieve context
# #     ctx, citations = retrieve_context(label)
# #     if not ctx.strip():
# #         logging.warning(f"No context found for '{label}'")
# #         return None

# #     # 2) call LLM for structured bullets
# #     schema_sys = """Return ONLY valid JSON with this schema:
# # {
# #   "risks": [ {"text": "bullet with [path] citation"} ],
# #   "commitments": [ {"text": "bullet with [path] citation"} ],
# #   "escalations": [ {"text": "bullet with [path] citation"} ],
# #   "highlights": [ {"text": "bullet with [path] citation"} ]
# # }
# # No prose, no extra keys.
# # """

# #     resp = OA.chat.completions.create(
# #         model="gpt-4o-mini",
# #         temperature=0.2,
# #         response_format={"type": "json_object"},
# #         messages=[
# #             {
# #                 "role": "system",
# #                 "content": (
# #                     "You are a rigorous CS analyst for executive briefs. "
# #                     "Only make claims supported by the CONTEXT. "
# #                     "Every bullet MUST include at least one source in [..]."
# #                 )
# #                 + "\n"
# #                 + schema_sys,
# #             },
# #             {"role": "user", "content": "CONTEXT:\n" + ctx},
# #         ],
# #     )

# #     try:
# #         raw = json.loads(resp.choices[0].message.content)
# #     except Exception as e:
# #         logging.error(f"Failed to parse LLM JSON: {e}")
# #         raw = {}

# #     # 3) guardrails: structure + citations
# #     risks = _ensure_cited(raw.get("risks", []) or [])
# #     commits = _ensure_cited(raw.get("commitments", []) or [])
# #     escs = _ensure_cited(raw.get("escalations", []) or [])
# #     highs = _ensure_cited(raw.get("highlights", []) or [])

# #     if not (risks or commits or escs or highs):
# #         highs = [{"text": "[context] See underlying evidence documents for this account."}]

# #     # 4) consistency + risk
# #     all_items = risks + commits + escs + highs
# #     consistency = check_usage_consistency(all_items)
# #     joined = "\n".join(i["text"] for i in all_items)
# #     level, level_reason = score_risk(joined)
# #     if consistency["usage_conflict"]:
# #         level_reason += " | Note: conflicting usage signals detected across sources."

# #     # 5) render markdown
# #     md = TEMPLATE.format(
# #         label=label,
# #         level=level,
# #         level_reason=level_reason,
# #         risks=_render_section(risks),
# #         commits=_render_section(commits),
# #         escalations=_render_section(escs),
# #         highlights=_render_section(highs),
# #         citations=citations or "_(citations included in bullets)_",
# #     )

# #     # 6) guardrail summary
# #     guardrails = {
# #         "ok": not consistency["usage_conflict"],
# #         "pii_flag": False,
# #         "usage_conflict": consistency["usage_conflict"],
# #     }

# #     # 7) save brief
# #     try:
# #         (BRIEFS / f"{slugify(label)}.md").write_text(md, encoding="utf-8")
# #     except Exception as e:
# #         logging.warning(f"Could not write brief file: {e}")

# #     # 8) build result
# #     result: Dict[str, Any] = {
# #         "account": label,
# #         "markdown": md,
# #         "risk_level": level,
# #         "risk_reason": level_reason,
# #         "guardrails": guardrails,
# #         "coverage": {"ratio": 1.0, "present": ["cue_chunks"]},
# #     }
    
# #     from opik import log_metric

# #     # record structured metrics
# #     log_metric("risk_level", result["risk_level"])
# #     log_metric("coverage_ratio", result["coverage"]["ratio"])
# #     log_metric("guardrails_ok", result["guardrails"]["ok"])


# #     # 9) local metrics
# #     log_eval(result)

# #     logging.info(f"Brief generated for '{label}' with risk={level}")
# #     return result

# # # ---------- CLI TEST ENTRYPOINT ----------

# # if __name__ == "__main__":
# #     import sys
# #     lbl = sys.argv[1] if len(sys.argv) > 1 else "Acme Tech"
# #     print(f"🔍 Generating brief for: {lbl}")
# #     res = generate_brief(lbl)
# #     print("✅ Result:")
# #     print(json.dumps(res, indent=2))


# import os
# import re
# import json
# import logging
# from pathlib import Path
# from typing import Tuple, List, Dict, Any
# from datetime import datetime

# import chromadb
# from openai import OpenAI

# import opik
# from opik import track
# from opik.integrations.openai import track_openai

# # ---------- LOGGING ----------

# logging.basicConfig(
#     level=logging.DEBUG,
#     format="%(asctime)s [%(levelname)s] %(message)s"
# )

# # ---------- CONFIG ----------

# CHROMA_PATH = r"D:\CUE_\chromadb_persist"   # adjust if needed
# COLLECTION = "cue_chunks"
# EMBED_MODEL = "text-embedding-3-small"

# ROOT = Path(__file__).resolve().parents[1]

# # briefs for history / memory
# BRIEFS = ROOT / "data" / "briefs"
# BRIEFS.mkdir(parents=True, exist_ok=True)

# # metrics for Trends tab
# METRICS = ROOT / "data" / "metrics"
# METRICS.mkdir(parents=True, exist_ok=True)
# METRICS_FILE = METRICS / "brief_runs.jsonl"

# OPENAI_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_KEY:
#     raise RuntimeError("OPENAI_API_KEY is not set for the server process.")

# OPIK_API_KEY = os.getenv("OPIK_API_KEY")

# # ---------- OPIK CONFIG ----------

# if OPIK_API_KEY:
#     # Traces go to workspace bound to this API key; project is configured via ~/.opik.config
#     opik.configure(
#         api_key=OPIK_API_KEY,
#         workspace="vidhya-thiruvenkadam",
#         use_local=False,
#     )
#     logging.info("Opik configured for remote tracing.")
# else:
#     opik.configure(use_local=True)
#     logging.info("OPIK_API_KEY not set; Opik running in local/no-remote mode.")

# # Wrap OpenAI client so all LLM calls are traced in Opik
# OA = track_openai(OpenAI(api_key=OPENAI_KEY))

# # Chroma client
# client = chromadb.PersistentClient(path=CHROMA_PATH)
# col = client.get_collection(COLLECTION)

# # ---------- HELPERS ----------

# def slugify(s: str) -> str:
#     s = (s or "").strip().lower()
#     s = re.sub(r"&", " and ", s)
#     s = re.sub(r"[^a-z0-9]+", "_", s)
#     return re.sub(r"_+", "_", s).strip("_")

# def _embed(text: str) -> List[float]:
#     return OA.embeddings.create(
#         model=EMBED_MODEL,
#         input=[text],
#     ).data[0].embedding

# def _query_with_where(field: str, value: str, k: int = 60):
#     """Query Chroma using metadata filter + embedding."""
#     qvec = _embed(f"{value} last 30 days customer signals")
#     return col.query(
#         query_embeddings=[qvec],
#         n_results=k,
#         where={field: value},
#     )

# @track(name="retrieve_context")  # logged as a span in the current trace
# def retrieve_context(label: str, k: int = 60) -> Tuple[str, str]:
#     """
#     Try metadata-constrained search first, then semantic fallback.
#     Returns (context_text, citations_block).
#     """
#     variants = {label, label.strip(), label.lower(), slugify(label)}

#     # 1) metadata-filtered search
#     for field in ("account_id", "customer_id", "account", "customer", "client"):
#         for v in variants:
#             try:
#                 res = _query_with_where(field, v, k=k)
#             except Exception as e:
#                 logging.warning(f"Chroma query failed for {field}={v}: {e}")
#                 continue

#             docs = res.get("documents", [[]])[0]
#             metas = (res.get("metadatas") or [[]])[0]

#             if docs:
#                 ctx_lines: List[str] = []
#                 cites: set[str] = set()
#                 for i, txt in enumerate(docs):
#                     meta = metas[i] if i < len(metas) else {}
#                     sp = (meta or {}).get("source_path", meta.get("source", "UNKNOWN"))
#                     ctx_lines.append(f"[{sp}] {txt}")
#                     if sp:
#                         cites.add(sp)
#                 return "\n".join(ctx_lines), "\n".join(sorted(cites))

#     # 2) pure semantic fallback
#     try:
#         qvec = _embed(label)
#         res = col.query(query_embeddings=[qvec], n_results=k)
#         docs = res.get("documents", [[]])[0]
#         metas = (res.get("metadatas") or [[]])[0]
#         if docs:
#             ctx_lines = []
#             cites = set()
#             for i, txt in enumerate(docs):
#                 meta = metas[i] if i < len(metas) else {}
#                 sp = (meta or {}).get("source_path", meta.get("source", "UNKNOWN"))
#                 ctx_lines.append(f"[{sp}] {txt}")
#                 if sp:
#                     cites.add(sp)
#             return "\n".join(ctx_lines), "\n".join(sorted(cites))
#     except Exception as e:
#         logging.error(f"Chroma semantic fallback failed: {e}")

#     # 3) nothing found
#     return "", ""

# # ---------- SIMPLE GUARDRAILS & RISK ----------

# NEG_SIGNS = [
#     r"\bp0\b", r"\bp1\b", "sev", "escalation", "outage",
#     "downtime", "sla breach", "churn", "drop", "decrease", "% drop",
# ]
# POS_SIGNS = [
#     "renewal confirmed", "adoption up", "positive nps",
#     "% increase", "resolved", "mitigated",
# ]

# def score_risk(text: str) -> Tuple[str, str]:
#     t = text.lower()
#     neg = sum(bool(re.search(p, t)) for p in NEG_SIGNS)
#     pos = sum(p in t for p in POS_SIGNS)
#     score = neg - 0.5 * pos
#     if score >= 2:
#         return "High", "Multiple strong negative signals detected."
#     if score <= 0:
#         return "Low", "No strong negatives; some positive/adoption signals."
#     return "Medium", "Mixed signals; monitor closely."

# CITATION_PATTERN = re.compile(r"\[[^\]]+\]")

# def _render_section(items: List[Dict[str, Any]]) -> str:
#     if not items:
#         return "_None found_"
#     return "\n".join(f"- {i['text']}" for i in items if i.get("text"))

# def _ensure_cited(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     """Drop bullets without [..] citations. Normalize to {'text': ...}."""
#     safe: List[Dict[str, Any]] = []
#     for it in items or []:
#         txt = (it.get("text") or it.get("summary") or "").strip()
#         if txt and CITATION_PATTERN.search(txt):
#             safe.append({"text": txt})
#     return safe

# def check_usage_consistency(items: List[Dict[str, Any]]) -> Dict[str, Any]:
#     ups = downs = 0
#     for it in items or []:
#         txt = (it.get("text") or "").lower()
#         if any(k in txt for k in ["usage up", "increase in usage", "+% usage"]):
#             ups += 1
#         if any(k in txt for k in ["usage down", "decrease in usage", "-% usage"]):
#             downs += 1
#     conflict = ups > 0 and downs > 0
#     return {
#         "usage_conflict": conflict,
#         "usage_ups": ups,
#         "usage_downs": downs,
#     }

# # ---------- METRICS (local) ----------

# def log_eval(run: Dict[str, Any]) -> None:
#     try:
#         payload = {
#             "ts": datetime.utcnow().isoformat() + "Z",
#             "account": run.get("account"),
#             "risk_level": run.get("risk_level"),
#             "guardrails_ok": run.get("guardrails", {}).get("ok", True),
#             "coverage_ratio": run.get("coverage", {}).get("ratio", 0.0),
#         }
#         with METRICS_FILE.open("a", encoding="utf-8") as f:
#             f.write(json.dumps(payload) + "\n")
#     except Exception as e:
#         logging.warning(f"Could not write metrics JSONL: {e}")

# # ---------- TEMPLATE ----------

# TEMPLATE = """CUE — Signal Unification & Citable Summaries (Iteration 3)

# Customer Brief — {label} (last 30 days)

# Risk Level: {level}
# {level_reason}

# Top Risks
# {risks}

# Open Commitments
# {commits}

# Recent Escalations
# {escalations}

# Highlights
# {highlights}

# Citations
# {citations}
# """

# # ---------- MAIN: generate_brief ----------

# @track(name="generate_brief", tags=["cue-iter3"])
# def generate_brief(label: str) -> Dict[str, Any]:
#     logging.info(f"Generating brief for '{label}'")

#     # 1) retrieve context
#     ctx, citations = retrieve_context(label)
#     if not ctx.strip():
#         logging.warning(f"No context found for '{label}'")
#         return None

#     # 2) call LLM for structured bullets
#     schema_sys = """Return ONLY valid JSON with this schema:
# {
#   "risks": [ {"text": "bullet with [path] citation"} ],
#   "commitments": [ {"text": "bullet with [path] citation"} ],
#   "escalations": [ {"text": "bullet with [path] citation"} ],
#   "highlights": [ {"text": "bullet with [path] citation"} ]
# }
# No prose, no extra keys.
# """

#     resp = OA.chat.completions.create(
#         model="gpt-4o-mini",
#         temperature=0.2,
#         response_format={"type": "json_object"},
#         messages=[
#             {
#                 "role": "system",
#                 "content": (
#                     "You are a rigorous CS analyst for executive briefs. "
#                     "Only make claims supported by the CONTEXT. "
#                     "Every bullet MUST include at least one source in [..]."
#                 ) + "\n" + schema_sys,
#             },
#             {"role": "user", "content": "CONTEXT:\n" + ctx},
#         ],
#     )

#     try:
#         raw = json.loads(resp.choices[0].message.content)
#     except Exception as e:
#         logging.error(f"Failed to parse LLM JSON: {e}")
#         raw = {}

#     # 3) guardrails: structure + citations
#     risks = _ensure_cited(raw.get("risks", []) or [])
#     commits = _ensure_cited(raw.get("commitments", []) or [])
#     escs = _ensure_cited(raw.get("escalations", []) or [])
#     highs = _ensure_cited(raw.get("highlights", []) or [])

#     if not (risks or commits or escs or highs):
#         highs = [{"text": "[context] See underlying evidence documents for this account."}]

#     # 4) consistency + risk
#     all_items = risks + commits + escs + highs
#     consistency = check_usage_consistency(all_items)
#     joined = "\n".join(i["text"] for i in all_items)
#     level, level_reason = score_risk(joined)
#     if consistency["usage_conflict"]:
#         level_reason += " | Note: conflicting usage signals detected across sources."

#     # 5) render markdown
#     md = TEMPLATE.format(
#         label=label,
#         level=level,
#         level_reason=level_reason,
#         risks=_render_section(risks),
#         commits=_render_section(commits),
#         escalations=_render_section(escs),
#         highlights=_render_section(highs),
#         citations=citations or "_(citations included in bullets)_",
#     )

#     # 6) guardrail summary
#     guardrails = {
#         "ok": not consistency["usage_conflict"],
#         "pii_flag": False,
#         "usage_conflict": consistency["usage_conflict"],
#     }

#     # 7) save brief
#     try:
#         (BRIEFS / f"{slugify(label)}.md").write_text(md, encoding="utf-8")
#     except Exception as e:
#         logging.warning(f"Could not write brief file: {e}")

#     # 8) build result (also carries metadata/metrics for Opik)
#     result: Dict[str, Any] = {
#         "account": label,
#         "markdown": md,
#         "risk_level": level,
#         "risk_reason": level_reason,
#         "guardrails": guardrails,
#         "coverage": {"ratio": 1.0, "present": ["cue_chunks"]},
#         "metadata": {
#             "account": label,
#             "pipeline": "cue-iter3",
#         },
#         "metrics": {
#             "guardrails_ok": guardrails["ok"],
#             "coverage_ratio": 1.0,
#         },
#     }

#     # 9) local metrics file (for your Trends tab)
#     log_eval(result)

#     logging.info(f"Brief generated for '{label}' with risk={level}")
#     return result

# # ---------- CLI TEST ENTRYPOINT ----------

# if __name__ == "__main__":
#     import sys
#     lbl = sys.argv[1] if len(sys.argv) > 1 else "Acme Tech"
#     print(f"🔍 Generating brief for: {lbl}")
#     res = generate_brief(lbl)
#     print("✅ Result:")
#     print(json.dumps(res, indent=2))



# scripts/generate_brief.py

import os
import re
import json
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any
from datetime import datetime

import chromadb
from openai import OpenAI

import opik
from opik import track
from opik.integrations.openai import track_openai

# ---------- LOGGING ----------

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ---------- CONFIG ----------

CHROMA_PATH = r"D:\CUE_\chromadb_persist"
COLLECTION = "cue_chunks"
EMBED_MODEL = "text-embedding-3-small"

ROOT = Path(__file__).resolve().parents[1]

# briefs for history / memory
BRIEFS = ROOT / "data" / "briefs"
BRIEFS.mkdir(parents=True, exist_ok=True)

# metrics for Trends tab
METRICS = ROOT / "data" / "metrics"
METRICS.mkdir(parents=True, exist_ok=True)
METRICS_FILE = METRICS / "brief_runs.jsonl"

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set for the server process.")

OPIK_API_KEY = os.getenv("OPIK_API_KEY")

# ---------- OPIK CONFIG ----------

if OPIK_API_KEY:
    # project name comes from ~/.opik.config; workspace inferred from API key
    opik.configure(
        api_key=OPIK_API_KEY,
        use_local=False,
    )
    logging.info("Opik configured for remote tracing.")
else:
    opik.configure(use_local=True)
    logging.info("OPIK_API_KEY not set; Opik running in local/no-remote mode.")

# Wrap OpenAI client so all LLM calls are traced in Opik
OA = track_openai(OpenAI(api_key=OPENAI_KEY))

# Chroma client
client = chromadb.PersistentClient(path=CHROMA_PATH)
col = client.get_collection(COLLECTION)

# ---------- HELPERS ----------

def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"&", " and ", s)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")

def _embed(text: str) -> List[float]:
    return OA.embeddings.create(
        model=EMBED_MODEL,
        input=[text],
    ).data[0].embedding

def _query_with_where(field: str, value: str, k: int = 60):
    """Query Chroma using metadata filter + embedding."""
    qvec = _embed(f"{value} last 30 days customer signals")
    return col.query(
        query_embeddings=[qvec],
        n_results=k,
        where={field: value},
    )

@track(name="retrieve_context")  # logged as a span
def retrieve_context(label: str, k: int = 60) -> Tuple[str, str]:
    """
    Try metadata-constrained search first, then semantic fallback.
    Returns (context_text, citations_block).
    """
    variants = {label, label.strip(), label.lower(), slugify(label)}

    # 1) metadata-filtered search
    for field in ("account_id", "customer_id", "account", "customer", "client"):
        for v in variants:
            try:
                res = _query_with_where(field, v, k=k)
            except Exception as e:
                logging.warning(f"Chroma query failed for {field}={v}: {e}")
                continue

            docs = res.get("documents", [[]])[0]
            metas = (res.get("metadatas") or [[]])[0]

            if docs:
                ctx_lines: List[str] = []
                cites: set[str] = set()
                for i, txt in enumerate(docs):
                    meta = metas[i] if i < len(metas) else {}
                    sp = (meta or {}).get("source_path", meta.get("source", "UNKNOWN"))
                    ctx_lines.append(f"[{sp}] {txt}")
                    if sp:
                        cites.add(sp)
                return "\n".join(ctx_lines), "\n".join(sorted(cites))

    # 2) pure semantic fallback
    try:
        qvec = _embed(label)
        res = col.query(query_embeddings=[qvec], n_results=k)
        docs = res.get("documents", [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        if docs:
            ctx_lines = []
            cites = set()
            for i, txt in enumerate(docs):
                meta = metas[i] if i < len(metas) else {}
                sp = (meta or {}).get("source_path", meta.get("source", "UNKNOWN"))
                ctx_lines.append(f"[{sp}] {txt}")
                if sp:
                    cites.add(sp)
            return "\n".join(ctx_lines), "\n".join(sorted(cites))
    except Exception as e:
        logging.error(f"Chroma semantic fallback failed: {e}")

    # 3) nothing found
    return "", ""

# ---------- SIMPLE GUARDRAILS & RISK ----------

NEG_SIGNS = [
    r"\bp0\b", r"\bp1\b", "sev", "escalation", "outage",
    "downtime", "sla breach", "churn", "drop", "decrease", "% drop",
]
POS_SIGNS = [
    "renewal confirmed", "adoption up", "positive nps",
    "% increase", "resolved", "mitigated",
]

def score_risk(text: str) -> Tuple[str, str]:
    t = text.lower()
    neg = sum(bool(re.search(p, t)) for p in NEG_SIGNS)
    pos = sum(p in t for p in POS_SIGNS)
    score = neg - 0.5 * pos
    if score >= 2:
        return "High", "Multiple strong negative signals detected."
    if score <= 0:
        return "Low", "No strong negatives; some positive/adoption signals."
    return "Medium", "Mixed signals; monitor closely."

CITATION_PATTERN = re.compile(r"\[[^\]]+\]")

def _render_section(items: List[Dict[str, Any]]) -> str:
    if not items:
        return "_None found_"
    return "\n".join(f"- {i['text']}" for i in items if i.get("text"))

def _ensure_cited(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Drop bullets without [..] citations. Normalize to {'text': ...}."""
    safe: List[Dict[str, Any]] = []
    for it in items or []:
        txt = (it.get("text") or it.get("summary") or "").strip()
        if txt and CITATION_PATTERN.search(txt):
            safe.append({"text": txt})
    return safe

def check_usage_consistency(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    ups = downs = 0
    for it in items or []:
        txt = (it.get("text") or "").lower()
        if any(k in txt for k in ["usage up", "increase in usage", "+% usage"]):
            ups += 1
        if any(k in txt for k in ["usage down", "decrease in usage", "-% usage"]):
            downs += 1
    conflict = ups > 0 and downs > 0
    return {
        "usage_conflict": conflict,
        "usage_ups": ups,
        "usage_downs": downs,
    }

# ---------- METRICS (local) ----------

def log_eval(run: Dict[str, Any]) -> None:
    try:
        payload = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "account": run.get("account"),
            "risk_level": run.get("risk_level"),
            "guardrails_ok": run.get("guardrails", {}).get("ok", True),
            "coverage_ratio": run.get("coverage", {}).get("ratio", 0.0),
        }
        with METRICS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception as e:
        logging.warning(f"Could not write metrics JSONL: {e}")

# ---------- TEMPLATE ----------

TEMPLATE = """CUE — Signal Unification & Citable Summaries (Iteration 3)

Customer Brief — {label} (last 30 days)

Risk Level: {level}
{level_reason}

Top Risks
{risks}

Open Commitments
{commits}

Recent Escalations
{escalations}

Highlights
{highlights}

Citations
{citations}
"""

# ---------- MAIN: generate_brief ----------

@track(name="generate_brief", tags=["cue-iter3"])
def generate_brief(label: str) -> Dict[str, Any]:
    logging.info(f"Generating brief for '{label}'")

    # 1) retrieve context
    ctx, citations = retrieve_context(label)
    if not ctx.strip():
        logging.warning(f"No context found for '{label}'")
        return None

    # 2) call LLM for structured bullets
    schema_sys = """Return ONLY valid JSON with this schema:
{
  "risks": [ {"text": "bullet with [path] citation"} ],
  "commitments": [ {"text": "bullet with [path] citation"} ],
  "escalations": [ {"text": "bullet with [path] citation"} ],
  "highlights": [ {"text": "bullet with [path] citation"} ]
}
No prose, no extra keys.
"""

    resp = OA.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a rigorous CS analyst for executive briefs. "
                    "Only make claims supported by the CONTEXT. "
                    "Every bullet MUST include at least one source in [..]."
                ) + "\n" + schema_sys,
            },
            {"role": "user", "content": "CONTEXT:\n" + ctx},
        ],
    )

    try:
        raw = json.loads(resp.choices[0].message.content)
    except Exception as e:
        logging.error(f"Failed to parse LLM JSON: {e}")
        raw = {}

    # 3) guardrails: structure + citations
    risks = _ensure_cited(raw.get("risks", []) or [])
    commits = _ensure_cited(raw.get("commitments", []) or [])
    escs = _ensure_cited(raw.get("escalations", []) or [])
    highs = _ensure_cited(raw.get("highlights", []) or [])

    if not (risks or commits or escs or highs):
        highs = [{"text": "[context] See underlying evidence documents for this account."}]

    # 4) consistency + risk
    all_items = risks + commits + escs + highs
    consistency = check_usage_consistency(all_items)
    joined = "\n".join(i["text"] for i in all_items)
    level, level_reason = score_risk(joined)
    if consistency["usage_conflict"]:
        level_reason += " | Note: conflicting usage signals detected across sources."

    # 5) render markdown
    md = TEMPLATE.format(
        label=label,
        level=level,
        level_reason=level_reason,
        risks=_render_section(risks),
        commits=_render_section(commits),
        escalations=_render_section(escs),
        highlights=_render_section(highs),
        citations=citations or "_(citations included in bullets)_",
    )

    # 6) guardrail summary
    guardrails = {
        "ok": not consistency["usage_conflict"],
        "pii_flag": False,
        "usage_conflict": consistency["usage_conflict"],
    }

    # 7) save brief to disk
    try:
        (BRIEFS / f"{slugify(label)}.md").write_text(md, encoding="utf-8")
    except Exception as e:
        logging.warning(f"Could not write brief file: {e}")

    # 8) build result (Opik-friendly)
    result: Dict[str, Any] = {
        "account": label,
        "markdown": md,
        "risk_level": level,
        "risk_reason": level_reason,
        "guardrails": guardrails,
        "coverage": {"ratio": 1.0, "present": ["cue_chunks"]},
        "metadata": {
            "account": label,
            "pipeline": "cue-iter3",
        },
        "metrics": {
            "guardrails_ok": guardrails["ok"],
            "coverage_ratio": 1.0,
        },
    }

    # 9) local metrics for Trends
    log_eval(result)

    logging.info(f"Brief generated for '{label}' with risk={level}")
    return result

# ---------- CLI TEST ENTRYPOINT ----------

if __name__ == "__main__":
    import sys
    lbl = sys.argv[1] if len(sys.argv) > 1 else "Acme Tech"
    print(f"🔍 Generating brief for: {lbl}")
    res = generate_brief(lbl)
    print("✅ Result:")
    print(json.dumps(res, indent=2))
