# scripts/export_trends.py

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
METRICS_FILE = ROOT / "data" / "metrics" / "brief_runs.jsonl"
OUT_FILE = ROOT / "data" / "metrics" / "trends.json"

def main():
    if not METRICS_FILE.exists():
        print(f"❌ No metrics file found at {METRICS_FILE}")
        return

    df = pd.read_json(METRICS_FILE, lines=True)

    # group by account, keep:
    # - latest risk_level
    # - avg coverage_ratio
    # - avg guardrails_ok (as fraction)
    # - latest ts
    trend = (
        df.sort_values("ts")
          .groupby("account")
          .agg(
              risk_level=("risk_level", "last"),
              coverage_ratio=("coverage_ratio", "mean"),
              guardrails_ok=("guardrails_ok", "mean"),
              ts=("ts", "last"),
          )
          .reset_index()
    )

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    trend.to_json(OUT_FILE, orient="records", indent=2)
    print(f"✅ Trends exported to {OUT_FILE}")

if __name__ == "__main__":
    main()
