from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .grounded_findings import (
    GroundedFindingValidator,
)
from .grounded_recommendations import (
    GroundedRecommendationValidator,
)
from .schemas import (
    EvidenceContract,
    EvidenceItem,
    InvestigationFinding,
    StructuredInvestigationContext,
)


# ============================================================
# DAY 11.8 — EVIDENCE-GROUNDED AI RESPONSE
# ============================================================


@dataclass
class GroundedResponseClaim:
    """
    One claim included in the final AI response.
    """

    text: str

    evidence_ids: list[str] = field(
        default_factory=list
    )

    grounded: bool = False


@dataclass
class GroundedResponseResult:
    """
    Complete evidence-grounded response.
    """

    response: str

    grounded: bool

    question: str

    intent: str

    evidence_ids: list[str] = field(
        default_factory=list
    )

    finding_titles: list[str] = field(
        default_factory=list
    )

    recommendation: str | None = None

    claims: list[GroundedResponseClaim] = field(
        default_factory=list
    )

    unsupported_claims: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    reason: str = ""


# ============================================================
# RESPONSE BUILDER
# ============================================================


class EvidenceGroundedResponseBuilder:
    """
    Builds a deterministic final response from already validated
    investigation context.

    This class does not invent facts.

    Every factual statement is derived from:
        - the investigation question,
        - the finding,
        - the linked evidence,
        - the recommendation generated from that finding.
    """

    def __init__(self) -> None:

        self.finding_validator = (
            GroundedFindingValidator()
        )

        self.recommendation_validator = (
            GroundedRecommendationValidator()
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def build(
        self,
        context: StructuredInvestigationContext,
        evidence_contract: EvidenceContract,
        findings: Iterable[InvestigationFinding] | None = None,
        recommendations: Iterable[
            tuple[
                InvestigationFinding,
                str,
            ]
        ] | None = None,
    ) -> GroundedResponseResult:
        """
        Build a complete grounded response.

        findings:
            Optional explicit finding list.

        recommendations:
            Optional pairs of:
                (finding, recommendation)
        """

        finding_list = list(
            findings
            if findings is not None
            else context.findings
        )

        recommendation_pairs = list(
            recommendations
            if recommendations is not None
            else []
        )

        # ----------------------------------------------------
        # Validate findings
        # ----------------------------------------------------

        grounded_findings = (
            self.finding_validator.validate_all(
                finding_list,
                evidence_contract,
            )
        )

        grounded_finding_objects: list[
            InvestigationFinding
        ] = []

        for finding, validation in zip(
            finding_list,
            grounded_findings.results,
        ):

            if validation.grounded:
                grounded_finding_objects.append(
                    finding
                )

        # ----------------------------------------------------
        # Validate recommendations
        # ----------------------------------------------------

        grounded_recommendation_objects = []

        if recommendation_pairs:

            recommendation_summary = (
                self.recommendation_validator.validate_all(
                    recommendation_pairs,
                    evidence_contract,
                )
            )

            grounded_recommendation_objects = [
                (
                    finding,
                    result,
                )
                for (
                    finding,
                    result,
                ) in zip(
                    [
                        pair[0]
                        for pair in recommendation_pairs
                    ],
                    recommendation_summary.results,
                )
                if result.grounded
            ]

        # ----------------------------------------------------
        # Collect evidence IDs
        # ----------------------------------------------------

        response_evidence_ids: list[str] = []

        for finding in grounded_finding_objects:

            for evidence_id in finding.evidence_ids:

                if evidence_id not in response_evidence_ids:

                    response_evidence_ids.append(
                        evidence_id
                    )

        # ----------------------------------------------------
        # Build claims
        # ----------------------------------------------------

        claims: list[GroundedResponseClaim] = []

        # Question/context claim

        question_claim = (
            f"Investigation question: "
            f"{context.question}"
        )

        claims.append(
            GroundedResponseClaim(
                text=question_claim,
                evidence_ids=[],
                grounded=True,
            )
        )

        # Finding claims

        for finding in grounded_finding_objects:

            finding_text = (
                self._format_finding(
                    finding
                )
            )

            claims.append(
                GroundedResponseClaim(
                    text=finding_text,
                    evidence_ids=list(
                        finding.evidence_ids
                    ),
                    grounded=True,
                )
            )

        # Recommendation claims

        recommendation_texts: list[str] = []

        for (
            finding,
            result,
        ) in grounded_recommendation_objects:

            recommendation_text = (
                result.recommendation.strip()
            )

            recommendation_texts.append(
                recommendation_text
            )

            claims.append(
                GroundedResponseClaim(
                    text=recommendation_text,
                    evidence_ids=list(
                        result.matched_evidence_ids
                    ),
                    grounded=True,
                )
            )

        # ----------------------------------------------------
        # Build warnings
        # ----------------------------------------------------

        warnings: list[str] = []

        if not grounded_finding_objects:

            warnings.append(
                "No grounded findings are available."
            )

        if finding_list and (
            len(grounded_finding_objects)
            < len(finding_list)
        ):

            warnings.append(
                "Some findings were excluded because "
                "they could not be fully grounded."
            )

        if (
            recommendation_pairs
            and not grounded_recommendation_objects
        ):

            warnings.append(
                "No grounded recommendation is available."
            )

        # ----------------------------------------------------
        # Build response text
        # ----------------------------------------------------

        response = (
            self._compose_response(
                context=context,
                grounded_findings=(
                    grounded_finding_objects
                ),
                grounded_recommendations=(
                    grounded_recommendation_objects
                ),
                warnings=warnings,
            )
        )

        # ----------------------------------------------------
        # Final response grounding check
        # ----------------------------------------------------

        unsupported_claims = (
            self._find_unsupported_claims(
                claims=claims,
                evidence_contract=evidence_contract,
            )
        )

        grounded = (
            len(unsupported_claims) == 0
            and
            all(
                claim.grounded
                for claim in claims
            )
        )

        # ----------------------------------------------------
        # Reason
        # ----------------------------------------------------

        if grounded:

            reason = (
                "Final response is composed only from "
                "grounded investigation findings and "
                "grounded recommendations."
            )

        else:

            reason = (
                "Final response contains one or more "
                "claims that could not be fully grounded."
            )

        return GroundedResponseResult(
            response=response,
            grounded=grounded,
            question=context.question,
            intent=context.intent,
            evidence_ids=response_evidence_ids,
            finding_titles=[
                finding.title
                for finding
                in grounded_finding_objects
            ],
            recommendation=(
                recommendation_texts[0]
                if recommendation_texts
                else None
            ),
            claims=claims,
            unsupported_claims=unsupported_claims,
            warnings=warnings,
            reason=reason,
        )

    # ========================================================
    # FINDING FORMATTER
    # ========================================================

    @staticmethod
    def _format_finding(
        finding: InvestigationFinding,
    ) -> str:
        """
        Convert a deterministic finding into a factual
        response statement.
        """

        pieces: list[str] = []

        if finding.title:
            pieces.append(
                finding.title
            )

        if finding.metric:

            pieces.append(
                f"{finding.metric}"
            )

        if finding.value is not None:

            pieces.append(
                f"value={finding.value}"
            )

        if finding.threshold is not None:

            if finding.operator:

                pieces.append(
                    (
                        f"threshold "
                        f"{finding.operator} "
                        f"{finding.threshold}"
                    )
                )

            else:

                pieces.append(
                    (
                        f"threshold="
                        f"{finding.threshold}"
                    )
                )

        if finding.detail:

            pieces.append(
                finding.detail.strip()
            )

        return " — ".join(
            piece
            for piece in pieces
            if piece
        )

    # ========================================================
    # RESPONSE COMPOSER
    # ========================================================

    def _compose_response(
        self,
        context: StructuredInvestigationContext,
        grounded_findings: list[
            InvestigationFinding
        ],
        grounded_recommendations: list[
            tuple[
                InvestigationFinding,
                Any,
            ]
        ],
        warnings: list[str],
    ) -> str:
        """
        Compose deterministic response text.
        """

        sections: list[str] = []

        sections.append(
            (
                f"Investigation: "
                f"{context.question}"
            )
        )

        # Findings section

        if grounded_findings:

            sections.append(
                "Findings:"
            )

            for finding in grounded_findings:

                sections.append(
                    (
                        "- "
                        + self._format_finding(
                            finding
                        )
                    )
                )

        else:

            sections.append(
                "Findings: No grounded findings available."
            )

        # Recommendations section

        if grounded_recommendations:

            sections.append(
                "Recommendations:"
            )

            for (
                _finding,
                recommendation,
            ) in grounded_recommendations:

                sections.append(
                    (
                        "- "
                        + recommendation.recommendation
                    )
                )

        # Warnings

        if warnings:

            sections.append(
                "Evidence notes:"
            )

            for warning in warnings:

                sections.append(
                    "- "
                    + warning
                )

        return "\n".join(
            sections
        )

    # ========================================================
    # CLAIM VALIDATION
    # ========================================================

    def _find_unsupported_claims(
        self,
        claims: list[
            GroundedResponseClaim
        ],
        evidence_contract: EvidenceContract,
    ) -> list[str]:
        """
        Ensure every factual claim that declares evidence
        references can resolve those evidence IDs.
        """

        evidence_index = {
            item.evidence_id: item
            for item in evidence_contract.evidence
        }

        unsupported: list[str] = []

        for claim in claims:

            if not claim.grounded:

                unsupported.append(
                    claim.text
                )

                continue

            for evidence_id in claim.evidence_ids:

                item = evidence_index.get(
                    evidence_id
                )

                if item is None:

                    unsupported.append(
                        claim.text
                    )

                    break

                if not item.available:

                    unsupported.append(
                        claim.text
                    )

                    break

        return list(
            dict.fromkeys(
                unsupported
            )
        )


# ============================================================
# SERIALIZATION
# ============================================================


def grounded_response_to_dict(
    result: GroundedResponseResult,
) -> dict[str, Any]:
    """
    Convert response result to JSON-safe dict.
    """

    return {
        "response": result.response,
        "grounded": result.grounded,
        "question": result.question,
        "intent": result.intent,
        "evidence_ids": result.evidence_ids,
        "finding_titles": result.finding_titles,
        "recommendation": result.recommendation,
        "claims": [
            {
                "text": claim.text,
                "evidence_ids": claim.evidence_ids,
                "grounded": claim.grounded,
            }
            for claim in result.claims
        ],
        "unsupported_claims": (
            result.unsupported_claims
        ),
        "warnings": result.warnings,
        "reason": result.reason,
    }


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================


def build_grounded_response(
    context: StructuredInvestigationContext,
    evidence_contract: EvidenceContract,
    findings: Iterable[InvestigationFinding] | None = None,
    recommendations: Iterable[
        tuple[
            InvestigationFinding,
            str,
        ]
    ] | None = None,
) -> GroundedResponseResult:
    """
    Convenience wrapper.
    """

    builder = (
        EvidenceGroundedResponseBuilder()
    )

    return builder.build(
        context=context,
        evidence_contract=evidence_contract,
        findings=findings,
        recommendations=recommendations,
    )