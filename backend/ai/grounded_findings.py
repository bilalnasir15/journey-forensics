from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .schemas import (
    EvidenceContract,
    EvidenceItem,
    InvestigationFinding,
)


# ============================================================
# DAY 11.5 / 11.9 / 11.10
# GROUNDED FINDINGS
# ============================================================
#
# Purpose:
#
# Validate that each InvestigationFinding is traceable to
# concrete available evidence.
#
# Important matching rule:
#
# A finding metric can be supported when:
#
#   1. Evidence.metric matches the finding metric, OR
#   2. Evidence.metric is a payload field such as
#      result.metric / result.source_column and
#      Evidence.value contains the finding metric.
#
# Example:
#
# Finding:
#     metric = "journey_duration_minutes"
#
# Evidence:
#     metric = "result.source_column"
#     value  = "journey_duration_minutes"
#
# This IS a valid grounding relationship.
# ============================================================


# ============================================================
# RESULT MODELS
# ============================================================


@dataclass
class GroundedFindingResult:
    """
    Validation result for one investigation finding.
    """

    grounded: bool

    finding_title: str

    evidence_ids: list[str] = field(
        default_factory=list
    )

    matched_evidence_ids: list[str] = field(
        default_factory=list
    )

    missing_evidence_ids: list[str] = field(
        default_factory=list
    )

    unavailable_evidence_ids: list[str] = field(
        default_factory=list
    )

    metric_mismatches: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    reason: str = ""


@dataclass
class GroundedFindingsSummary:
    """
    Collection-level grounding result.
    """

    grounded: bool

    total_findings: int

    grounded_findings: int

    ungrounded_findings: int

    results: list[GroundedFindingResult] = field(
        default_factory=list
    )

    summary: str = ""


# ============================================================
# GROUNDED FINDING VALIDATOR
# ============================================================


class GroundedFindingValidator:
    """
    Deterministic validator for InvestigationFinding objects.

    A finding is grounded when:

        1. It contains evidence IDs.
        2. Every referenced evidence ID exists.
        3. Every referenced evidence item is available.
        4. Its metric is compatible with at least one linked
           evidence item when a finding metric exists.

    The validator does not infer causality.
    """

    # ========================================================
    # SINGLE FINDING
    # ========================================================

    def validate(
        self,
        finding: InvestigationFinding,
        evidence_contract: EvidenceContract,
    ) -> GroundedFindingResult:
        """
        Validate one finding against an evidence contract.
        """

        evidence_ids = list(
            dict.fromkeys(
                finding.evidence_ids
            )
        )

        # ----------------------------------------------------
        # No evidence IDs
        # ----------------------------------------------------

        if not evidence_ids:

            return GroundedFindingResult(
                grounded=False,
                finding_title=finding.title,
                evidence_ids=[],
                matched_evidence_ids=[],
                missing_evidence_ids=[],
                unavailable_evidence_ids=[],
                metric_mismatches=[],
                warnings=[
                    "Finding does not reference any evidence."
                ],
                reason=(
                    "Finding is not grounded because "
                    "evidence_ids is empty."
                ),
            )

        # ----------------------------------------------------
        # Evidence index
        # ----------------------------------------------------

        evidence_index = {
            item.evidence_id: item
            for item in evidence_contract.evidence
        }

        matched_evidence_ids: list[str] = []

        missing_evidence_ids: list[str] = []

        unavailable_evidence_ids: list[str] = []

        referenced_evidence: list[
            EvidenceItem
        ] = []

        # ----------------------------------------------------
        # Resolve IDs
        # ----------------------------------------------------

        for evidence_id in evidence_ids:

            item = evidence_index.get(
                evidence_id
            )

            if item is None:

                missing_evidence_ids.append(
                    evidence_id
                )

                continue

            if not item.available:

                unavailable_evidence_ids.append(
                    evidence_id
                )

                continue

            matched_evidence_ids.append(
                evidence_id
            )

            referenced_evidence.append(
                item
            )

        # ----------------------------------------------------
        # Any missing/unavailable evidence means the finding
        # cannot be fully grounded.
        # ----------------------------------------------------

        if (
            missing_evidence_ids
            or
            unavailable_evidence_ids
        ):

            reasons: list[str] = []

            if missing_evidence_ids:

                reasons.append(
                    (
                        "Missing evidence IDs: "
                        +
                        ", ".join(
                            missing_evidence_ids
                        )
                    )
                )

            if unavailable_evidence_ids:

                reasons.append(
                    (
                        "Unavailable evidence IDs: "
                        +
                        ", ".join(
                            unavailable_evidence_ids
                        )
                    )
                )

            return GroundedFindingResult(
                grounded=False,
                finding_title=finding.title,
                evidence_ids=evidence_ids,
                matched_evidence_ids=(
                    matched_evidence_ids
                ),
                missing_evidence_ids=(
                    missing_evidence_ids
                ),
                unavailable_evidence_ids=(
                    unavailable_evidence_ids
                ),
                metric_mismatches=[],
                warnings=[],
                reason="; ".join(
                    reasons
                ),
            )

        # ----------------------------------------------------
        # Metric validation
        # ----------------------------------------------------

        metric_mismatches: list[str] = []

        if finding.metric:

            metric_supported = any(
                self._evidence_supports_metric(
                    finding_metric=(
                        finding.metric
                    ),
                    evidence=item,
                )
                for item
                in referenced_evidence
            )

            if not metric_supported:

                metric_mismatches.append(
                    finding.metric
                )

        # ----------------------------------------------------
        # Final decision
        # ----------------------------------------------------

        grounded = (
            len(metric_mismatches)
            == 0
        )

        if grounded:

            reason = (
                "Finding is grounded in available "
                "referenced evidence."
            )

        else:

            reason = (
                "Finding references available evidence, "
                "but its metric could not be matched "
                "to the referenced evidence."
            )

        return GroundedFindingResult(
            grounded=grounded,
            finding_title=finding.title,
            evidence_ids=evidence_ids,
            matched_evidence_ids=(
                matched_evidence_ids
            ),
            missing_evidence_ids=[],
            unavailable_evidence_ids=[],
            metric_mismatches=(
                metric_mismatches
            ),
            warnings=[],
            reason=reason,
        )

    # ========================================================
    # MULTIPLE FINDINGS
    # ========================================================

    def validate_all(
        self,
        findings: Iterable[
            InvestigationFinding
        ],
        evidence_contract: EvidenceContract,
    ) -> GroundedFindingsSummary:
        """
        Validate multiple findings.
        """

        finding_list = list(
            findings
        )

        results: list[
            GroundedFindingResult
        ] = []

        for finding in finding_list:

            results.append(
                self.validate(
                    finding=finding,
                    evidence_contract=evidence_contract,
                )
            )

        grounded_count = sum(
            1
            for result
            in results
            if result.grounded
        )

        ungrounded_count = (
            len(results)
            -
            grounded_count
        )

        all_grounded = (
            ungrounded_count == 0
        )

        if all_grounded:

            summary_text = (
                "All investigation findings are "
                "grounded in available evidence."
            )

        else:

            summary_text = (
                f"{ungrounded_count} of "
                f"{len(results)} finding(s) "
                "are not fully grounded."
            )

        return GroundedFindingsSummary(
            grounded=all_grounded,
            total_findings=len(
                results
            ),
            grounded_findings=(
                grounded_count
            ),
            ungrounded_findings=(
                ungrounded_count
            ),
            results=results,
            summary=summary_text,
        )

    # ========================================================
    # METRIC SUPPORT
    # ========================================================

    @classmethod
    def _evidence_supports_metric(
        cls,
        finding_metric: str,
        evidence: EvidenceItem,
    ) -> bool:
        """
        Determine whether one EvidenceItem supports a finding
        metric.

        Supported patterns:

            Pattern 1:
                evidence.metric == finding.metric

            Pattern 2:
                evidence.metric contains finding.metric

            Pattern 3:
                evidence.metric is a payload location and
                evidence.value == finding.metric

            Example:
                finding.metric:
                    journey_duration_minutes

                evidence:
                    metric = result.source_column
                    value  = journey_duration_minutes

                Result:
                    True
        """

        finding = (
            cls._normalize_metric(
                finding_metric
            )
        )

        if not finding:

            return False

        evidence_metric = (
            cls._normalize_metric(
                evidence.metric
            )
        )

        evidence_value = (
            cls._normalize_value(
                evidence.value
            )
        )

        # ----------------------------------------------------
        # Direct evidence metric match
        # ----------------------------------------------------

        if evidence_metric:

            if (
                evidence_metric
                == finding
            ):
                return True

            if (
                finding
                in evidence_metric
            ):
                return True

            if (
                evidence_metric
                in finding
                and
                len(evidence_metric)
                > 2
            ):
                return True

        # ----------------------------------------------------
        # Evidence value match
        #
        # Critical for nested statistical payloads:
        #
        # result.metric = journey_duration_minutes
        # result.source_column =
        # journey_duration_minutes
        # ----------------------------------------------------

        if evidence_value:

            if (
                evidence_value
                == finding
            ):
                return True

            if (
                finding
                in evidence_value
            ):
                return True

        # ----------------------------------------------------
        # Dictionary/list values
        # ----------------------------------------------------

        if isinstance(
            evidence.value,
            (dict, list, tuple, set),
        ):

            if cls._contains_metric_value(
                evidence.value,
                finding,
            ):
                return True

        return False

    # ========================================================
    # NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_metric(
        value: Any,
    ) -> str:

        if value is None:

            return ""

        return (
            str(value)
            .strip()
            .lower()
            .replace(
                " ",
                "_",
            )
            .replace(
                "-",
                "_",
            )
        )

    @staticmethod
    def _normalize_value(
        value: Any,
    ) -> str:

        if value is None:

            return ""

        if isinstance(
            value,
            bool,
        ):

            return ""

        if isinstance(
            value,
            (dict, list, tuple, set),
        ):

            return ""

        return (
            str(value)
            .strip()
            .lower()
            .replace(
                " ",
                "_",
            )
            .replace(
                "-",
                "_",
            )
        )

    # ========================================================
    # RECURSIVE METRIC SEARCH
    # ========================================================

    @classmethod
    def _contains_metric_value(
        cls,
        value: Any,
        finding_metric: str,
    ) -> bool:
        """
        Recursively search arbitrary payloads for the finding
        metric.
        """

        finding = (
            cls._normalize_metric(
                finding_metric
            )
        )

        if value is None:

            return False

        if isinstance(
            value,
            str,
        ):

            normalized = (
                cls._normalize_value(
                    value
                )
            )

            return (
                normalized
                == finding
                or
                finding
                in normalized
            )

        if isinstance(
            value,
            dict,
        ):

            return any(
                cls._contains_metric_value(
                    nested,
                    finding,
                )
                for nested
                in value.values()
            )

        if isinstance(
            value,
            (list, tuple, set),
        ):

            return any(
                cls._contains_metric_value(
                    nested,
                    finding,
                )
                for nested
                in value
            )

        return False


# ============================================================
# SERIALIZATION
# ============================================================


def grounded_finding_result_to_dict(
    result: GroundedFindingResult,
) -> dict[str, Any]:
    """
    Serialize one grounded finding result.
    """

    return {
        "grounded": result.grounded,
        "finding_title": result.finding_title,
        "evidence_ids": (
            result.evidence_ids
        ),
        "matched_evidence_ids": (
            result.matched_evidence_ids
        ),
        "missing_evidence_ids": (
            result.missing_evidence_ids
        ),
        "unavailable_evidence_ids": (
            result.unavailable_evidence_ids
        ),
        "metric_mismatches": (
            result.metric_mismatches
        ),
        "warnings": result.warnings,
        "reason": result.reason,
    }


def grounded_findings_summary_to_dict(
    summary: GroundedFindingsSummary,
) -> dict[str, Any]:
    """
    Serialize a grounded findings summary.
    """

    return {
        "grounded": summary.grounded,
        "total_findings": (
            summary.total_findings
        ),
        "grounded_findings": (
            summary.grounded_findings
        ),
        "ungrounded_findings": (
            summary.ungrounded_findings
        ),
        "summary": summary.summary,
        "results": [
            grounded_finding_result_to_dict(
                result
            )
            for result
            in summary.results
        ],
    }