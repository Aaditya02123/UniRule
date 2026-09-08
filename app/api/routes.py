from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from app.models.schemas import AskRequest, GeneratedAnswer
from app.services.retrieval import RetrievalService
from app.services.evidence_analyzer import EvidenceAnalyzer
from app.services.answer_generator import AnswerGenerator

router = APIRouter()

# Globals to hold pipeline services after startup initialization
_retrieval_service: RetrievalService | None = None
_evidence_analyzer: EvidenceAnalyzer | None = None
_answer_generator: AnswerGenerator | None = None

def get_retrieval_service() -> RetrievalService:
    if not _retrieval_service:
        raise HTTPException(status_code=500, detail="QA pipeline not initialized")
    return _retrieval_service

def get_evidence_analyzer() -> EvidenceAnalyzer:
    if not _evidence_analyzer:
        raise HTTPException(status_code=500, detail="QA pipeline not initialized")
    return _evidence_analyzer
    
def get_answer_generator() -> AnswerGenerator:
    if not _answer_generator:
        raise HTTPException(status_code=500, detail="QA pipeline not initialized")
    return _answer_generator

@router.get("/health", summary="Health check endpoint")
async def health_check() -> Dict[str, Any]:
    pipeline_ready = all([_retrieval_service, _evidence_analyzer, _answer_generator])
    return {
        "status": "ok",
        "pipeline_ready": pipeline_ready
    }

@router.post("/ask", response_model=GeneratedAnswer, summary="Ask a question against the rulebook")
async def ask_question(
    request: AskRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    evidence_analyzer: EvidenceAnalyzer = Depends(get_evidence_analyzer),
    answer_generator: AnswerGenerator = Depends(get_answer_generator)
) -> GeneratedAnswer:
    try:
        if not request.question.strip():
            raise HTTPException(status_code=422, detail="Question cannot be entirely whitespace")
            
        retrieval_results = retrieval_service.retrieve(request.question)
        analysis = evidence_analyzer.analyze(retrieval_results)
        answer = answer_generator.generate(analysis)
        
        return answer
    except HTTPException:
        raise
    except Exception as e:
        # Avoid leaking internal stack trace details in the response
        raise HTTPException(status_code=500, detail="Internal server error executing QA pipeline")
