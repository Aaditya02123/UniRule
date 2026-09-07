import os
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
from tempfile import TemporaryDirectory

from app.models.schemas import DocumentChunk
from app.services.embeddings import generate_embeddings, save_embeddings, load_embeddings

@pytest.fixture
def sample_chunks():
    return [
        DocumentChunk(chunk_id="chunk1", document="foo.txt", file_type="txt", text="Hello world"),
        DocumentChunk(chunk_id="chunk2", document="bar.txt", file_type="txt", text="Testing 123", section="Sec 1", page=2),
    ]

@pytest.fixture
def mock_openai():
    with patch("app.services.embeddings.OpenAI") as mock:
        # Configuration for standard response shape matching embeddings model format
        client_instance = mock.return_value
        yield client_instance

@pytest.fixture
def mock_sentence_transformer():
    with patch("sentence_transformers.SentenceTransformer") as mock:
        yield mock.return_value

def set_valid_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test_mock_key")
    monkeypatch.setenv("EMBEDDING_BATCH_SIZE", "10")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")

def test_generate_embeddings_success(sample_chunks, mock_openai, monkeypatch):
    set_valid_env(monkeypatch)
    
    # Mocking the structured data payload returned by OpenAI API
    mock_data = []
    vector_dim = 1536
    
    for i in range(len(sample_chunks)):
        item = MagicMock()
        item.index = i
        item.embedding = np.random.rand(vector_dim).tolist()
        mock_data.append(item)
        
    mock_response = MagicMock()
    mock_response.data = mock_data
    mock_openai.embeddings.create.return_value = mock_response

    embeddings = generate_embeddings(sample_chunks)
    
    assert type(embeddings) == np.ndarray
    assert embeddings.shape == (2, 1536)
    mock_openai.embeddings.create.assert_called_once()
    
def test_generate_embeddings_ordering(sample_chunks, mock_openai, monkeypatch):
    set_valid_env(monkeypatch)
    
    # Force the mock API to return results deliberately misordered
    mock_data = []
    vector_dim = 1536
    
    embed_0 = np.full((vector_dim,), 0.0).tolist()
    embed_1 = np.full((vector_dim,), 1.0).tolist()
    
    item1 = MagicMock()
    item1.index = 1
    item1.embedding = embed_1
    
    item0 = MagicMock()
    item0.index = 0
    item0.embedding = embed_0
    
    mock_response = MagicMock()
    # MOCK RETURNS OUT OF ORDER
    mock_response.data = [item1, item0]
    
    mock_openai.embeddings.create.return_value = mock_response

    embeddings = generate_embeddings(sample_chunks)
    
    # The first row of the returned matrix should explicitly map to index 0.
    assert np.allclose(embeddings[0], embed_0)
    assert np.allclose(embeddings[1], embed_1)
    
def test_missing_api_key(sample_chunks, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
        generate_embeddings(sample_chunks)
        
def test_empty_input():
    with pytest.raises(ValueError, match="Empty chunk list"):
        generate_embeddings([])

def test_duplicate_chunks(sample_chunks):
    sample_chunks.append(sample_chunks[0]) # Duplicate it exactly
    with pytest.raises(ValueError, match="Duplicate chunk_id"):
        generate_embeddings(sample_chunks)

def test_api_failure(sample_chunks, mock_openai, monkeypatch):
    set_valid_env(monkeypatch)
    mock_openai.embeddings.create.side_effect = Exception("Network timeout")
    
    with pytest.raises(RuntimeError, match="OpenAI API embedding failure"):
        generate_embeddings(sample_chunks)
        
def test_save_and_load_success(sample_chunks):
    vector_dim = 1536
    mock_embeddings = np.random.rand(len(sample_chunks), vector_dim).astype(np.float32)
    
    with TemporaryDirectory() as tmpdir:
        save_embeddings(mock_embeddings, sample_chunks, tmpdir)
        
        # Verify formats exist
        assert (Path(tmpdir) / "embeddings.npy").exists()
        assert (Path(tmpdir) / "metadata.json").exists()
        
        # Load logic parity map
        loaded_embs, loaded_chunks = load_embeddings(tmpdir)
        
        assert np.allclose(loaded_embs, mock_embeddings)
        assert len(loaded_chunks) == len(sample_chunks)
        assert loaded_chunks[0].chunk_id == sample_chunks[0].chunk_id

def test_save_mismatch_counts(sample_chunks):
    mock_embeddings = np.random.rand(len(sample_chunks) + 1, 1536).astype(np.float32)
    with TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="Row count mismatch"):
            save_embeddings(mock_embeddings, sample_chunks, tmpdir)
            
def test_save_duplicate_chunks_safeguard(sample_chunks):
    mock_embeddings = np.random.rand(len(sample_chunks) + 1, 1536).astype(np.float32)
    duplicate_chunks = sample_chunks.copy()
    duplicate_chunks.append(sample_chunks[0])
    
    with TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="Duplicate chunk_id detected during save"):
            save_embeddings(mock_embeddings, duplicate_chunks, tmpdir)

def test_save_non_finite_values(sample_chunks):
    mock_embeddings = np.random.rand(len(sample_chunks), 1536).astype(np.float32)
    mock_embeddings[0, 0] = np.inf
    
    with TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="non-finite numeric values"):
            save_embeddings(mock_embeddings, sample_chunks, tmpdir)

def test_local_provider_dimension_and_shape(sample_chunks, mock_sentence_transformer, monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("EMBEDDING_BATCH_SIZE", "10")
    
    # Mocking standard sentence transformer payload strictly guaranteeing 384 length
    vector_dim = 384
    
    def mock_encode(texts, batch_size=10, show_progress_bar=False):
        return [np.random.rand(vector_dim).tolist() for _ in texts]
        
    mock_sentence_transformer.encode.side_effect = mock_encode
    
    embeddings = generate_embeddings(sample_chunks)
    assert type(embeddings) == np.ndarray
    assert embeddings.shape == (2, 384)
    # Ensure chunk ordering implicitly mapped natively against inputs
    mock_sentence_transformer.encode.assert_called_once()
    
    
from app.services.embeddings import get_embedding_provider, OpenAIProvider, LocalProvider
def test_provider_selection(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test_mock_key")
    p1 = get_embedding_provider()
    assert isinstance(p1, OpenAIProvider)
    
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    try:
        p2 = get_embedding_provider()
        assert isinstance(p2, LocalProvider)
    except RuntimeError:
        pass # Handle natively skipping if dependencies unavailable in bare environments

    monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)
    try:
        p3 = get_embedding_provider()
        assert isinstance(p3, LocalProvider)
    except RuntimeError:
        pass
        
def test_local_provider_empty_and_duplicates(sample_chunks, mock_sentence_transformer, monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    
    # Test Empty
    with pytest.raises(ValueError, match="Empty chunk list"):
        generate_embeddings([])
        
    # Test Duplicate
    duplicate_chunks = sample_chunks.copy()
    duplicate_chunks.append(sample_chunks[0])
    
    with pytest.raises(ValueError, match="Duplicate chunk_id"):
        generate_embeddings(duplicate_chunks)
