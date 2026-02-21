import os
import sys
import shutil
import logging
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ingest import process_file, COLLECTION_NAME, QDRANT_PATH, EMBEDDING_MODEL_NAME

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ingestion():
    # Setup paths
    data_dir = os.path.join(os.path.dirname(__file__), "../data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    sample_file = os.path.join(data_dir, "test_sample.txt")
    
    # Create sample file
    with open(sample_file, "w") as f:
        f.write("Sentinel-Research is an autonomous AI agent system. It uses RAG and web search.")
    
    logger.info(f"Created sample file: {sample_file}")
    
    # Run ingestion
    try:
        process_file(sample_file)
        logger.info("Ingestion process completed.")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return

    # Verify Qdrant
    try:
        client = QdrantClient(path=QDRANT_PATH)
        if client.collection_exists(COLLECTION_NAME):
            info = client.get_collection(COLLECTION_NAME)
            logger.info(f"Collection {COLLECTION_NAME} exists. Point count: {info.points_count}")
            
            if info.points_count > 0:
                logger.info("SUCCESS: Vectors found in Qdrant.")
            else:
                logger.error("FAILURE: No vectors found in Qdrant.")
        else:
            logger.error(f"FAILURE: Collection {COLLECTION_NAME} does not exist.")
            
    except Exception as e:
        logger.error(f"Verification failed: {e}")

    # Cleanup
    # if os.path.exists(sample_file):
    #     os.remove(sample_file)
    # shutil.rmtree(QDRANT_PATH, ignore_errors=True) # Optional: clean up DB

if __name__ == "__main__":
    test_ingestion()
