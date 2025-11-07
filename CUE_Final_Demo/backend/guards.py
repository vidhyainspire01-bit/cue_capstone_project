import re
from typing import Dict, Any, List, Tuple

# ---- Input Guardrails ----

ALLOWED_CLIENT_CHARS = re.compile(r"^[\w\s\-\.&()]+$")

def validate_client_name(name: str) -> Tuple[bool, str]:
    if not name or not name.strip():
        return False, "Client name is required."
    if len(name) > 100:
        return False, "Client name too long."
    if not ALLOWED_CLIENT_CHARS.match(name):
        return False, "Client name contains invalid characters."
    return True, ""

def sanitize_question(q: str) -> str:
    # Strip obvious prompt-injection / system override patterns
    banned = [
        "ignore previous instructions",
        "act as system",
        "you are chatgpt",
        "delete all data",
    ]
    q_norm = q.strip()
    lower = q_norm.lower()
    if any(b in lower for b in banned):
        # neutralize by truncating / replacing
        return "Explain the recent customer status based on available evidence."
    return q_norm

# ---- Process Guardrails ----

CITATION_PATTERN = re.compile(r"\[[^\]]+\]")  # [path] style

def ensure_citations_on_bullets(section_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Drop or tag bullets that don't have any [..] style citation.
    This enforces: no naked claims.
    """
    safe_items: List[Dict[str, Any]] = []
    for item in section_items or []:
        txt = item.get("text", "") or item.get("summary", "")
        if CITATION_PATTERN.search(txt):
            safe_items.append(item)
        # else: silently drop; could also tag as 'needs_review'
    return safe_items

def limit_section_len(section_items: List[Dict[str, Any]], max_items: int = 10) -> List[Dict[str, Any]]:
    return (section_items or [])[:max_items]

def validate_llm_schema(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Defensive: keep only expected keys + list-of-dict structure.
    """
    safe: Dict[str, Any] = {}
    for key in ["risks", "commitments", "escalations", "highlights"]:
        raw = obj.get(key, []) or []
        if isinstance(raw, list):
            cleaned = []
            for it in raw:
                if not isinstance(it, dict):
                    continue
                txt = str(it.get("text", "")).strip()
                if not txt:
                    continue
                cleaned.append({"text": txt})
            if cleaned:
                safe[key] = cleaned
    return safe

# ---- Output Guardrails ----

PII_HINTS = [
    r"\b\d{12,16}\b",          # long numbers (potential card/ids)
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN-like
    r"@gmail\.com", r"@yahoo\.com"
]

def scan_pii(text: str) -> bool:
    lower = text.lower()
    for pattern in PII_HINTS:
        if re.search(pattern, lower):
            return True
    return False

def final_output_guardrails(markdown: str) -> Dict[str, Any]:
    """
    Return guardrail status for UI + logging.
    """
    pii_flag = scan_pii(markdown)
    return {
        "ok": not pii_flag,
        "pii_flag": pii_flag,
    }
