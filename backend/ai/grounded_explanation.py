from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .evidence_guard import HallucinationGuard
from .schemas import EvidenceContract


# ============================================================
# DAY 11.11 — GROUNDED GEMINI EXPLANATION GUARD
# ============================================================


@dataclass
class GroundedExplanationResult:
    """
    Final result of validating an LLM explanation against
    deterministic investigation evidence.
    """

    explanation: str

    accepted: bool

    hallucination_valid: bool

    unsupported_claims: list[str] = field(
        default_factory=list
    )

    evidence_ids: list[str] = field(
        default_factory=list
    )

    fallback_used: bool = False

    reason: str = ""


class GroundedExplanationGuard:
    """
    Evidence-aware wrapper around the existing
    HallucinationGuard.

    The existing HallucinationGuard remains unchanged because
    it is already independently validated by Day 11.3.

    This wrapper additionally understands normal LLM response
    structure:

        Finding:
        Evidence:
        Interpretation:
        Next investigation:

    Structural headings are ignored.

    Concrete numeric and identifier claims remain strict.

    Qualitative interpretation/recommendation text may pass
    when it is explicitly connected to the supplied evidence.
    """

    # ========================================================
    # STRUCTURAL HEADINGS
    # ========================================================

    STRUCTURAL_HEADINGS = {
        "finding",
        "evidence",
        "interpretation",
        "next investigation",
        "next step",
        "recommendation",
        "recommendations",
        "analysis",
        "summary",
        "conclusion",
    }

    # ========================================================
    # SAFE QUALITATIVE PHRASES
    # ========================================================

    SAFE_QUALITATIVE_PHRASES = (
        "the evidence shows",
        "the evidence indicates",
        "the evidence suggests",
        "the results show",
        "the results indicate",
        "the investigation shows",
        "the investigation indicates",
        "the investigation suggests",
        "the analysis shows",
        "the analysis indicates",
        "based on the evidence",
        "based on the investigation",
        "based on the results",
        "this suggests",
        "this indicates",
        "this means",
        "review",
        "investigate",
        "analyze",
        "analyse",
        "examine",
        "compare",
        "break down",
        "look into",
        "assess",
        "evaluate",
    )

    # ========================================================
    # INVESTIGATIVE VERBS
    # ========================================================

    INVESTIGATIVE_VERBS = (
        "review",
        "investigate",
        "analyze",
        "analyse",
        "examine",
        "compare",
        "break down",
        "look into",
        "assess",
        "evaluate",
    )

    def __init__(
        self,
        hallucination_guard: HallucinationGuard | None = None,
    ) -> None:

        self.hallucination_guard = (
            hallucination_guard
            or HallucinationGuard()
        )

    # ========================================================
    # MAIN VALIDATION
    # ========================================================

    def validate(
        self,
        explanation: str,
        evidence_contract: EvidenceContract,
    ) -> GroundedExplanationResult:
        """
        Validate a complete explanation.
        """

        explanation = (
            explanation or ""
        ).strip()

        available_evidence = [
            item
            for item
            in evidence_contract.evidence
            if item.available
        ]

        # ----------------------------------------------------
        # EMPTY
        # ----------------------------------------------------

        if not explanation:

            return GroundedExplanationResult(
                explanation="",
                accepted=False,
                hallucination_valid=False,
                unsupported_claims=[
                    "EMPTY_EXPLANATION"
                ],
                evidence_ids=[],
                fallback_used=True,
                reason=(
                    "LLM returned an empty explanation."
                ),
            )

        # ----------------------------------------------------
        # NO EVIDENCE
        # ----------------------------------------------------

        if not available_evidence:

            return GroundedExplanationResult(
                explanation=explanation,
                accepted=False,
                hallucination_valid=False,
                unsupported_claims=[
                    "NO_AVAILABLE_EVIDENCE"
                ],
                evidence_ids=[],
                fallback_used=True,
                reason=(
                    "No available evidence exists "
                    "to ground the explanation."
                ),
            )

        # ----------------------------------------------------
        # Extract meaningful claims.
        # ----------------------------------------------------

        claims = self._extract_meaningful_claims(
            explanation
        )

        if not claims:

            return GroundedExplanationResult(
                explanation=explanation,
                accepted=False,
                hallucination_valid=False,
                unsupported_claims=[
                    "NO_VALID_CLAIMS"
                ],
                evidence_ids=[
                    item.evidence_id
                    for item
                    in available_evidence
                ],
                fallback_used=True,
                reason=(
                    "Explanation does not contain any "
                    "meaningful claims."
                ),
            )

        unsupported_claims: list[str] = []

        evidence_ids_used: set[str] = set()

        # ----------------------------------------------------
        # Validate claims.
        # ----------------------------------------------------

        for claim in claims:

            # ------------------------------------------------
            # First use the strict existing guard.
            # ------------------------------------------------

            claim_result = (
                self.hallucination_guard.validate_claim(
                    claim,
                    available_evidence,
                )
            )

            if claim_result.supported:

                evidence_ids_used.update(
                    claim_result.matched_evidence_ids
                )

                continue

            # ------------------------------------------------
            # Conservative explanation-aware qualitative
            # fallback.
            # ------------------------------------------------

            if self._safe_qualitative_claim(
                claim,
                available_evidence,
            ):

                linked_ids = (
                    self._find_evidence_for_qualitative_claim(
                        claim,
                        available_evidence,
                    )
                )

                # A qualitative claim must still have a link
                # to evidence unless it is an explicit
                # investigative recommendation.
                if (
                    linked_ids
                    or
                    self._is_investigative_recommendation(
                        claim
                    )
                ):

                    evidence_ids_used.update(
                        linked_ids
                    )

                    continue

            # ------------------------------------------------
            # Reject unsupported claim.
            # ------------------------------------------------

            unsupported_claims.append(
                claim
            )

            evidence_ids_used.update(
                claim_result.matched_evidence_ids
            )

        # ----------------------------------------------------
        # Deduplicate
        # ----------------------------------------------------

        unsupported_claims = list(
            dict.fromkeys(
                unsupported_claims
            )
        )

        # ----------------------------------------------------
        # ACCEPT
        # ----------------------------------------------------

        if not unsupported_claims:

            if not evidence_ids_used:

                evidence_ids_used.update(
                    item.evidence_id
                    for item
                    in available_evidence
                )

            return GroundedExplanationResult(
                explanation=explanation,
                accepted=True,
                hallucination_valid=True,
                unsupported_claims=[],
                evidence_ids=sorted(
                    evidence_ids_used
                ),
                fallback_used=False,
                reason=(
                    "Explanation passed the "
                    "evidence-aware hallucination guard."
                ),
            )

        # ----------------------------------------------------
        # REJECT
        # ----------------------------------------------------

        return GroundedExplanationResult(
            explanation=explanation,
            accepted=False,
            hallucination_valid=False,
            unsupported_claims=unsupported_claims,
            evidence_ids=sorted(
                evidence_ids_used
            ),
            fallback_used=True,
            reason=(
                f"{len(unsupported_claims)} explanation "
                "claim(s) could not be grounded in "
                "available evidence."
            ),
        )

    # ========================================================
    # CLAIM EXTRACTION
    # ========================================================

    def _extract_meaningful_claims(
        self,
        explanation: str,
    ) -> list[str]:
        """
        Convert an LLM response into factual/interpretive
        claims.

        Structural headings are removed.

        Consecutive lines are intelligently merged when the
        second line is a continuation of the first sentence.
        """

        raw_lines = [
            line.strip()
            for line
            in explanation.splitlines()
            if line.strip()
        ]

        filtered_lines: list[str] = []

        for line in raw_lines:

            cleaned = (
                line
                .strip()
                .strip("-•*")
                .strip()
            )

            if not cleaned:

                continue

            if self._is_structural_heading(
                cleaned
            ):

                continue

            filtered_lines.append(
                cleaned
            )

        # ----------------------------------------------------
        # Join multiline continuation text first.
        #
        # Example:
        #
        # Review the flagged journeys and associated journey
        # characteristics to identify relevant patterns.
        #
        # becomes ONE claim.
        # ----------------------------------------------------

        joined_lines: list[str] = []

        for line in filtered_lines:

            if not joined_lines:

                joined_lines.append(
                    line
                )

                continue

            previous = (
                joined_lines[-1]
            )

            # ------------------------------------------------
            # Previous line does not end a sentence:
            # treat current line as continuation.
            # ------------------------------------------------

            if not self._ends_sentence(
                previous
            ):

                joined_lines[-1] = (
                    previous
                    + " "
                    + line
                )

            else:

                joined_lines.append(
                    line
                )

        # ----------------------------------------------------
        # Now split only real sentence boundaries.
        # ----------------------------------------------------

        claims: list[str] = []

        for line in joined_lines:

            parts = re.split(
                r"(?<=[.!?])\s+",
                line,
            )

            for part in parts:

                cleaned = (
                    part
                    .strip()
                    .strip("-•*")
                    .strip()
                )

                if not cleaned:

                    continue

                if self._is_structural_heading(
                    cleaned
                ):

                    continue

                claims.append(
                    cleaned
                )

        return claims

    # ========================================================
    # SENTENCE END
    # ========================================================

    @staticmethod
    def _ends_sentence(
        text: str,
    ) -> bool:

        return text.rstrip().endswith(
            (
                ".",
                "!",
                "?",
                ":",
            )
        )

    # ========================================================
    # STRUCTURAL HEADING
    # ========================================================

    def _is_structural_heading(
        self,
        text: str,
    ) -> bool:

        normalized = (
            text
            .strip()
            .rstrip(":")
            .strip()
            .lower()
        )

        return (
            normalized
            in self.STRUCTURAL_HEADINGS
        )

    # ========================================================
    # SAFE QUALITATIVE CLAIM
    # ========================================================

    def _safe_qualitative_claim(
        self,
        claim: str,
        evidence: list[Any],
    ) -> bool:
        """
        Handle qualitative claims that are not directly
        matched by the strict guard.

        Numeric and identifier safety remains strict.
        """

        # ----------------------------------------------------
        # Numeric values must still be supported.
        # ----------------------------------------------------

        claim_numbers = (
            self.hallucination_guard._extract_numbers(
                claim
            )
        )

        if claim_numbers:

            evidence_numbers = (
                self.hallucination_guard
                ._build_evidence_numbers(
                    evidence
                )
            )

            for (
                _token,
                number,
                is_percentage,
            ) in claim_numbers:

                matches = (
                    self.hallucination_guard
                    ._find_numeric_matches(
                        number=number,
                        is_percentage=is_percentage,
                        evidence_numbers=evidence_numbers,
                    )
                )

                if not matches:

                    return False

        # ----------------------------------------------------
        # Identifiers must still be supported.
        # ----------------------------------------------------

        claim_identifiers = (
            self.hallucination_guard
            ._extract_identifiers(
                claim
            )
        )

        if claim_identifiers:

            identifier_index = (
                self.hallucination_guard
                ._build_identifier_index(
                    evidence
                )
            )

            available_identifiers = set()

            for values in (
                identifier_index.values()
            ):

                available_identifiers.update(
                    values
                )

            for identifier in claim_identifiers:

                if (
                    identifier.lower()
                    not in available_identifiers
                ):

                    return False

        # ----------------------------------------------------
        # Normalize
        # ----------------------------------------------------

        normalized_claim = (
            self._normalize_text(
                claim
            )
        )

        # ----------------------------------------------------
        # Explicit interpretation/recommendation language.
        # ----------------------------------------------------

        has_safe_phrase = any(
            phrase
            in normalized_claim
            for phrase
            in self.SAFE_QUALITATIVE_PHRASES
        )

        if not has_safe_phrase:

            return False

        # ----------------------------------------------------
        # Evidence overlap.
        # ----------------------------------------------------

        evidence_text = (
            self._build_evidence_text(
                evidence
            )
        )

        claim_tokens = (
            self._important_tokens(
                normalized_claim
            )
        )

        evidence_tokens = (
            self._important_tokens(
                evidence_text
            )
        )

        overlap = (
            claim_tokens
            &
            evidence_tokens
        )

        if overlap:

            return True

        # ----------------------------------------------------
        # Explicit investigation recommendation can be
        # accepted even without exact word overlap because it
        # tells the analyst to inspect available evidence,
        # rather than asserting a new fact.
        # ----------------------------------------------------

        return self._is_investigative_recommendation(
            claim
        )

    # ========================================================
    # INVESTIGATIVE RECOMMENDATION
    # ========================================================

    def _is_investigative_recommendation(
        self,
        claim: str,
    ) -> bool:

        normalized = (
            self._normalize_text(
                claim
            )
        )

        return any(
            phrase
            in normalized
            for phrase
            in self.INVESTIGATIVE_VERBS
        )

    # ========================================================
    # QUALITATIVE EVIDENCE LINKING
    # ========================================================

    def _find_evidence_for_qualitative_claim(
        self,
        claim: str,
        evidence: list[Any],
    ) -> list[str]:

        normalized_claim = (
            self._normalize_text(
                claim
            )
        )

        claim_tokens = (
            self._important_tokens(
                normalized_claim
            )
        )

        matched_ids: list[str] = []

        for item in evidence:

            candidate_parts: list[str] = []

            if item.metric:

                candidate_parts.append(
                    str(item.metric)
                )

            if item.value is not None:

                candidate_parts.append(
                    str(item.value)
                )

            if item.detail:

                candidate_parts.append(
                    str(item.detail)
                )

            if item.source_reference:

                candidate_parts.append(
                    str(item.source_reference)
                )

            candidate_text = (
                self._normalize_text(
                    " ".join(
                        candidate_parts
                    )
                )
            )

            candidate_tokens = (
                self._important_tokens(
                    candidate_text
                )
            )

            if (
                claim_tokens
                &
                candidate_tokens
            ):

                matched_ids.append(
                    item.evidence_id
                )

        return matched_ids

    # ========================================================
    # EVIDENCE TEXT
    # ========================================================

    @staticmethod
    def _build_evidence_text(
        evidence: list[Any],
    ) -> str:

        parts: list[str] = []

        for item in evidence:

            if item.metric:

                parts.append(
                    str(item.metric)
                )

            if item.value is not None:

                parts.append(
                    str(item.value)
                )

            if item.detail:

                parts.append(
                    str(item.detail)
                )

            if item.source_reference:

                parts.append(
                    str(item.source_reference)
                )

        return " ".join(
            parts
        )

    # ========================================================
    # NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:

        return re.sub(
            r"\s+",
            " ",
            value.strip().lower(),
        )

    # ========================================================
    # TOKENIZATION
    # ========================================================

    @staticmethod
    def _important_tokens(
        text: str,
    ) -> set[str]:

        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "of",
            "to",
            "for",
            "in",
            "on",
            "is",
            "are",
            "was",
            "were",
            "with",
            "that",
            "this",
            "it",
            "as",
            "by",
            "from",
            "be",
            "been",
            "being",
            "only",
            "based",
            "before",
            "after",
            "into",
            "their",
            "there",
            "those",
            "these",
            "can",
            "could",
            "would",
            "should",
            "may",
            "might",
            "will",
            "has",
            "have",
            "had",
            "its",
            "than",
            "then",
            "where",
            "which",
            "what",
            "who",
            "how",
        }

        tokens = {
            token
            for token
            in re.findall(
                r"[a-zA-Z_][a-zA-Z0-9_]*",
                text,
            )
            if (
                len(token) >= 3
                and token not in stop_words
            )
        }

        return tokens


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================


def validate_grounded_explanation(
    explanation: str,
    evidence_contract: EvidenceContract,
) -> GroundedExplanationResult:

    guard = (
        GroundedExplanationGuard()
    )

    return guard.validate(
        explanation=explanation,
        evidence_contract=evidence_contract,
    )