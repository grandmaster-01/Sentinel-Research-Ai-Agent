import os
import time
import logging
from pathlib import Path
from typing import List

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    UnstructuredMarkdownLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR        = os.path.join(os.path.dirname(__file__), "../data")
COLLECTION_NAME = "sentinel_research"   # must match agent_tools.py
QDRANT_PATH     = os.path.join(os.path.dirname(__file__), "../qdrant_db")
QDRANT_URL      = os.getenv("QDRANT_URL", "")   # set in .env for server mode
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_loader(file_path: str):
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return PyPDFLoader(file_path)
    elif ext == ".txt":
        return TextLoader(file_path, encoding="utf-8")
    elif ext == ".md":
        return UnstructuredMarkdownLoader(file_path)
    elif ext == ".csv":
        return CSVLoader(file_path)
    return None

def get_or_create_collection(client: QdrantClient):
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        logger.info(f"Created collection: {COLLECTION_NAME}")

def process_file(file_path: str) -> dict:
    """
    Processes a single file: load → chunk → embed → upsert into Qdrant.
    Returns a status dict.
    """
    logger.info(f"Processing: {file_path}")
    ext = Path(file_path).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        msg = f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}"
        logger.warning(msg)
        return {"status": "skipped", "message": msg}

    try:
        loader = get_loader(file_path)
        documents = loader.load()

        if not documents:
            return {"status": "error", "message": f"No content found in {file_path}"}

        # Chunk
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = splitter.split_documents(documents)
        logger.info(f"Split into {len(chunks)} chunks.")

        # Embed & upsert
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        if QDRANT_URL:
            client = QdrantClient(url=QDRANT_URL)
        else:
            client = QdrantClient(path=QDRANT_PATH)
        get_or_create_collection(client)

        vector_store = QdrantVectorStore(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding=embeddings,
        )
        vector_store.add_documents(chunks)
        logger.info(f"Indexed {len(chunks)} chunks from {file_path}")

        return {
            "status": "success",
            "file": os.path.basename(file_path),
            "chunks_indexed": len(chunks)
        }

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return {"status": "error", "message": str(e)}

def process_existing_files():
    """Process all supported files already in the data directory."""
    os.makedirs(DATA_DIR, exist_ok=True)
    results = []
    for filename in os.listdir(DATA_DIR):
        if Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS:
            results.append(process_file(os.path.join(DATA_DIR, filename)))
    return results

def get_collection_stats() -> dict:
    """Returns info about the current knowledge base."""
    try:
        if QDRANT_URL:
            try:
                client = QdrantClient(url=QDRANT_URL)
                client.get_collections()  # reachability check
            except Exception:
                # Server not running — fall back to local file
                if not os.path.exists(QDRANT_PATH):
                    return {"status": "empty", "count": 0}
                client = QdrantClient(path=QDRANT_PATH)
        elif not os.path.exists(QDRANT_PATH):
            return {"status": "empty", "count": 0}
        else:
            client = QdrantClient(path=QDRANT_PATH)

        if not client.collection_exists(COLLECTION_NAME):
            return {"status": "empty", "count": 0}
        info = client.get_collection(COLLECTION_NAME)
        return {
            "status": "ready",
            "count": info.points_count,
            "collection": COLLECTION_NAME
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    logger.info("Processing existing files in data/ directory...")
    results = process_existing_files()
    for r in results:
        logger.info(r)
