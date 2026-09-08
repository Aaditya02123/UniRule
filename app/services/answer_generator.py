import logging
from typing import List, cast

from app.models.schemas import (
    Classification, 
    EvidenceAnalysisResult, 
    RetrievalResult,
    GeneratedAnswer
)

logger = logging.getLogger(__name__)

class DeterministicAnswerGenerator:
    """
    A deterministic template-based answer generator that safely constructs 
    answers solely from provided EvidenceAnalysisResult without querying external APIs.
    """
    def generate(self, analysis_result: EvidenceAnalysisResult) -> GeneratedAnswer:
        if analysis_result.classification == Classification.NOT_COVERED:
            return self._generate_not_covered(analysis_result)
        elif analysis_result.classification == Classification.CONFLICT:
            return self._generate_conflict(analysis_result)
        else:
            return self._generate_answered(analysis_result)
            
    def _generate_not_covered(self, analysis_result: EvidenceAnalysisResult) -> GeneratedAnswer:
        return GeneratedAnswer(
            classification=Classification.NOT_COVERED,
            answer="The rulebook does not provide sufficient information to answer this question.",
            evidence=[]
        )
        
    def _generate_answered(self, analysis_result: EvidenceAnalysisResult) -> GeneratedAnswer:
        lines = ["According to the university rulebook:"]
        
        for e in analysis_result.supporting_evidence:
            passage = self._clean_text(e.text)
            meta_str = self._format_meta(e)
            lines.append(f" - {passage}{meta_str}")
            
        return GeneratedAnswer(
            classification=Classification.ANSWERED,
            answer="\n".join(lines),
            evidence=analysis_result.supporting_evidence
        )
        
    def _generate_conflict(self, analysis_result: EvidenceAnalysisResult) -> GeneratedAnswer:
        lines = ["The rulebook contains conflicting provisions regarding this topic:"]
        
        all_evidence = []
        
        # Sort conflict groups by name for determinism
        for source in sorted(analysis_result.conflict_groups.keys()):
            chunks = analysis_result.conflict_groups[source]
            lines.append(f"\nFrom {source}:")
            for chunk in chunks:
                all_evidence.append(chunk)
                passage = self._clean_text(chunk.text)
                meta_str = self._format_meta(chunk, include_doc=False)
                lines.append(f" - {passage}{meta_str}")
                
        lines.append("\nThe corpus does not specify which provision takes precedence. Please consult the relevant university authority.")
        
        return GeneratedAnswer(
            classification=Classification.CONFLICT,
            answer="\n".join(lines),
            evidence=all_evidence
        )
        
    def _format_meta(self, chunk: RetrievalResult, include_doc: bool = True) -> str:
        parts = []
        if include_doc and chunk.document:
            parts.append(chunk.document)
        if chunk.section:
            parts.append(chunk.section)
        if chunk.page is not None:
            parts.append(f"Page {chunk.page}")
            
        if parts:
            return f" ({', '.join(parts)})"
        return ""
        
    def _clean_text(self, text: str) -> str:
        # Simplify text presentation by collapsing whitespace
        return " ".join(text.split())

class AnswerGenerator(DeterministicAnswerGenerator):
    """
    Default adapter for Answer generation.
    Currently delegates entirely to DeterministicAnswerGenerator.
    """
    pass
