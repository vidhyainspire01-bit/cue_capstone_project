import pandas as pd
import json
from pathlib import Path

f = Path("data/metrics/brief_runs.jsonl")
df = pd.read_json(f, lines=True)
trend = df.groupby("account").agg({
    "risk_level": lambda x: x.iloc[-1],
    "coverage_ratio": "mean",
    "guardrails_ok": "mean",
    "ts": "max"
})
trend.to_json("data/metrics/trends.json", orient="records")
print("✅ Trends exported.")
