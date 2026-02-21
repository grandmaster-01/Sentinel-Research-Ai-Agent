"""
models.py — Centralized LLM loader for Sentinel.

  RAG    → phi3.5:latest      (Retrieval-Augmented Generation)
  Fast   → llama3.2:3b        (Quick answers with web search)
  Deep   → gemma3:latest      (Full research pipeline)
  Coding → qwen2.5:7b-instruct (Code generation)
"""
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# These defaults MUST match `ollama list` output exactly (including :tag)
MODEL_RAG    = os.getenv("OLLAMA_MODEL_RAG",    "phi3.5:latest")
MODEL_FAST   = os.getenv("OLLAMA_MODEL_FAST",   "llama3.2:3b")
MODEL_DEEP   = os.getenv("OLLAMA_MODEL_DEEP",   "gemma3:latest")
MODEL_CODING = os.getenv("OLLAMA_MODEL_CODING", "qwen2.5:7b-instruct")

_llm_cache: dict = {}


def _get_llm(model_name: str):
    if model_name not in _llm_cache:
        from langchain_ollama import ChatOllama
        _llm_cache[model_name] = ChatOllama(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            timeout=300,          # 5-min timeout — prevents "not found" on cold starts
            keep_alive="10m",     # keep model warm between requests
        )
    return _llm_cache[model_name]


def get_rag_llm():    return _get_llm(MODEL_RAG)
def get_fast_llm():   return _get_llm(MODEL_FAST)
def get_deep_llm():   return _get_llm(MODEL_DEEP)
def get_coding_llm(): return _get_llm(MODEL_CODING)


def detect_coding_query(query: str) -> bool:
    keywords = [
        "code", "program", "script", "function", "class", "method",
        "bug", "error", "exception", "debug", "implement", "algorithm",
        "python", "javascript", "java", "c++", "typescript", "rust",
        "golang", "sql", "regex", "api", "library", "framework",
        "syntax", "compile", "runtime", "loop", "array", "list",
        "dictionary", "object", "module", "import", "git", "docker",
        "refactor", "optimize", "snippet", "write me",
    ]
    lower = query.lower()
    return any(kw in lower for kw in keywords)


def model_info() -> dict:
    return {
        "rag":    {"model": MODEL_RAG,    "purpose": "RAG — Phi 3.5"},
        "fast":   {"model": MODEL_FAST,   "purpose": "Fast — Llama 3.2"},
        "deep":   {"model": MODEL_DEEP,   "purpose": "Deep — Gemma 3"},
        "coding": {"model": MODEL_CODING, "purpose": "Coding — Qwen 2.5"},
    }
