import os
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
from tempfile import TemporaryDirectory

from app.models.schemas import DocumentChunk, RetrievalResult
from app.services.retrieval import cosine_similarity, RetrievalService
from app.services.embeddings import save_embeddings

@pytest.fixture
def mock_storage():
    with TemporaryDirectory() as tmpdir:
        chunks = [
            DocumentChunk(chunk_id="chunkA", document="A", file_type="txt", text="Test A"),
            DocumentChunk(chunk_id="chunkB", document="B", file_type="txt", text="Test B"),
            DocumentChunk(chunk_id="chunkC", document="C", file_type="txt", text="Test C"),
            DocumentChunk(chunk_id="chunkD", document="D", file_type="txt", text="Test D")
        ]
        
        # Dimensions = 4
        # We will make A perfectly match query, B perfectly inverse, C orthogonal, D identical to A for tie breaking
        matrix = np.array([
            [1.0, 0.0, 0.0, 0.0],  # A (Score: 1.0)
            [-1.0, 0.0, 0.0, 0.0], # B (Score: -1.0)
            [0.0, 1.0, 0.0, 0.0],  # C (Score: 0.0)
            [1.0, 0.0, 0.0, 0.0]   # D (Score: 1.0) - tie with A
        ], dtype=np.float32)
        
        save_embeddings(matrix, chunks, tmpdir)
        yield tmpdir
        
@pytest.fixture
def valid_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "mock_key")
    monkeypatch.setenv("RETRIEVAL_TOP_K", "3")
    monkeypatch.setenv("RETRIEVAL_MIN_SCORE", "0.5")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")

@pytest.fixture
def mock_openai():
    with patch("app.services.embeddings.OpenAI") as mock:
        client_instance = mock.return_value
        yield client_instance
        
def test_cosine_similarity_basic():
    query = np.array([1, 0], dtype=np.float32)
    docs = np.array([
        [1, 0],
        [0, 1],
        [-1, 0]
    ], dtype=np.float32)
    
    sim = cosine_similarity(query, docs)
    assert np.allclose(sim, [1.0, 0.0, -1.0])
    
def test_cosine_similarity_zero_query():
    query = np.array([0, 0], dtype=np.float32)
    docs = np.array([[1, 0], [0, 1]], dtype=np.float32)
    
    sim = cosine_similarity(query, docs)
    assert np.allclose(sim, [0.0, 0.0])
    
def test_cosine_similarity_zero_doc():
    query = np.array([1, 0], dtype=np.float32)
    docs = np.array([[0, 0]], dtype=np.float32)
    
    sim = cosine_similarity(query, docs)
    assert np.allclose(sim, [0.0])

def test_cosine_similarity_dimension_mismatch():
    query = np.array([1, 0, 0], dtype=np.float32)
    docs = np.array([[1, 0]], dtype=np.float32)
    
    with pytest.raises(ValueError, match="Dimension mismatch"):
        cosine_similarity(query, docs)

def test_cosine_similarity_nan_check():
    query = np.array([np.nan, 0], dtype=np.float32)
    docs = np.array([[1, 0]], dtype=np.float32)
    with pytest.raises(ValueError, match="non-finite"):
        cosine_similarity(query, docs)
        
def test_retrieval_ranking_and_tie_breaking(mock_storage, valid_env, mock_openai):
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[1.0, 0.0, 0.0, 0.0])]
    mock_openai.embeddings.create.return_value = mock_response
    
    service = RetrievalService(mock_storage)
    results = service.retrieve("Query?")
    
    # Expected scores: A=1.0, B=-1.0, C=0.0, D=1.0
    # Threshold = 0.5. Top K = 3
    # A and D should be returned. B, C dropped.
    # Because A and D tie, chunkA comes before chunkD ascending.
    
    assert len(results) == 2
    assert results[0].chunk_id == "chunkA"
    assert results[0].similarity_score == 1.0
    
    assert results[1].chunk_id == "chunkD"
    assert results[1].similarity_score == 1.0

def test_retrieval_empty_result(mock_storage, valid_env, mock_openai):
    mock_response = MagicMock()
    # Query is orthogonal to everything threshold
    mock_response.data = [MagicMock(embedding=[0.0, 0.0, 1.0, 0.0])]
    mock_openai.embeddings.create.return_value = mock_response
    
    service = RetrievalService(mock_storage)
    results = service.retrieve("Query?")
    
    # C hits 1.0, but wait, C is orthogonal to C? Wait, C in DB is [0,1,0,0]. This query is [0,0,1,0].
    # C score = 0.0
    # All scores are 0.0. Threshold is 0.5. Therefore empty!
    assert len(results) == 0

def test_retrieval_missing_key(mock_storage, valid_env, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    service = RetrievalService(mock_storage)
    with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
        service.retrieve("Test")
        
def test_malformed_storage_dimensions():
    with TemporaryDirectory() as tmpdir:
        chunks = [DocumentChunk(chunk_id="x", document="doc", file_type="txt", text="Test")]
        # Write corrupted 3D matrix
        matrix = np.zeros((1, 1, 1), dtype=np.float32)
        
        # Manually save to bypass save_embeddings safety bounds explicitly
        np.save(Path(tmpdir) / "embeddings.npy", matrix)
        with open(Path(tmpdir) / "metadata.json", "w") as f:
            import json
            json.dump([c.model_dump() for c in chunks], f)
            
        with pytest.raises(ValueError, match="Corrupted storage matrix dimensionality"):
            RetrievalService(tmpdir)
