import streamlit as st
import requests
import pandas as pd
from pathlib import Path
from urllib.parse import quote
import json

API = "http://localhost:8000"

st.set_page_config(page_title="CUE — Exec Brief (Iter 3)", layout="wide")
st.title("CUE — Signal Unification & Citable Summaries (Iteration 3)")

# --- load accounts ---
try:
    acc_resp = requests.get(f"{API}/accounts", timeout=15)
    acc_resp.raise_for_status()
    accounts = acc_resp.json()["accounts"]
except Exception as e:
    st.error(f"Could not load accounts from API: {e}")
    st.stop()

selected = st.sidebar.selectbox("Choose account", accounts)

if st.sidebar.button("Generate / Refresh Brief"):
    st.session_state.pop("brief", None)

# --- fetch brief ---
def fetch_brief(account_label: str):
    url = f"{API}/brief/{quote(account_label, safe='')}"
    resp = requests.get(url, timeout=90)

    if resp.status_code == 404:
        st.warning("No recent evidence for this account.")
        st.stop()

    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        st.error(f"Brief generation failed ({resp.status_code}): {detail[:600]}")
        st.stop()

    return resp.json()

if "brief" not in st.session_state:
    st.session_state["brief"] = fetch_brief(selected)

if st.session_state["brief"]["account"] != selected:
    st.session_state["brief"] = fetch_brief(selected)

data = st.session_state["brief"]

# =========================================================
# TABS: 📄 Brief  |  📊 Trends
# =========================================================
tab_brief, tab_trends = st.tabs(["📄 Brief", "📊 Trends"])

# ---------------------------------------------------------
# TAB 1: Brief
# ---------------------------------------------------------
with tab_brief:
    cols = st.columns(4)

    # Risk level
    with cols[0]:
        st.metric("Risk Level", data.get("risk_level", "Medium"))
        if data.get("risk_reason"):
            st.caption(data["risk_reason"])

    # Coverage
    coverage = data.get("coverage", {}) or {}
    ratio = float(coverage.get("ratio", 0)) if coverage else 0.0
    present = ", ".join(coverage.get("present", [])) if coverage else "N/A"
    with cols[1]:
        st.metric("Source Coverage", f"{ratio:.0%}")
        st.caption(f"Sources: {present}")

    # Guardrails
    gr = data.get("guardrails", {}) or {}
    status_label = "Pass" if gr.get("ok", True) else "Review"
    status_icon = "✔️" if gr.get("ok", True) else "⚠️"
    with cols[2]:
        st.metric("Guardrails", f"{status_icon} {status_label}")
        if gr.get("usage_conflict"):
            st.caption("Usage signals conflict across sources.")
        if gr.get("pii_flag"):
            st.caption("Potential PII detected in output.")

    # Run type
    with cols[3]:
        st.metric("Run Type", "Demo (Iter-3)")
        st.caption("Agentic pipeline: retrieve → analyze → finalize.")

    st.markdown("---")
    st.markdown(data["markdown"])

    # Sidebar summary
    st.sidebar.header("Summary")
    st.sidebar.metric("Risk", data.get("risk_level", "Medium"))
    if gr.get("ok", True):
        st.sidebar.success("Guardrails: OK")
    else:
        st.sidebar.error("Guardrails: Review output")
    st.sidebar.caption(
        "All bullets require citations; guardrails enforce schema, "
        "basic consistency checks & (stub) PII checks."
    )

# ---------------------------------------------------------
# TAB 2: Trends  (uses data/metrics/brief_runs.jsonl)
# ---------------------------------------------------------
with tab_trends:
    st.subheader(f"Trends for {selected}")

    metrics_path = (
        Path(__file__).resolve().parents[1] /
        "data" / "metrics" / "brief_runs.jsonl"
    )

    if not metrics_path.exists():
        st.info("No historical runs logged yet. Generate a few briefs first.")
    else:
        rows = []
        with metrics_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue

        # Filter for current account
        rows = [r for r in rows if r.get("account") == selected]

        if not rows:
            st.info(f"No runs logged yet for {selected}.")
        else:
            # Map risk to numeric for chart
            risk_map = {"Low": 0, "Medium": 1, "High": 2}
            df = pd.DataFrame(rows)

            # Ensure required cols
            df["risk_score"] = df["risk_level"].map(
                lambda x: risk_map.get(x, 1)
            )
            df["coverage_ratio"] = df.get("coverage_ratio", 0.0)
            df["guardrails_ok"] = df.get("guardrails_ok", True).astype(int)

            df = df.sort_values("ts")

            st.markdown("**Risk Level Over Time** (0=Low, 1=Medium, 2=High)")
            st.line_chart(df.set_index("ts")[["risk_score"]])

            st.markdown("**Coverage Ratio Over Time**")
            st.line_chart(df.set_index("ts")[["coverage_ratio"]])

            st.markdown("**Guardrails Pass Rate Over Time** (1=OK, 0=Review)")
            st.line_chart(df.set_index("ts")[["guardrails_ok"]])

            st.caption(
                "These metrics are logged automatically from each brief run; "
                "you can also stream them into Opik for richer evaluation."
            )
