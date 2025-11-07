# Customer Understanding Engine (CUE)
### Agentic AI for Insights & Decisions

CUE transforms unstructured business data — CRM, support, Slack, usage — into evidence-based executive insights.  
It evolves across iterations:

| Iteration | Theme | Key Capability |
|------------|--------|----------------|
| **1** | Signal Unification | Citable summaries & risk scoring |
| **2** | Semantic RAG + Orchestration | Multi-source reasoning & guardrails |
| **3** | Strategic Portfolio Intelligence | Multi-agent orchestration across accounts |

---

## System Architecture (Iteration 3)────────────────┐
         │              Data Sources                    │
         │  CRM | Slack | Support | Usage | SteerCo     │
         └──────────────────────────────────────────────┘
                              │
                              ▼
     ┌──────────────────────────────────────────────────────┐
     │   MCP-Compatible Retrieval Layer (FastAPI + Chroma)  │
     │  - Unified embeddings, metadata, provenance          │
     │  - Account-aware hybrid retrieval (semantic + keyword)│
     └──────────────────────────────────────────────────────┘
                              │
                              ▼
      ┌────────────────────────────────────────────────────┐
      │           Orchestrator (Iteration 3)               │
      │ - Intent Classifier                                │
      │ - LLM Router & Multi-Agent Manager                 │
      │ - Insight Agent (summarizer)                       │
      │ - Forecast Agent (trend predictor)                 │
      │ - Risk Advisor (portfolio-level)                   │
      └────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌────────────────────────────────────────────────────────┐
    │       Validation & Guardrails                          │
    │  - Evidence Health, Faithfulness, Sensitive Intent     │
    │  - Diversity & Policy Enforcement                      │
    └────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌────────────────────────────────────────────────────────┐
    │              CUE Insights Hub (Frontend)               │
    │  - Briefs | Trends | Ask CUE | Portfolio Overview      │
    │  - Live retrieval status, guardrail badges, citations  │
    └────────────────────────────────────────────────────────┘


---

## 🧮 Core Tech Stack

| Layer | Technology | Purpose |
|--------|-------------|----------|
| **LLM Reasoning** | GPT-4o / GPT-4o-mini | Multi-source summarization, reasoning |
| **Embeddings** | `text-embedding-3-small` | Dense vector retrieval (semantic search) |
| **Vector DB** | ChromaDB (DuckDB + Parquet backend) | Fast persistent similarity search |
| **Backend** | FastAPI | REST orchestration for `/ask`, `/ask2`, `/trends` |
| **Frontend** | Streamlit / Vercel | Interactive insight dashboards |
| **Guardrails** | Custom (Faithfulness, Sensitive Intent, Diversity) | Prevents hallucination or policy violations |

---

## 🧩 Key Components Overview

### **1. Hybrid Retriever (`common/retriever.py`)**
- Combines vector similarity + keyword overlap using RRF.
- Supports account filtering, freshness gating, and multi-source blending.
- Uses ChromaDB with embedding-based querying.

### **2. Summarization & Reasoning (`common/summarizer.py`)**
- GPT-4o-mini summarizer producing Markdown with citable brackets.
- Optional faithfulness checks via validator LLM.

### **3. Guardrails (`common/guards.py`)**
- Sensitive Intent Blocker (detects “private Slack DMs”, “export all messages”).
- Evidence Health Scorer (requires ≥2 strong hits, ≥3 total).
- Diversity Check (ensures cross-source grounding).

### **4. Orchestrator (`api/main.py`)**
- FastAPI router serving:
  - `/ask` — Account-level insight
  - `/ask2` — Multi-source RAG reasoning
  - `/trends` — Portfolio risk aggregation

### **5. Validators (`common/validators.py`)**
- Faithfulness Judge (ensures answer claims match retrieved evidence).
- Citation detector using Markdown-style pattern recognition.

---




---

Ask an Account-Level Question

curl -X POST http://127.0.0.1:8001/ask2 \
  -H "Content-Type: application/json" \
  -d '{
        "account": "Delta Logistics",
        "question": "Why is this customer at risk?"
      }'

Response:

{
  "answer_md": "Delta Logistics shows rising support escalations and usage decline [12].",
  "citations": ["[12] support_tickets_delta_aug.docx"],
  "merged_json": {"account": "Delta Logistics", "signals": [...]} 
}


###  Example Usage
```bash
python -m scripts.generate_brief  "Weekly exec summary for Acme onboarding"


# 1. Create environment
conda create -n cue python=3.10
conda activate cue

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your OpenAI key
export OPENAI_API_KEY="sk-..."

# 4. Run the API
uvicorn api.main:app --reload --port 8001

# 5. (Optional) Launch UI
streamlit run ui/streamlit_app.py


 License

MIT License © 2025 Vidhya Thiruvenkadam
