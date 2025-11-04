# common/llm_client.py
from typing import List, Dict, Any
import os
from openai import OpenAI
from .config import OPENAI_API_KEY, LLM_MODEL

_client = None

def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY or os.getenv("OPENAI_API_KEY"))
    return _client

def chat(messages: List[Dict[str, str]], model: str = LLM_MODEL) -> str:
    resp = client().chat.completions.create(model=model, messages=messages)
    return resp.choices[0].message.content.strip()
