import os
import json
import logging
from pathlib import Path
from typing import List

from app.models.schemas import RetrievalResult, EvidenceAnalysisResult, Classification

logger = logging.getLogger(__name__)

class EvidenceAnalyzer:
    def __init__(self, data_dir: str | Path | None = None):
        self.min_score = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.55"))
        
        # Load contradictions registry
        if data_dir is None:
            # Fallback to standard project structure
            data_dir = Path(__file__).resolve().parent.parent.parent / "data"
        else:
            data_dir = Path(data_dir)
            
        self.contradictions_registry = []
        contradictions_file = data_dir / "contradictions.json"
        
        if contradictions_file.exists():
            try:
                with open(contradictions_file, "r", encoding="utf-8") as f:
                    self.contradictions_registry = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load contradictions registry: {e}")
        else:
            logger.warning(f"Contradictions registry not found at {contradictions_file}")

    def analyze(self, results: List[RetrievalResult]) -> EvidenceAnalysisResult:
        """
        Analyzes retrieved evidence to determine if it can coherently answer the query
        or if there are material contradictions.
        """
        valid_results = [r for r in results if r.similarity_score >= self.min_score]

        if not valid_results:
            return EvidenceAnalysisResult(classification=Classification.NOT_COVERED)

        # Separate into documents to check against known contradictions
        chunks_by_doc = {}
        for r in valid_results:
            if r.document not in chunks_by_doc:
                chunks_by_doc[r.document] = []
            chunks_by_doc[r.document].append(r)

        # Check for known contradictions deterministically
        for contradiction in self.contradictions_registry:
            source_a = contradiction.get("source_A")
            source_b = contradiction.get("source_B")
            
            if not source_a or not source_b:
                continue
                
            # If valid evidence contains both source_A and source_B, we have a material conflict
            if source_a in chunks_by_doc and source_b in chunks_by_doc:
                return EvidenceAnalysisResult(
                    classification=Classification.CONFLICT,
                    supporting_evidence=valid_results,
                    conflict_groups={
                        source_a: chunks_by_doc[source_a],
                        source_b: chunks_by_doc[source_b]
                    }
                )

        # If no deterministic contradiction was found, the evidence is complementary or single-source
        return EvidenceAnalysisResult(
            classification=Classification.ANSWERED,
            supporting_evidence=valid_results
        )
