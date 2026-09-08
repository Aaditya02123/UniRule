import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch

from app.models.schemas import RetrievalResult, EvidenceAnalysisResult, Classification
from app.services.evidence_analyzer import EvidenceAnalyzer

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("RETRIEVAL_MIN_SCORE", "0.55")

@pytest.fixture
def test_data_dir(tmp_path):
    contradictions = [
        {
            "contradiction_id": "C01",
            "source_A": "academic_regulations.pdf",
            "source_B": "medical_exemptions.md"
        },
        {
            "contradiction_id": "C02",
            "source_A": "academic_regulations.pdf",
            "source_B": "fee_schedule.csv"
        },
        {
            "contradiction_id": "C03",
            "source_A": "hostel_handbook.pdf",
            "source_B": "student_discipline.md"
        }
    ]
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    with open(data_dir / "contradictions.json", "w") as f:
        json.dump(contradictions, f)
    return data_dir

@pytest.fixture
def analyzer(test_data_dir):
    return EvidenceAnalyzer(data_dir=test_data_dir)

def test_empty_input_not_covered(analyzer):
    result = analyzer.analyze([])
    assert result.classification == Classification.NOT_COVERED
    assert len(result.supporting_evidence) == 0

def test_all_chunks_below_threshold_not_covered(analyzer):
    results = [
        RetrievalResult(chunk_id="1", document="doc1.pdf", file_type="pdf", text="test", similarity_score=0.54)
    ]
    result = analyzer.analyze(results)
    assert result.classification == Classification.NOT_COVERED
    assert len(result.supporting_evidence) == 0

def test_one_relevant_source_answered(analyzer):
    results = [
        RetrievalResult(chunk_id="1", document="academic_regulations.pdf", file_type="pdf", text="test", similarity_score=0.60)
    ]
    result = analyzer.analyze(results)
    assert result.classification == Classification.ANSWERED
    assert len(result.supporting_evidence) == 1

def test_multiple_relevant_sources_non_conflicting_answered(analyzer):
    # 'doc1.pdf' and 'doc2.md' are not a known contradiction pair
    results = [
        RetrievalResult(chunk_id="1", document="doc1.pdf", file_type="pdf", text="test", similarity_score=0.60),
        RetrievalResult(chunk_id="2", document="doc2.md", file_type="md", text="test2", similarity_score=0.62)
    ]
    result = analyzer.analyze(results)
    assert result.classification == Classification.ANSWERED
    assert len(result.supporting_evidence) == 2
    assert "doc1.pdf" not in result.conflict_groups

def test_attendance_contradiction(analyzer):
    results = [
        RetrievalResult(chunk_id="1", document="academic_regulations.pdf", file_type="pdf", text="75% required", similarity_score=0.70),
        RetrievalResult(chunk_id="2", document="medical_exemptions.md", file_type="md", text="60% allowed", similarity_score=0.68)
    ]
    result = analyzer.analyze(results)
    assert result.classification == Classification.CONFLICT
    assert len(result.supporting_evidence) == 2
    assert "academic_regulations.pdf" in result.conflict_groups
    assert "medical_exemptions.md" in result.conflict_groups

def test_fee_deadline_contradiction(analyzer):
    results = [
        RetrievalResult(chunk_id="1", document="academic_regulations.pdf", file_type="pdf", text="July 15", similarity_score=0.66),
        RetrievalResult(chunk_id="2", document="fee_schedule.csv", file_type="csv", text="July 31", similarity_score=0.58) # Over 0.55 threshold
    ]
    result = analyzer.analyze(results)
    assert result.classification == Classification.CONFLICT
    assert len(result.conflict_groups) == 2

def test_hostel_curfew_contradiction(analyzer):
    results = [
        RetrievalResult(chunk_id="1", document="hostel_handbook.pdf", file_type="pdf", text="10 PM", similarity_score=0.60),
        RetrievalResult(chunk_id="2", document="student_discipline.md", file_type="md", text="11 PM", similarity_score=0.65)
    ]
    result = analyzer.analyze(results)
    assert result.classification == Classification.CONFLICT
    assert len(result.conflict_groups) == 2

def test_only_one_side_of_contradiction_not_conflict(analyzer):
    results = [
        RetrievalResult(chunk_id="1", document="academic_regulations.pdf", file_type="pdf", text="July 15", similarity_score=0.66)
    ]
    result = analyzer.analyze(results)
    assert result.classification == Classification.ANSWERED
    assert len(result.conflict_groups) == 0

def test_unsupported_laptop_style_query_not_covered(analyzer):
    # Real test script uses the retriever which will return empty or chunks below 0.55.
    # We will simulate chunks below threshold.
    results = [
        RetrievalResult(chunk_id="1", document="academic_regulations.pdf", file_type="pdf", text="irrelevant", similarity_score=0.30),
        RetrievalResult(chunk_id="2", document="hostel_handbook.pdf", file_type="pdf", text="irrelevant2", similarity_score=0.40)
    ]
    result = analyzer.analyze(results)
    assert result.classification == Classification.NOT_COVERED
