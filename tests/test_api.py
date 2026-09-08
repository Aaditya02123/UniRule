import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import get_retrieval_service, get_evidence_analyzer, get_answer_generator
from app.models.schemas import Classification, EvidenceAnalysisResult, RetrievalResult, GeneratedAnswer
from app.services.retrieval import RetrievalService
from app.services.evidence_analyzer import EvidenceAnalyzer
from app.services.answer_generator import AnswerGenerator

# --- Mocks ---

class MockRetrievalService:
    def retrieve(self, question: str):
        return []

class MockEvidenceAnalyzer:
    def analyze(self, results):
        return EvidenceAnalysisResult(classification=Classification.NOT_COVERED)

class MockAnswerGenerator:
    def generate(self, analysis):
        if analysis.classification == Classification.ANSWERED:
            return GeneratedAnswer(classification=Classification.ANSWERED, answer="Mock Answer.", evidence=[])
        elif analysis.classification == Classification.CONFLICT:
            return GeneratedAnswer(classification=Classification.CONFLICT, answer="Mock Conflict.", evidence=[])
        return GeneratedAnswer(classification=Classification.NOT_COVERED, answer="Mock Not Covered.", evidence=[])

@pytest.fixture
def client():
    app.dependency_overrides[get_retrieval_service] = MockRetrievalService
    app.dependency_overrides[get_evidence_analyzer] = MockEvidenceAnalyzer
    app.dependency_overrides[get_answer_generator] = MockAnswerGenerator
    
    with TestClient(app) as c:
        yield c
        
    app.dependency_overrides.clear()

def test_health_endpoint(client):
    response = client.get("/health")
    # Note: during testing, pipeline globals might be None unless lifecycle triggered,
    # but the health check should gracefully return status 200 regardless.
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_ask_valid_question(client):
    response = client.post("/ask", json={"question": "What is the fee deadline?"})
    assert response.status_code == 200
    data = response.json()
    assert "classification" in data
    assert "answer" in data
    assert "evidence" in data

def test_ask_empty_question(client):
    # Pydantic validation fails empty string if min_length=1 is used
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 422 
    # Must correctly enforce validation

def test_ask_whitespace_question(client):
    # FastAPI handler enforces stripping checking if it's purely whitespace
    response = client.post("/ask", json={"question": "   \n "})
    assert response.status_code == 422 
    assert "entirely whitespace" in response.json()["detail"]

def test_ask_answered_mock(client):
    class MockAnsweredAnalyzer:
        def analyze(self, results):
            return EvidenceAnalysisResult(classification=Classification.ANSWERED)
            
    app.dependency_overrides[get_evidence_analyzer] = MockAnsweredAnalyzer
    
    response = client.post("/ask", json={"question": "valid?"})
    assert response.status_code == 200
    assert response.json()["classification"] == Classification.ANSWERED.value
    assert "Mock Answer." in response.json()["answer"]

def test_ask_conflict_mock(client):
    class MockConflictAnalyzer:
        def analyze(self, results):
            return EvidenceAnalysisResult(classification=Classification.CONFLICT)
            
    app.dependency_overrides[get_evidence_analyzer] = MockConflictAnalyzer
    
    response = client.post("/ask", json={"question": "conflict?"})
    assert response.status_code == 200
    assert response.json()["classification"] == Classification.CONFLICT.value
    assert "Mock Conflict." in response.json()["answer"]
    
def test_ask_not_covered_mock(client):
    # Uses default mocks 
    response = client.post("/ask", json={"question": "random string?"})
    assert response.status_code == 200
    assert response.json()["classification"] == Classification.NOT_COVERED.value
    assert "Mock Not Covered." in response.json()["answer"]
    assert response.json()["evidence"] == []

def test_service_initialization_uncached():
    # Calling FastAPI natively with no mock dependencies
    client_live = TestClient(app)
    response = client_live.get("/health")
    assert response.status_code == 200
    # Because of context manager TestClient triggers lifespan logic perfectly
    assert response.json()["pipeline_ready"] == True

