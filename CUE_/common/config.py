from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = BASE_DIR / "Data sets"
DATA_PREP = BASE_DIR / "data" / "preprocessed"
CHROMA_DB = BASE_DIR / "chromadb_persist"

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"

# Default values
DEFAULT_TOP_K = 10
BRIEF_OUTPUT = BASE_DIR / "data" / "briefs"
