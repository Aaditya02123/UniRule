import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pathlib import Path

from app.api.routes import router
import app.api.routes as routes
from app.services.retrieval import RetrievalService
from app.services.evidence_analyzer import EvidenceAnalyzer
from app.services.answer_generator import AnswerGenerator
from app.services.embeddings import get_embedding_provider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base directory for storage resolution
BASE_DIR = Path(__file__).resolve().parent.parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager gracefully handles pipeline initialization 
    at application startup safely avoiding per-request index reloading overhead.
    """
    logger.info("Initializing UniRule QA Pipeline...")
    try:
        # Pre-heat the global embedding model precisely once securely inside FastAPI ecosystem
        cached_provider = get_embedding_provider()
        
        # Load indexes from persisted storage safely
        storage_dir = BASE_DIR / "storage"
        if not storage_dir.exists():
            raise FileNotFoundError(f"Storage directory {storage_dir} omitted. Run ingestion/embedding generation first.")
            
        routes._retrieval_service = RetrievalService(storage_dir=storage_dir, embedding_provider=cached_provider)
        routes._evidence_analyzer = EvidenceAnalyzer()
        routes._answer_generator = AnswerGenerator()
        
        logger.info("UniRule QA Pipeline initialized cleanly.")
    except Exception as e:
        logger.error(f"Failed to initialize QA Pipeline: {e}")
        # Allow the application to crash transparently if critical infrastructure misses.
        raise e
        
    yield
    # Safely tear down if necessary
    logger.info("Shutting down... ")

app = FastAPI(
    title="UniRule API",
    description="UniRule University QA Expert System Pipeline",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)
