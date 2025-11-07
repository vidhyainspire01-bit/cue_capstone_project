# scripts/build_signals.py
import json, uuid, os, re
from pathlib import Path
from datetime import datetime, timezone
from dateutil import parser
PREP = Path("data/preprocessed")
OUT = Path("data/signals.jsonl")
OUT.parent.mkdir(parents=True, exist_ok=True)

PII_PAT = re.compile(r'[\w\.-]+@[\w\.-]+|\+?\d[\d\s\-]{7,}\d')
def scrub(t): return PII_PAT.sub("[REDACTED]", t or "")

def to_utc_iso(s):
    if not s: return None
    dt = parser.parse(str(s))
    if not dt.tzinfo: dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()

def normalize_account(x):
    return (x or "").strip().lower().replace("&","and").replace(" ", "_") or None

def main():
    with open(OUT, "w", encoding="utf-8") as out:
        for p in sorted(PREP.glob("*.ndjson")):
            for line in p.read_text(encoding="utf-8").splitlines():
                c = json.loads(line)
                evt = {
                    "event_id": c.get("chunk_id") or str(uuid.uuid4()),
                    "account_id": normalize_account(c.get("account_id") or c.get("customer_id")),
                    "source": c.get("doc_type"),
                    "created_at": to_utc_iso(c.get("date")),
                    "actors": [],  # can be populated by source loaders later
                    "artifacts": [{
                        "type": c.get("doc_type"),
                        "url": c.get("source_path"),
                        "doc_id": c.get("doc_id")
                    }],
                    "text": scrub(c.get("text")),
                    "tags": c.get("tags") or [],
                    "mentions": c.get("mentions") or {"features":[], "competitors":[], "dates":[]},
                    "confidence": 0.8
                }
                if evt["account_id"]:
                    out.write(json.dumps(evt, ensure_ascii=False) + "\n")
    print(f"✅ Wrote {OUT}")

if __name__ == "__main__":
    main()
