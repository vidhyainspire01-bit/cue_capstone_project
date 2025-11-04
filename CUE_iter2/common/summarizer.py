# common/summarizer.py
from typing import List, Dict
from .llm_client import chat

SYSTEM_PROMPT = """You are CUE's Summarizer v2.
- Answer the user's question using ONLY the retrieved snippets.
- Be concise, factual, and executive-friendly.
- Always include a short 'Sources' section listing source_path or doc_id from metadata.
- If evidence is missing, say what’s missing instead of guessing.
"""

def _format_context(hits: List[Dict]) -> str:
    blocks = []
    for i, h in enumerate(hits, 1):
        meta = h.get("metadata", {}) or {}
        src = meta.get("source_path") or meta.get("url") or meta.get("doc_id") or "unknown_source"
        tag = meta.get("doc_type") or meta.get("tags") or ""
        blocks.append(
            f"[{i}] source={src} tag={tag}\n{h.get('text','').strip()}"
        )
    return "\n\n".join(blocks)

def summarize_answer_v2(question: str, hits: List[Dict]) -> str:
    context = _format_context(hits)
    user = f"""Question:
{question}

Context (retrieved snippets):
{context}

Instructions:
- Synthesize a direct answer in 5-10 bullet points max (or fewer if simple).
- Quote numbers and dates when present.
- End with:

Sources:
- list each [index] with its source (avoid duplicates)."""

    return chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ]
    )
