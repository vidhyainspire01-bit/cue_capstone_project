# # ui/app.py
# import streamlit as st
# import requests
# from urllib.parse import quote

# API = "http://localhost:8000"  # no secrets needed for local demo

# st.set_page_config(page_title="CUE — Iteration 1", layout="wide")
# st.title("CUE — Signal Unification & Citable Summaries (Iteration 1)")

# # --- load accounts ---
# try:
#     acc_resp = requests.get(f"{API}/accounts", timeout=20)
#     acc_resp.raise_for_status()
#     accounts = acc_resp.json()["accounts"]  # ["Acme Tech", "Beta Corp", ...]
# except Exception as e:
#     st.error(f"Could not load accounts from API: {e}")
#     st.stop()

# selected = st.sidebar.selectbox("Choose account", accounts)

# if st.sidebar.button("Generate / Refresh Brief"):
#     st.session_state.pop("brief", None)

# # --- fetch brief (URL-encode the account name) ---
# def fetch_brief(account_label: str):
#     url = f"{API}/brief/{quote(account_label, safe='')}"
#     resp = requests.get(url, timeout=60)
#     if resp.status_code == 404:
#         st.warning("No recent evidence for this account. Try another or ingest more data.")
#         st.stop()
#     resp.raise_for_status()
#     try:
#         return resp.json()  # {"account": "...", "markdown": "..."}
#     except requests.exceptions.JSONDecodeError:
#         st.error(f"API did not return JSON.\n\nRaw response:\n{resp.text[:600]}")
#         st.stop()

# if "brief" not in st.session_state:
#     st.session_state["brief"] = fetch_brief(selected)

# # re-fetch if user changed selection after we cached
# if st.session_state["brief"]["account"] != selected:
#     st.session_state["brief"] = fetch_brief(selected)

# data = st.session_state["brief"]
# st.markdown(data["markdown"])

# st.sidebar.header("Early Warning")
# st.sidebar.metric("Risk Level", data.get("risk_level", "Medium"))
# if data.get("risk_reason"):
#     st.sidebar.caption(data["risk_reason"])
    
# # simple Early Warning badge from text heuristics
# import re
# brief_text = data["markdown"].lower()
# risk = "Medium"
# if re.search(r"\bp0\b|escalation|outage|sev|drop|decrease|\b-\d+%|\b\d+% drop", brief_text):
#     risk = "High"
# elif re.search(r"\bpositive nps|renewal confirmed|adoption up|\b\d+% increase", brief_text):
#     risk = "Low"

# st.sidebar.header("Early Warning")
# st.sidebar.metric("Risk Level", risk)


import streamlit as st
import requests
from urllib.parse import quote

API = "http://localhost:8000"  # local demo

st.set_page_config(page_title="CUE — Iteration 1", layout="wide")
st.title("CUE — Signal Unification & Citable Summaries (Iteration 3)")

# --- load accounts ---
try:
    acc_resp = requests.get(f"{API}/accounts", timeout=20)
    acc_resp.raise_for_status()
    accounts = acc_resp.json()["accounts"]
except Exception as e:
    st.error(f"Could not load accounts from API: {e}")
    st.stop()

selected = st.sidebar.selectbox("Choose account", accounts)
if st.sidebar.button("Generate / Refresh Brief"):
    st.session_state.pop("brief", None)

# --- fetch brief (URL-encode the account name) ---
def fetch_brief(account_label: str):
    url = f"{API}/brief/{quote(account_label, safe='')}"
    resp = requests.get(url, timeout=60)
    if resp.status_code >= 400:
        # show backend error detail if present
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        st.error(f"Brief generation failed ({resp.status_code}): {detail[:600]}")
        st.stop()
    try:
        return resp.json()  # {"account","markdown","risk_level","risk_reason"}
    except Exception:
        st.error(f"API did not return JSON.\n\nRaw response:\n{resp.text[:600]}")
        st.stop()

if "brief" not in st.session_state:
    st.session_state["brief"] = fetch_brief(selected)

# re-fetch if user changed selection after we cached
if st.session_state["brief"]["account"] != selected:
    st.session_state["brief"] = fetch_brief(selected)

data = st.session_state["brief"]

# --- render brief ---
st.markdown(data["markdown"])

# --- Early Warning (from backend) ---
st.sidebar.header("Early Warning")
st.sidebar.metric("Risk Level", data.get("risk_level", "Medium"))
if data.get("risk_reason"):
    st.sidebar.caption(data["risk_reason"])
