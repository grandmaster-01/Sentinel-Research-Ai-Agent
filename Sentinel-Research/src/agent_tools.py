import os
import time
import json
from typing import List
from langchain_core.tools import tool
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

# ── Constants ─────────────────────────────────────────────────────────────────
COLLECTION_NAME  = "sentinel_research"
QDRANT_PATH      = "./qdrant_db"
EMBEDDING_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"
BRAVE_API_KEY    = os.getenv("BRAVE_SEARCH_API_KEY", "")

# ── Singletons ────────────────────────────────────────────────────────────────
_qdrant_client = None
_embeddings    = None

def get_qdrant_client():
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(path=QDRANT_PATH)
    return _qdrant_client

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embeddings

# ── Search Backends ───────────────────────────────────────────────────────────

def _brave_search(query: str, max_results: int = 5) -> List[str]:
    """Brave Search via langchain-community BraveSearchWrapper."""
    from langchain_community.utilities.brave_search import BraveSearchWrapper
    wrapper = BraveSearchWrapper(api_key=BRAVE_API_KEY, search_kwargs={"count": max_results})
    raw = wrapper.run(query)            # returns a JSON string
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        # BraveSearchWrapper sometimes returns a plain text string
        return [f"Source 1: Brave Search Result\nContent: {raw}"] if raw else []

    results = []
    # Handle both list-of-dicts and the nested {"web":{"results":[...]}} format
    items = data if isinstance(data, list) else data.get("web", {}).get("results", [])
    for i, item in enumerate(items[:max_results]):
        title   = item.get("title",       "No title")
        url     = item.get("url",         item.get("link", "No URL"))
        snippet = item.get("description", item.get("snippet", "No content"))
        results.append(f"Source {i+1}: {title}\nURL: {url}\nContent: {snippet}")
    return results


def _ddg_search(query: str, max_results: int = 5, retries: int = 2) -> List[str]:
    """DuckDuckGo fallback — compatible with duckduckgo-search v8+."""
    from duckduckgo_search import DDGS
    for attempt in range(retries + 1):
        try:
            ddgs = DDGS(timeout=15)
            raw  = list(ddgs.text(query, max_results=max_results))
            if not raw:
                if attempt < retries:
                    time.sleep(1.5)
                    continue
                return ["Web search returned no results. The LLM will answer from its own knowledge."]
            return [
                f"Source {i+1}: {r.get('title','')}\nURL: {r.get('href','')}\nContent: {r.get('body','')}"
                for i, r in enumerate(raw)
            ]
        except Exception as exc:
            if attempt < retries:
                time.sleep(1.5)
            else:
                return [f"Web search unavailable ({type(exc).__name__}). Answering from model knowledge."]
    return ["Web search unavailable. Answering from model knowledge."]

# ── Tools ─────────────────────────────────────────────────────────────────────

@tool
def retrieve_documents(query: str) -> List[str]:
    """
    Retrieves relevant documents from the local Qdrant vector store (RAG).
    Use when the user asks about uploaded/ingested documents or their knowledge base.
    """
    try:
        if not os.path.exists(QDRANT_PATH):
            return ["No knowledge base found. Please ingest documents first."]
        client = get_qdrant_client()
        if not client.collection_exists(COLLECTION_NAME):
            return ["Knowledge base is empty. Please ingest documents first."]
        vector_store = QdrantVectorStore(
            client=client, collection_name=COLLECTION_NAME, embedding=get_embeddings()
        )
        results = vector_store.similarity_search(query, k=4)
        if not results:
            return ["No relevant documents found for this query."]
        return [
            f"[Doc {i+1} | Source: {os.path.basename(d.metadata.get('source','Unknown'))}]\n{d.page_content}"
            for i, d in enumerate(results)
        ]
    except Exception as e:
        return [f"Error retrieving documents: {e}"]


@tool
def search_web(query: str) -> List[str]:
    """
    Searches the live web for the latest information.
    Uses Brave Search when an API key is configured, otherwise falls back to DuckDuckGo.
    Never raises an exception — returns a graceful fallback message on failure.
    """
    if BRAVE_API_KEY:
        try:
            results = _brave_search(query)
            if results:
                return results
            # Brave returned nothing — fall through to DDGS
        except Exception:
            pass  # Fall through to DDGS
    return _ddg_search(query)
