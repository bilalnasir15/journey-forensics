from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .schemas import (
    EvidenceContract,
    EvidenceItem,
    EvidenceSupportLevel,
    InvestigationFinding,
)


# ============================================================
# CONFIDENCE LEVEL
# ============================================================


@dataclass(frozen=True)
class ConfidenceLevel:
    """
    Human-readable confidence classification.
    """

    label: str

    score: float

    rationale: str


# ============================================================
# UNCERTAINTY ITEM
# ============================================================


@dataclass
class UncertaintyItem:
    """
    One known uncertainty or limitation.
    """

    category: str

    description: str

    severity: str = "MEDIUM"

    evidence_ids: list[str] = field(
        default_factory=list
    )


# ============================================================
# CONFIDENCE ASSESSMENT
# ============================================================


@dataclass
class ConfidenceAssessment:
    """
    Overall deterministic confidence assessment.
    """

    level: str

    score: float

    rationale: str

    evidence_count: int

    available_evidence_count: int

    direct_evidence_count: int

    derived_evidence_count: int

    contextual_evidence_count: int

    unavailable_evidence_count: int

    average_evidence_confidence: float

    grounded_finding_count: int

    total_finding_count: int


# ============================================================
# UNCERTAINTY ASSESSMENT
# ============================================================


@dataclass
class UncertaintyAssessment:
    """
    Deterministic uncertainty assessment.
    """

    has_uncertainty: bool

    items: list[UncertaintyItem] = field(
        default_factory=list
    )

    summary: str = ""


# ============================================================
# COMPLETE ASSESSMENT
# ============================================================


@dataclass
class ConfidenceUncertaintyResult:
    """
    Combined confidence and uncertainty result.
    """

    confidence: ConfidenceAssessment

    uncertainty: UncertaintyAssessment


# ============================================================
# CONFIDENCE + UNCERTAINTY ANALYZER
# ============================================================


class ConfidenceUncertaintyAnalyzer:
    """
    Deterministic Day 11.6 analyzer.

    Confidence is based on:
        - amount of available evidence
        - evidence support level
        - evidence confidence values
        - grounded finding coverage

    Uncertainty is based on:
        - unavailable evidence
        - weak evidence
        - missing finding evidence
        - derived/contextual evidence
    """

    HIGH_THRESHOLD = 0.80

    MEDIUM_THRESHOLD = 0.60

    # ========================================================
    # MAIN API
    # ========================================================

    def analyze(
        self,
        evidence_contract: EvidenceContract,
        findings: Iterable[
            InvestigationFinding
        ] | None = None,
    ) -> ConfidenceUncertaintyResult:

        evidence = list(
            evidence_contract.evidence
        )

        finding_list = list(
            findings
            or []
        )

        confidence = self._calculate_confidence(
            evidence,
            finding_list,
        )

        uncertainty = self._calculate_uncertainty(
            evidence,
            finding_list,
        )

        return ConfidenceUncertaintyResult(
            confidence=confidence,
            uncertainty=uncertainty,
        )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    def _calculate_confidence(
        self,
        evidence: list[EvidenceItem],
        findings: list[InvestigationFinding],
    ) -> ConfidenceAssessment:

        total_evidence = len(
            evidence
        )

        available_evidence = [
            item
            for item in evidence
            if item.available
        ]

        unavailable_evidence = [
            item
            for item in evidence
            if not item.available
        ]

        direct_count = sum(
            1
            for item in available_evidence
            if item.support_level
            == EvidenceSupportLevel.DIRECT
        )

        derived_count = sum(
            1
            for item in available_evidence
            if item.support_level
            == EvidenceSupportLevel.DERIVED
        )

        contextual_count = sum(
            1
            for item in available_evidence
            if item.support_level
            == EvidenceSupportLevel.CONTEXTUAL
        )

        # ----------------------------------------------------
        # Evidence confidence
        # ----------------------------------------------------

        if available_evidence:

            average_confidence = (
                sum(
                    max(
                        0.0,
                        min(
                            float(
                                item.confidence
                            ),
                            1.0,
                        ),
                    )
                    for item
                    in available_evidence
                )
                /
                len(
                    available_evidence
                )
            )

        else:

            average_confidence = 0.0

        # ----------------------------------------------------
        # Evidence coverage
        # ----------------------------------------------------

        if total_evidence:

            availability_ratio = (
                len(
                    available_evidence
                )
                /
                total_evidence
            )

        else:

            availability_ratio = 0.0

        # ----------------------------------------------------
        # Direct evidence ratio
        # ----------------------------------------------------

        if available_evidence:

            direct_ratio = (
                direct_count
                /
                len(
                    available_evidence
                )
            )

        else:

            direct_ratio = 0.0

        # ----------------------------------------------------
        # Derived/contextual penalty
        # ----------------------------------------------------

        if available_evidence:

            weak_ratio = (
                derived_count
                +
                contextual_count
            ) / len(
                available_evidence
            )

        else:

            weak_ratio = 1.0

        support_quality = (
            max(
                0.0,
                min(
                    1.0,
                    (
                        0.70
                        * direct_ratio
                        +
                        0.30
                        * (
                            1.0
                            - weak_ratio
                        )
                    ),
                ),
            )
        )

        # ----------------------------------------------------
        # Finding grounding coverage
        # ----------------------------------------------------

        if findings:

            grounded_count = sum(
                1
                for finding
                in findings
                if self._finding_is_grounded(
                    finding,
                    evidence,
                )
            )

            finding_grounding_ratio = (
                grounded_count
                /
                len(findings)
            )

        else:

            grounded_count = 0

            # No findings means confidence is based on
            # evidence only rather than pretending that
            # finding grounding exists.
            finding_grounding_ratio = 0.75

        # ----------------------------------------------------
        # Overall score
        # ----------------------------------------------------

        score = (
            0.40
            * average_confidence
            +
            0.25
            * availability_ratio
            +
            0.20
            * support_quality
            +
            0.15
            * finding_grounding_ratio
        )

        # No evidence must produce LOW confidence.
        if not available_evidence:

            score = 0.0

        score = max(
            0.0,
            min(
                score,
                1.0,
            ),
        )

        score = round(
            score,
            3,
        )

        level = (
            self._confidence_label(
                score
            )
        )

        rationale = (
            self._confidence_rationale(
                level=level,
                score=score,
                average_evidence_confidence=(
                    average_confidence
                ),
                availability_ratio=(
                    availability_ratio
                ),
                direct_ratio=direct_ratio,
                grounded_count=grounded_count,
                finding_count=len(findings),
                unavailable_count=len(
                    unavailable_evidence
                ),
            )
        )

        return ConfidenceAssessment(
            level=level,
            score=score,
            rationale=rationale,
            evidence_count=total_evidence,
            available_evidence_count=len(
                available_evidence
            ),
            direct_evidence_count=direct_count,
            derived_evidence_count=derived_count,
            contextual_evidence_count=(
                contextual_count
            ),
            unavailable_evidence_count=len(
                unavailable_evidence
            ),
            average_evidence_confidence=round(
                average_confidence,
                3,
            ),
            grounded_finding_count=grounded_count,
            total_finding_count=len(
                findings
            ),
        )

    # ========================================================
    # CONFIDENCE LABEL
    # ========================================================

    @classmethod
    def _confidence_label(
        cls,
        score: float,
    ) -> str:

        if score >= cls.HIGH_THRESHOLD:

            return "HIGH"

        if score >= cls.MEDIUM_THRESHOLD:

            return "MEDIUM"

        return "LOW"

    # ========================================================
    # CONFIDENCE RATIONALE
    # ========================================================

    @staticmethod
    def _confidence_rationale(
        *,
        level: str,
        score: float,
        average_evidence_confidence: float,
        availability_ratio: float,
        direct_ratio: float,
        grounded_count: int,
        finding_count: int,
        unavailable_count: int,
    ) -> str:

        reasons: list[str] = []

        if direct_ratio >= 0.75:

            reasons.append(
                "most available evidence is direct"
            )

        elif direct_ratio > 0:

            reasons.append(
                "some evidence is directly observed"
            )

        else:

            reasons.append(
                "little or no direct evidence is available"
            )

        if average_evidence_confidence >= 0.80:

            reasons.append(
                "evidence confidence is high"
            )

        elif average_evidence_confidence >= 0.60:

            reasons.append(
                "evidence confidence is moderate"
            )

        else:

            reasons.append(
                "evidence confidence is low"
            )

        if finding_count:

            if (
                grounded_count
                == finding_count
            ):

                reasons.append(
                    "all findings are evidence-grounded"
                )

            elif grounded_count > 0:

                reasons.append(
                    "only some findings are evidence-grounded"
                )

            else:

                reasons.append(
                    "findings lack grounded evidence"
                )

        if unavailable_count:

            reasons.append(
                f"{unavailable_count} evidence item(s) "
                "are unavailable"
            )

        availability_text = (
            f"{availability_ratio:.0%}"
        )

        return (
            f"{level} confidence "
            f"({score:.1%}). "
            f"Evidence availability is "
            f"{availability_text}; "
            + "; ".join(
                reasons
            )
            + "."
        )

    # ========================================================
    # UNCERTAINTY
    # ========================================================

    def _calculate_uncertainty(
        self,
        evidence: list[EvidenceItem],
        findings: list[InvestigationFinding],
    ) -> UncertaintyAssessment:

        items: list[
            UncertaintyItem
        ] = []

        evidence_index = {
            item.evidence_id: item
            for item in evidence
        }

        # ----------------------------------------------------
        # Unavailable evidence
        # ----------------------------------------------------

        for item in evidence:

            if not item.available:

                items.append(
                    UncertaintyItem(
                        category="UNAVAILABLE_EVIDENCE",
                        description=(
                            f"Evidence '{item.evidence_id}' "
                            f"from '{item.source}' is unavailable."
                        ),
                        severity="HIGH",
                        evidence_ids=[
                            item.evidence_id
                        ],
                    )
                )

        # ----------------------------------------------------
        # Derived evidence
        # ----------------------------------------------------

        for item in evidence:

            if (
                item.available
                and
                item.support_level
                == EvidenceSupportLevel.DERIVED
            ):

                items.append(
                    UncertaintyItem(
                        category="DERIVED_EVIDENCE",
                        description=(
                            f"Evidence '{item.evidence_id}' "
                            "is derived rather than directly observed."
                        ),
                        severity="MEDIUM",
                        evidence_ids=[
                            item.evidence_id
                        ],
                    )
                )

        # ----------------------------------------------------
        # Contextual evidence
        # ----------------------------------------------------

        for item in evidence:

            if (
                item.available
                and
                item.support_level
                == EvidenceSupportLevel.CONTEXTUAL
            ):

                items.append(
                    UncertaintyItem(
                        category="CONTEXTUAL_EVIDENCE",
                        description=(
                            f"Evidence '{item.evidence_id}' "
                            "provides context but does not directly "
                            "establish the investigated fact."
                        ),
                        severity="LOW",
                        evidence_ids=[
                            item.evidence_id
                        ],
                    )
                )

        # ----------------------------------------------------
        # Low-confidence evidence
        # ----------------------------------------------------

        for item in evidence:

            if (
                item.available
                and float(
                    item.confidence
                ) < 0.60
            ):

                items.append(
                    UncertaintyItem(
                        category="LOW_CONFIDENCE_EVIDENCE",
                        description=(
                            f"Evidence '{item.evidence_id}' "
                            f"has confidence "
                            f"{float(item.confidence):.0%}."
                        ),
                        severity="MEDIUM",
                        evidence_ids=[
                            item.evidence_id
                        ],
                    )
                )

        # ----------------------------------------------------
        # Ungrounded findings
        # ----------------------------------------------------

        for finding in findings:

            if not self._finding_is_grounded(
                finding,
                evidence,
            ):

                items.append(
                    UncertaintyItem(
                        category="UNGROUNDED_FINDING",
                        description=(
                            f"Finding '{finding.title}' "
                            "does not have complete evidence grounding."
                        ),
                        severity="HIGH",
                        evidence_ids=list(
                            finding.evidence_ids
                        ),
                    )
                )

        # ----------------------------------------------------
        # De-duplicate
        # ----------------------------------------------------

        unique_items: list[
            UncertaintyItem
        ] = []

        seen: set[
            tuple[str, str]
        ] = set()

        for item in items:

            key = (
                item.category,
                item.description,
            )

            if key in seen:

                continue

            seen.add(
                key
            )

            unique_items.append(
                item
            )

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        if not unique_items:

            summary = (
                "No material uncertainty was identified "
                "in the available evidence."
            )

        else:

            high_count = sum(
                1
                for item
                in unique_items
                if item.severity == "HIGH"
            )

            medium_count = sum(
                1
                for item
                in unique_items
                if item.severity == "MEDIUM"
            )

            low_count = sum(
                1
                for item
                in unique_items
                if item.severity == "LOW"
            )

            summary = (
                f"{len(unique_items)} uncertainty item(s): "
                f"{high_count} high, "
                f"{medium_count} medium, "
                f"{low_count} low."
            )

        return UncertaintyAssessment(
            has_uncertainty=bool(
                unique_items
            ),
            items=unique_items,
            summary=summary,
        )

    # ========================================================
    # FINDING GROUNDING
    # ========================================================

    @staticmethod
    def _finding_is_grounded(
        finding: InvestigationFinding,
        evidence: list[EvidenceItem],
    ) -> bool:

        if not finding.evidence_ids:

            return False

        evidence_index = {
            item.evidence_id: item
            for item in evidence
        }

        referenced_items: list[
            EvidenceItem
        ] = []

        for evidence_id in (
            finding.evidence_ids
        ):

            item = evidence_index.get(
                evidence_id
            )

            if item is None:

                return False

            if not item.available:

                return False

            referenced_items.append(
                item
            )

        if not referenced_items:

            return False

        # If finding has a metric, at least one referenced
        # evidence item should have a compatible metric.
        if (
            finding.metric is not None
            and finding.metric.strip()
        ):

            finding_metric = (
                finding.metric
                .strip()
                .lower()
            )

            metrics = [
                item.metric.strip().lower()
                for item in referenced_items
                if (
                    item.metric is not None
                    and item.metric.strip()
                )
            ]

            if metrics:

                if not any(
                    finding_metric == metric
                    or finding_metric in metric
                    or metric in finding_metric
                    for metric in metrics
                ):

                    return False

        return True


# ============================================================
# SERIALIZATION
# ============================================================


def confidence_uncertainty_to_dict(
    result: ConfidenceUncertaintyResult,
) -> dict[str, Any]:
    """
    Convert Day 11.6 result into JSON-compatible output.
    """

    confidence = result.confidence

    uncertainty = result.uncertainty

    return {
        "confidence": {
            "level": confidence.level,
            "score": confidence.score,
            "rationale": confidence.rationale,
            "evidence_count": (
                confidence.evidence_count
            ),
            "available_evidence_count": (
                confidence.available_evidence_count
            ),
            "direct_evidence_count": (
                confidence.direct_evidence_count
            ),
            "derived_evidence_count": (
                confidence.derived_evidence_count
            ),
            "contextual_evidence_count": (
                confidence.contextual_evidence_count
            ),
            "unavailable_evidence_count": (
                confidence.unavailable_evidence_count
            ),
            "average_evidence_confidence": (
                confidence.average_evidence_confidence
            ),
            "grounded_finding_count": (
                confidence.grounded_finding_count
            ),
            "total_finding_count": (
                confidence.total_finding_count
            ),
        },
        "uncertainty": {
            "has_uncertainty": (
                uncertainty.has_uncertainty
            ),
            "summary": uncertainty.summary,
            "items": [
                {
                    "category": item.category,
                    "description": item.description,
                    "severity": item.severity,
                    "evidence_ids": item.evidence_ids,
                }
                for item in uncertainty.items
            ],
        },
    }