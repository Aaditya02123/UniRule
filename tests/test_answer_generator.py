import pytest
from app.models.schemas import Classification, EvidenceAnalysisResult, RetrievalResult, GeneratedAnswer
from app.services.answer_generator import AnswerGenerator

@pytest.fixture
def generator():
    return AnswerGenerator()

def test_not_covered_generation(generator):
    analysis = EvidenceAnalysisResult(
        classification=Classification.NOT_COVERED,
        supporting_evidence=[],
        conflict_groups={}
    )
    result = generator.generate(analysis)
    
    assert result.classification == Classification.NOT_COVERED
    assert "not provide sufficient information" in result.answer.lower()
    assert len(result.evidence) == 0

def test_answered_generation_single(generator):
    evidence = [
        RetrievalResult(chunk_id="1", document="doc1.pdf", file_type="pdf", text="Single fact.", section="Sec 1", similarity_score=0.9)
    ]
    analysis = EvidenceAnalysisResult(
        classification=Classification.ANSWERED,
        supporting_evidence=evidence
    )
    
    result = generator.generate(analysis)
    assert result.classification == Classification.ANSWERED
    assert "Single fact." in result.answer
    assert "(doc1.pdf, Sec 1)" in result.answer
    assert len(result.evidence) == 1
    assert result.evidence[0].similarity_score == 0.9

def test_multi_document_answered(generator):
    evidence = [
        RetrievalResult(chunk_id="1", document="doc1.pdf", file_type="pdf", text="Fact A.", similarity_score=0.8),
        RetrievalResult(chunk_id="2", document="doc2.md", file_type="md", text="Fact B.", similarity_score=0.75)
    ]
    analysis = EvidenceAnalysisResult(
        classification=Classification.ANSWERED,
        supporting_evidence=evidence
    )
    
    result = generator.generate(analysis)
    assert result.classification == Classification.ANSWERED
    assert "Fact A." in result.answer
    assert "Fact B." in result.answer
    assert "conflicting" not in result.answer.lower()
    assert len(result.evidence) == 2

def test_attendance_conflict(generator):
    groups = {
        "academic_regulations.pdf": [RetrievalResult(chunk_id="1", document="academic_regulations.pdf", file_type="pdf", text="75% minimum", section="Sec 3", similarity_score=0.8)],
        "medical_exemptions.md": [RetrievalResult(chunk_id="2", document="medical_exemptions.md", file_type="md", text="60% limit", section="Sec 2", similarity_score=0.85)]
    }
    
    analysis = EvidenceAnalysisResult(
        classification=Classification.CONFLICT,
        conflict_groups=groups
    )
    
    result = generator.generate(analysis)
    assert result.classification == Classification.CONFLICT
    ans_lower = result.answer.lower()
    assert "conflicting provisions" in ans_lower
    assert "75% minimum" in ans_lower
    assert "60% limit" in ans_lower
    assert "academic_regulations.pdf" in ans_lower
    assert "medical_exemptions.md" in ans_lower
    # Ensure it doesn't try to resolve it
    assert "overrides" not in ans_lower
    assert "precedence" in ans_lower # "does not specify which provision takes precedence"
    assert len(result.evidence) == 2

def test_fee_deadline_conflict(generator):
    groups = {
        "academic_regulations.pdf": [RetrievalResult(chunk_id="1", document="academic_regulations.pdf", file_type="pdf", text="July 15 deadline", similarity_score=0.8)],
        "fee_schedule.csv": [RetrievalResult(chunk_id="2", document="fee_schedule.csv", file_type="csv", text="July 31 deadline", similarity_score=0.85)]
    }
    
    analysis = EvidenceAnalysisResult(
        classification=Classification.CONFLICT,
        conflict_groups=groups
    )
    
    result = generator.generate(analysis)
    assert result.classification == Classification.CONFLICT
    assert "July 15" in result.answer
    assert "July 31" in result.answer

def test_hostel_curfew_conflict(generator):
    groups = {
        "hostel_handbook.pdf": [RetrievalResult(chunk_id="1", document="hostel_handbook.pdf", file_type="pdf", text="10:00 PM curfew", similarity_score=0.8)],
        "student_discipline.md": [RetrievalResult(chunk_id="2", document="student_discipline.md", file_type="md", text="11:00 PM curfew", similarity_score=0.75)]
    }
    
    analysis = EvidenceAnalysisResult(
        classification=Classification.CONFLICT,
        conflict_groups=groups
    )
    
    result = generator.generate(analysis)
    assert result.classification == Classification.CONFLICT
    assert "10:00 PM" in result.answer
    assert "11:00 PM" in result.answer

def test_conflict_evidence_completeness(generator):
    groups = {
        "doc1": [
            RetrievalResult(chunk_id="1", document="doc1", file_type="txt", text="A1", similarity_score=0.9),
            RetrievalResult(chunk_id="2", document="doc1", file_type="txt", text="A2", similarity_score=0.8)
        ],
        "doc2": [
            RetrievalResult(chunk_id="3", document="doc2", file_type="txt", text="B1", similarity_score=0.85)
        ]
    }
    analysis = EvidenceAnalysisResult(classification=Classification.CONFLICT, conflict_groups=groups)
    result = generator.generate(analysis)
    assert result.classification == Classification.CONFLICT
    
    assert len(result.evidence) == 3
    assert set(e.chunk_id for e in result.evidence) == {"1", "2", "3"}

def test_evidence_isolation(generator):
    # Pass an EvidenceAnalysisResult containing only one chunk
    evidence = [
        RetrievalResult(chunk_id="1", document="doc1.pdf", file_type="pdf", text="Expected fact.", similarity_score=0.9)
    ]
    # Simulate some stray RetrievalResult that wasn't included
    stray_evidence = RetrievalResult(chunk_id="2", document="doc2.pdf", file_type="pdf", text="Stray fact.", similarity_score=0.8)
    
    analysis = EvidenceAnalysisResult(
        classification=Classification.ANSWERED,
        supporting_evidence=evidence
    )
    
    result = generator.generate(analysis)
    assert "Stray fact" not in result.answer
    assert len(result.evidence) == 1
    assert result.evidence[0].chunk_id == "1"

def test_determinism(generator):
    groups = {
        "A_doc": [RetrievalResult(chunk_id="1", document="A_doc", file_type="txt", text="A", similarity_score=0.8)],
        "B_doc": [RetrievalResult(chunk_id="2", document="B_doc", file_type="txt", text="B", similarity_score=0.85)]
    }
    analysis = EvidenceAnalysisResult(classification=Classification.CONFLICT, conflict_groups=groups)
    
    result1 = generator.generate(analysis)
    result2 = generator.generate(analysis)
    
    assert result1.answer == result2.answer
    assert result1.evidence == result2.evidence
