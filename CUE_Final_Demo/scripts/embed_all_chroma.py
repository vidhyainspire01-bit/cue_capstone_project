# scripts/embed_all_chroma.py
"""
Embed all preprocessed chunks and upsert into a local Chroma collection.
Uses the modern OpenAI Python API (openai>=1.0.0) via OpenAI client.
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# OpenAI new client
from openai import OpenAI
import numpy as np

# Chroma
import chromadb

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY must be set in environment")

client_oa = OpenAI(api_key=OPENAI_API_KEY)

# Initialize Chroma persistent client
try:
    client = chromadb.PersistentClient(path="chromadb_persist")
except Exception:
    client = chromadb.Client()

COLLECTION_NAME = "cue_chunks"
try:
    collection = client.get_collection(COLLECTION_NAME)
except Exception:
    collection = client.create_collection(name=COLLECTION_NAME)

PREP_ROOT = Path("data/preprocessed")

EMBED_MODEL = "text-embedding-3-small"
BATCH_SIZE = 32          # safer batch size for stability
RETRY_SLEEP = 2.0
MAX_RETRIES = 3

def get_openai_embeddings(texts):
    """
    Uses the new OpenAI client interface:
      client_oa.embeddings.create(model=..., input=[...])
    Returns: list of embedding vectors (lists of floats).
    """
    embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i+BATCH_SIZE]
        attempt = 0
        while True:
            try:
                resp = client_oa.embeddings.create(model=EMBED_MODEL, input=batch)
                # resp.data is a list of objects with .embedding attribute
                embeddings.extend([item.embedding for item in resp.data])
                break
            except Exception as e:
                attempt += 1
                if attempt >= MAX_RETRIES:
                    raise
                print(f"[embed] API error (attempt {attempt}) - sleeping {RETRY_SLEEP}s: {e}")
                time.sleep(RETRY_SLEEP)
    return embeddings

def load_preprocessed_chunks():
    chunks = []
    for p in sorted(PREP_ROOT.glob("*.ndjson")):
        with open(p, "r", encoding="utf-8") as fh:
            for line in fh:
                chunks.append(json.loads(line))
    return chunks

def upsert_to_chroma(chunks):
    if not chunks:
        print("No chunks found in data/preprocessed. Run preprocessing first.")
        return

    ids = [c["chunk_id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [
        {
            "doc_id": c.get("doc_id"),
            "doc_type": c.get("doc_type"),
            "customer_id": c.get("customer_id"),
            "date": c.get("date"),
            "chunk_index": c.get("chunk_index"),
            "source_path": c.get("source_path"),
            "length_words": c.get("length_words"),
        }
        for c in chunks
    ]

    print(f"Requesting embeddings for {len(texts)} chunks (batch_size={BATCH_SIZE})...")
    embeddings = get_openai_embeddings(texts)
    print("Embedding complete. Upserting to Chroma...")

    # Add or upsert depending on Chroma version
    try:
        collection.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
    except Exception:
        collection.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)

    # persist
    try:
        client.persist()
    except Exception:
        pass

    print(f"Upsert complete. Persisted to chroma (path: chromadb_persist).")

if __name__ == "__main__":
    chunks = load_preprocessed_chunks()
    upsert_to_chroma(chunks)
