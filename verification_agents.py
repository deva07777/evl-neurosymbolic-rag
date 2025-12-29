"""E-V-L Verification Framework for Neuro-Symbolic RAG.

Three sequential verification agents:
- Agent E (Earnings): Verify numerical claims match sources
- Agent V (Validity): Verify factual claims are supported
- Agent L (Longevity): Verify trends are consistent with history
"""
from typing import Dict, List, Tuple, Any, Optional
import re
from dataclasses import dataclass
from utils import logger

@dataclass
class VerificationResult:
    agent: str  # "E", "V", or "L"
    status: str  # "PASS" or "FAIL"
    details: str  # Human-readable explanation
    corrections: Optional[str] = None  # Suggested fixes
    confidence_penalty: float = 0.0  # How much to reduce confidence (0.0-1.0)


class VerificationAgentE:
    """Agent E: Earnings Verification - Check numerical claims."""

    def __init__(self):
        self.name = "E"

    def extract_numbers(self, text: str) -> List[Tuple[float, str]]:
        """Extract all numerical claims from answer text."""
        # Pattern: number followed by metric name
        pattern = r'(\$?[0-9,]+(?:\.[0-9]+)?)\s*(?:B|M|billion|million|%)?(?:\s+(?:in\s+)?([a-zA-Z\s]+?))?(?=[,\.\;:\n]|$)'
        matches = re.findall(pattern, text)
        numbers = []
        for match in matches:
            try:
                num = float(match[0].replace('$', '').replace(',', ''))
                metric = match[1].strip() if len(match) > 1 else ""
                numbers.append((num, metric))
            except:
                pass
        return numbers

    def cross_check_numbers(self, extracted_numbers: List[Tuple[float, str]], source_chunks: List[Dict]) -> Tuple[List[str], List[str]]:
        """Cross-check extracted numbers against source chunks."""
        valid_claims = []
        hallucinations = []

        for num, metric in extracted_numbers:
            found = False
            for chunk in source_chunks:
                chunk_text = chunk.get('metadata', {}).get('text', '') or chunk.get('text', '')
                # Try to find the number in the chunk
                if str(int(num)) in chunk_text or f"{num:.2f}" in chunk_text or f"{num:.1f}" in chunk_text:
                    valid_claims.append(f"{num} ({metric})")
                    found = True
                    break

            if not found:
                hallucinations.append(f"{num} ({metric})")

        return valid_claims, hallucinations

    def verify(self, answer: str, source_chunks: List[Dict]) -> VerificationResult:
        """Run Agent E verification."""
        numbers = self.extract_numbers(answer)

        if not numbers:
            # No numerical claims = automatic pass
            return VerificationResult(
                agent="E",
                status="PASS",
                details="No numerical claims to verify.",
                confidence_penalty=0.0
            )

        valid, hallucinated = self.cross_check_numbers(numbers, source_chunks)

        if not hallucinated:
            return VerificationResult(
                agent="E",
                status="PASS",
                details=f"All {len(valid)} numerical claims verified against sources.",
                confidence_penalty=0.0
            )
        else:
            correction = f"Verified numbers: {', '.join(valid) if valid else 'None'}. " \
                        f"Unverified: {', '.join(hallucinated)}"
            return VerificationResult(
                agent="E",
                status="FAIL",
                details=f"Found {len(hallucinated)} unverified numerical claims: {', '.join(hallucinated)}",
                corrections=correction,
                confidence_penalty=0.3
            )


class VerificationAgentV:
    """Agent V: Validity Verification - Check factual support."""

    def __init__(self):
        self.name = "V"

    def extract_claims(self, text: str) -> List[str]:
        """Extract main factual claims from answer."""
        # Split by sentence and filter short ones
        sentences = re.split(r'[\.!\?]+', text)
        claims = [s.strip() for s in sentences if len(s.strip()) > 10]
        return claims

    def check_claim_support(self, claim: str, source_chunks: List[Dict]) -> Tuple[bool, float]:
        """Check if a claim is supported by sources using word overlap."""
        claim_words = set(claim.lower().split())
        claim_words = {w for w in claim_words if len(w) > 3}  # Filter short words

        max_overlap = 0.0
        for chunk in source_chunks:
            chunk_text = chunk.get('metadata', {}).get('text', '') or chunk.get('text', '')
            chunk_words = set(chunk_text.lower().split())
            overlap = len(claim_words & chunk_words) / (len(claim_words) + 1e-6)
            max_overlap = max(max_overlap, overlap)

        # Claim is supported if overlap > 0.4 (40% of words found)
        return max_overlap > 0.4, max_overlap

    def verify(self, answer: str, source_chunks: List[Dict]) -> VerificationResult:
        """Run Agent V verification."""
        claims = self.extract_claims(answer)

        if not claims:
            return VerificationResult(
                agent="V",
                status="PASS",
                details="No claims to verify.",
                confidence_penalty=0.0
            )

        supported = []
        unsupported = []

        for claim in claims:
            is_supported, overlap_score = self.check_claim_support(claim, source_chunks)
            if is_supported:
                supported.append(claim[:50])
            else:
                unsupported.append(claim[:50])

        if not unsupported:
            return VerificationResult(
                agent="V",
                status="PASS",
                details=f"All {len(supported)} claims verified in sources.",
                confidence_penalty=0.0
            )
        else:
            return VerificationResult(
                agent="V",
                status="FAIL",
                details=f"Found {len(unsupported)} unsupported claims.",
                corrections=f"Unsupported: {'; '.join(unsupported[:2])}...",
                confidence_penalty=0.25
            )


class VerificationAgentL:
    """Agent L: Longevity Verification - Check historical consistency."""

    def __init__(self):
        self.name = "L"

    def extract_trend_claims(self, text: str) -> List[Tuple[str, str]]:
        """Extract trend statements (e.g., 'revenue grew', 'margins declined')."""
        patterns = [
            r'(\w+)\s+(?:grew|increased|rose|climbed)',
            r'(\w+)\s+(?:declined|decreased|fell|dropped)',
            r'(\w+)\s+(?:was\s+)?stable|flat|consistent',
        ]
        claims = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                trend = "growth" if "grew" in pattern or "increased" in pattern else "decline" if "declined" in pattern else "stable"
                claims.append((match, trend))
        return claims

    def verify(self, answer: str, knowledge_graph: Optional[Any] = None, ticker: Optional[str] = None) -> VerificationResult:
        """Run Agent L verification.

        If knowledge_graph and ticker provided, check against historical trends.
        Otherwise, return PASS (can't verify without graph).
        """
        if not knowledge_graph or not ticker:
            return VerificationResult(
                agent="L",
                status="PASS",
                details="No historical data available for trend verification.",
                confidence_penalty=0.0
            )

        trend_claims = self.extract_trend_claims(answer)

        if not trend_claims:
            return VerificationResult(
                agent="L",
                status="PASS",
                details="No trend claims to verify.",
                confidence_penalty=0.0
            )

        # Check trends against historical data
        anomalies = []
        for metric_name, claimed_trend in trend_claims:
            years, values, actual_trend = knowledge_graph.get_trend(ticker, metric_name.lower())
            if years and actual_trend != "unknown":
                if actual_trend != claimed_trend:
                    anomalies.append(f"{metric_name}: claimed {claimed_trend} but historically {actual_trend}")

        if not anomalies:
            return VerificationResult(
                agent="L",
                status="PASS",
                details=f"All {len(trend_claims)} trend claims consistent with history.",
                confidence_penalty=0.0
            )
        else:
            return VerificationResult(
                agent="L",
                status="FAIL",
                details=f"Found {len(anomalies)} trend inconsistencies.",
                corrections=f"Anomalies: {'; '.join(anomalies[:2])}",
                confidence_penalty=0.15
            )


class EVLVerificationFramework:
    """Orchestrates all three verification agents."""

    def __init__(self):
        self.agent_e = VerificationAgentE()
        self.agent_v = VerificationAgentV()
        self.agent_l = VerificationAgentL()

    def verify_answer(
        self,
        answer: str,
        source_chunks: List[Dict],
        knowledge_graph: Optional[Any] = None,
        ticker: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run all three verification agents and combine results.

        Returns:
        {
            "all_pass": bool,
            "confidence_adjustment": float,  # penalty to apply to base confidence
            "agent_results": [VerificationResult, ...],
            "final_confidence_score": float,  # after applying penalties
            "verification_summary": str
        }
        """
        results: List[VerificationResult] = []

        # Run Agent E
        logger.info("Running Agent E (Earnings Verification)...")
        result_e = self.agent_e.verify(answer, source_chunks)
        results.append(result_e)

        # Run Agent V
        logger.info("Running Agent V (Validity Verification)...")
        result_v = self.agent_v.verify(answer, source_chunks)
        results.append(result_v)

        # Run Agent L
        logger.info("Running Agent L (Longevity Verification)...")
        result_l = self.agent_l.verify(answer, knowledge_graph, ticker)
        results.append(result_l)

        # Combine results
        all_pass = all(r.status == "PASS" for r in results)
        total_penalty = sum(r.confidence_penalty for r in results)
        base_confidence = 0.95 if all_pass else 0.60

        summary_lines = []
        for r in results:
            symbol = "[PASS]" if r.status == "PASS" else "[FAIL]"
            summary_lines.append(f"Agent {r.agent}: {symbol} {r.details}")
            if r.corrections:
                summary_lines.append(f"  -> Correction: {r.corrections}")

        return {
            "all_pass": all_pass,
            "confidence_adjustment": -total_penalty,
            "agent_results": results,
            "final_confidence_score": max(0.0, min(1.0, base_confidence - total_penalty)),
            "verification_summary": "\n".join(summary_lines)
        }
