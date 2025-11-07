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

### 🚀 Tech Stack
- **Frontend:** Streamlit / Vercel Web UI  
- **Backend:** FastAPI + ChromaDB  
- **LLM:** GPT-4o-mini for reasoning and summarization  
- **Retrieval:** Hybrid semantic search (OpenAI text-embedding-3-small)  
- **Guardrails:** Evidence validation, sensitive intent detection  

---

### 🧩 Architecture
![CUE Architecture](assets/cue-architecture.png)

---

### 📘 Example Usage
```bash
python -m scripts.generate_brief  "Weekly exec summary for Acme onboarding"
