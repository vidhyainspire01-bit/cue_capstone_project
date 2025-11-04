# common/config.py
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# --- Iteration switch ---------------------------------------------------------
# Set CUE_ITERATION=2 in your env for the Iteration 2 copy (recommended)
CUE_ITERATION = os.getenv("CUE_ITERATION", "1").strip()

# --- Base directories ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = Path(os.getenv("CUE_DATA_RAW", BASE_DIR / "Data sets"))
DATA_PREP = Path(os.getenv("CUE_DATA_PREP", BASE_DIR / "data" / "preprocessed"))

# Separate vector store per iteration (avoids index clashes)
_default_chroma = BASE_DIR / f"chromadb_persist_iter{CUE_ITERATION}"
CHROMA_DB = Path(os.getenv("CUE_CHROMA_DB", _default_chroma))
CHROMA_DB.mkdir(parents=True, exist_ok=True)

# Collection name per iteration
COLLECTION_NAME = os.getenv("CUE_COLLECTION_NAME", f"cue_iter{CUE_ITERATION}")

# Briefs output
BRIEF_OUTPUT = Path(os.getenv("CUE_BRIEF_OUTPUT", BASE_DIR / "data" / "briefs"))
BRIEF_OUTPUT.mkdir(parents=True, exist_ok=True)

# --- OpenAI / Models ----------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
LLM_MODEL   = os.getenv("OPENAI_LLM_MODEL",   "gpt-4o-mini")

# Retrieval / ranking knobs
DEFAULT_TOP_K = int(os.getenv("CUE_TOP_K", "10"))
MAX_CONTEXT_TOKENS = int(os.getenv("CUE_MAX_CONTEXT_TOKENS", "6000"))
USE_RERANKER = os.getenv("CUE_USE_RERANKER", "true").lower() in {"1", "true", "yes"}

# --- UI / API conveniences ----------------------------------------------------
DEFAULT_API_BASE = os.getenv(
    "CUE_API_BASE",
    "http://localhost:8000" if CUE_ITERATION == "1" else "http://localhost:8001",
)
DEFAULT_ACCOUNT = os.getenv("CUE_DEFAULT_ACCOUNT", "Acme Tech")

# --- Sanity helpers -----------------------------------------------------------
def require_api_key() -> None:
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Create a .env with OPENAI_API_KEY=... "
            "or export it in your environment."
        )

def describe() -> str:
    return (
        f"[CUE] Iteration={CUE_ITERATION} | Chroma='{CHROMA_DB}' "
        f"Collection='{COLLECTION_NAME}' | TopK={DEFAULT_TOP_K} "
        f"| Models(embed={EMBED_MODEL}, llm={LLM_MODEL}) | API={DEFAULT_API_BASE}"
    )
