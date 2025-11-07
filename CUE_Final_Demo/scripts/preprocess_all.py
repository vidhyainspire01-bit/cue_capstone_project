# scripts/preprocess_all.py
import json
from pathlib import Path
from utils.file_loader import emit_chunks_for_call_file
from utils.crm_loader import emit_chunks_from_crm_file
from utils.product_loader import emit_chunks_from_product_usage
from utils.slack_loader import emit_chunks_from_slack_file
from utils.tickets_loader import emit_chunks_from_ticket_file

RAW_ROOT = Path(r"D:\CUE_\Data sets")  # your base dataset path
PREP_ROOT = Path("data/preprocessed")
PREP_ROOT.mkdir(parents=True, exist_ok=True)

def process_source(name, exts, func):
    src_path = RAW_ROOT / name
    if not src_path.exists():
        print(f"[{name}] ⚠️ Folder not found, skipping.")
        return
    files = [p for p in src_path.rglob("*") if p.is_file() and p.suffix.lower() in exts]
    if not files:
        print(f"[{name}] ⚠️ No matching files found, skipping.")
        return
    for p in files:
        try:
            chunks = func(p)
            if not chunks:
                continue
            out_path = PREP_ROOT / f"{p.stem}.ndjson"
            with open(out_path, "w", encoding="utf-8") as f:
                for c in chunks:
                    f.write(json.dumps(c, ensure_ascii=False) + "\n")
            print(f"[{name}] ✅ wrote {out_path.name} chunks: {len(chunks)}")
        except Exception as e:
            print(f"[{name}] ❌ FAILED {p}: {e}")

def main():
    process_source("Client call transcripts", {".docx", ".json", ".txt"}, emit_chunks_for_call_file)
    process_source("CRM notes", {".docx", ".csv", ".json"}, emit_chunks_from_crm_file)
    process_source("Product usage", {".docx", ".csv", ".json"}, emit_chunks_from_product_usage)
    process_source("Slack messages", {".docx", ".csv", ".json"}, emit_chunks_from_slack_file)
    process_source("Support tickets", {".docx", ".csv", ".json"}, emit_chunks_from_ticket_file)

if __name__ == "__main__":
    main()
