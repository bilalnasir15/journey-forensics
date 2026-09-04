from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from .schemas import (
    EvidenceContract,
    EvidenceItem,
    InvestigationFinding,
)


# ============================================================
# DAY 11.7 — GROUNDED RECOMMENDATIONS
# ============================================================
#
# Purpose:
#
# Validate recommendations against the actual evidence
# referenced by an InvestigationFinding.
#
# Grounding chain:
#
#     Evidence
#         ↓
#     Finding
#         ↓
#     Recommendation
#
# Important:
#
# Real statistical evidence may represent the source metric
# like this:
#
#     EvidenceItem.metric = "result.metric"
#     EvidenceItem.value  = "journey_duration_minutes"
#
# Therefore metric grounding must support BOTH:
#
#     1. evidence.metric matching finding.metric
#     2. evidence.value matching finding.metric
#
# This avoids rejecting valid production evidence merely
# because the payload stores the metric name as a value.
# ============================================================


# ============================================================
# RESULT MODELS
# ============================================================


@dataclass
class GroundedRecommendationResult:
    """
    Validation result for one recommendation.
    """

    recommendation: str

    grounded: bool

    finding_title: str

    finding_evidence_ids: list[str] = field(
        default_factory=list
    )

    matched_evidence_ids: list[str] = field(
        default_factory=list
    )

    unsupported_references: list[str] = field(
        default_factory=list
    )

    reason: str = ""


@dataclass
class GroundedRecommendationSummary:
    """
    Collection-level recommendation validation result.
    """

    grounded: bool

    total_recommendations: int

    grounded_recommendations: int

    ungrounded_recommendations: int

    results: list[
        GroundedRecommendationResult
    ] = field(
        default_factory=list
    )

    summary: str = ""


# ============================================================
# VALIDATOR
# ============================================================


class GroundedRecommendationValidator:
    """
    Deterministic validator for evidence-grounded
    recommendations.

    A recommendation is grounded when:

        1. It is non-empty.
        2. The finding contains evidence IDs.
        3. Those evidence IDs exist.
        4. Those evidence items are available.
        5. The finding metric can be resolved from the linked
           evidence.
        6. Explicit numeric references are supported.
        7. Explicit customer/booking identifiers are supported.

    No unsupported business fact is invented.
    """

    # ========================================================
    # SINGLE RECOMMENDATION
    # ========================================================

    def validate(
        self,
        finding: InvestigationFinding,
        recommendation: str,
        evidence_contract: EvidenceContract,
    ) -> GroundedRecommendationResult:
        """
        Validate one recommendation against a finding and
        evidence contract.
        """

        recommendation = (
            recommendation or ""
        ).strip()

        finding_evidence_ids = list(
            dict.fromkeys(
                finding.evidence_ids
            )
        )

        # ----------------------------------------------------
        # Empty recommendation
        # ----------------------------------------------------

        if not recommendation:

            return GroundedRecommendationResult(
                recommendation="",
                grounded=False,
                finding_title=finding.title,
                finding_evidence_ids=(
                    finding_evidence_ids
                ),
                matched_evidence_ids=[],
                unsupported_references=[],
                reason=(
                    "Recommendation is empty and "
                    "cannot be considered grounded."
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

        invalid_finding_ids: list[str] = []

        for evidence_id in finding_evidence_ids:

            item = evidence_index.get(
                evidence_id
            )

            if item is None:

                invalid_finding_ids.append(
                    evidence_id
                )

                continue

            if not item.available:

                invalid_finding_ids.append(
                    evidence_id
                )

                continue

            matched_evidence_ids.append(
                evidence_id
            )

        # ----------------------------------------------------
        # No valid evidence
        # ----------------------------------------------------

        if not matched_evidence_ids:

            return GroundedRecommendationResult(
                recommendation=recommendation,
                grounded=False,
                finding_title=finding.title,
                finding_evidence_ids=(
                    finding_evidence_ids
                ),
                matched_evidence_ids=[],
                unsupported_references=(
                    invalid_finding_ids
                ),
                reason=(
                    "Recommendation cannot be grounded "
                    "because the associated finding has "
                    "no valid available evidence."
                ),
            )

        referenced_evidence = [
            evidence_index[evidence_id]
            for evidence_id
            in matched_evidence_ids
        ]

        unsupported_references: list[str] = []

        # ----------------------------------------------------
        # Metric compatibility
        # ----------------------------------------------------

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

                unsupported_references.append(
                    finding.metric
                )

        # ----------------------------------------------------
        # Numeric references
        # ----------------------------------------------------

        recommendation_numbers = (
            self._extract_numbers(
                recommendation
            )
        )

        evidence_numbers = (
            self._extract_evidence_numbers(
                referenced_evidence
            )
        )

        for token, number in recommendation_numbers:

            if not self._number_supported(
                number,
                evidence_numbers,
            ):

                unsupported_references.append(
                    token
                )

        # ----------------------------------------------------
        # Customer / booking IDs
        # ----------------------------------------------------

        recommendation_identifiers = (
            self._extract_identifiers(
                recommendation
            )
        )

        evidence_identifiers = (
            self._extract_evidence_identifiers(
                referenced_evidence
            )
        )

        for identifier in recommendation_identifiers:

            if (
                identifier.lower()
                not in evidence_identifiers
            ):

                unsupported_references.append(
                    identifier
                )

        # ----------------------------------------------------
        # De-duplicate unsupported references
        # ----------------------------------------------------

        unsupported_references = list(
            dict.fromkeys(
                unsupported_references
            )
        )

        # ----------------------------------------------------
        # Final decision
        # ----------------------------------------------------

        grounded = (
            len(
                unsupported_references
            )
            == 0
        )

        if grounded:

            reason = (
                "Recommendation is grounded in the "
                "finding's available evidence."
            )

        else:

            reason = (
                "Recommendation contains unsupported "
                "reference(s) that cannot be traced to "
                "the finding evidence."
            )

        return GroundedRecommendationResult(
            recommendation=recommendation,
            grounded=grounded,
            finding_title=finding.title,
            finding_evidence_ids=(
                finding_evidence_ids
            ),
            matched_evidence_ids=(
                matched_evidence_ids
            ),
            unsupported_references=(
                unsupported_references
            ),
            reason=reason,
        )

    # ========================================================
    # MULTIPLE RECOMMENDATIONS
    # ========================================================

    def validate_all(
        self,
        recommendations: Iterable[
            tuple[
                InvestigationFinding,
                str,
            ]
        ],
        evidence_contract: EvidenceContract,
    ) -> GroundedRecommendationSummary:
        """
        Validate multiple finding/recommendation pairs.
        """

        pairs = list(
            recommendations
        )

        results: list[
            GroundedRecommendationResult
        ] = []

        for finding, recommendation in pairs:

            results.append(
                self.validate(
                    finding=finding,
                    recommendation=recommendation,
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
            - grounded_count
        )

        all_grounded = (
            ungrounded_count == 0
        )

        if all_grounded:

            summary = (
                "All recommendations are grounded "
                "in available investigation evidence."
            )

        else:

            summary = (
                f"{ungrounded_count} of "
                f"{len(results)} recommendation(s) "
                "are not fully grounded."
            )

        return GroundedRecommendationSummary(
            grounded=all_grounded,
            total_recommendations=len(
                results
            ),
            grounded_recommendations=(
                grounded_count
            ),
            ungrounded_recommendations=(
                ungrounded_count
            ),
            results=results,
            summary=summary,
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
        Determine whether an evidence item supports the
        finding metric.

        Supports real-world payload structures such as:

            metric="journey_duration_minutes"

        and:

            metric="result.metric"
            value="journey_duration_minutes"

        and:

            metric="result.source_column"
            value="journey_duration_minutes"
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
            cls._normalize_metric(
                evidence.value
            )
        )

        # ----------------------------------------------------
        # Direct metric match
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
                len(evidence_metric) > 2
            ):
                return True

        # ----------------------------------------------------
        # Metric stored as evidence VALUE
        #
        # Critical production case:
        #
        # result.metric =
        #       journey_duration_minutes
        #
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
        # Nested dictionary/list payload
        # ----------------------------------------------------

        if isinstance(
            evidence.value,
            (
                dict,
                list,
                tuple,
                set,
            ),
        ):

            if cls._contains_metric_value(
                evidence.value,
                finding,
            ):
                return True

        return False

    # ========================================================
    # NORMALIZE METRIC
    # ========================================================

    @staticmethod
    def _normalize_metric(
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
            (
                dict,
                list,
                tuple,
                set,
            ),
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
                cls._normalize_metric(
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
            (
                list,
                tuple,
                set,
            ),
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

    # ========================================================
    # NUMBER EXTRACTION
    # ========================================================

    @staticmethod
    def _extract_numbers(
        text: str,
    ) -> list[
        tuple[str, float]
    ]:

        pattern = re.compile(
            r"(?<![A-Za-z0-9_])"
            r"[-+]?"
            r"(?:"
            r"\d{1,3}(?:,\d{3})+"
            r"|"
            r"\d+(?:\.\d+)?"
            r"|"
            r"\.\d+"
            r")"
            r"%?"
            r"(?![A-Za-z0-9_])"
        )

        results: list[
            tuple[str, float]
        ] = []

        for match in pattern.finditer(
            text
        ):

            token = match.group(
                0
            )

            try:

                number = float(
                    token
                    .replace(
                        ",",
                        "",
                    )
                    .replace(
                        "%",
                        "",
                    )
                )

            except ValueError:

                continue

            results.append(
                (
                    token,
                    number,
                )
            )

        return results

    # ========================================================
    # EVIDENCE NUMBERS
    # ========================================================

    def _extract_evidence_numbers(
        self,
        evidence: Iterable[EvidenceItem],
    ) -> list[float]:

        values: list[float] = []

        for item in evidence:

            values.extend(
                self._numbers_from_value(
                    item.value
                )
            )

            if item.record_count is not None:

                values.extend(
                    self._numbers_from_value(
                        item.record_count
                    )
                )

            if item.detail:

                values.extend(
                    number
                    for _, number
                    in self._extract_numbers(
                        item.detail
                    )
                )

        return values

    # ========================================================
    # RECURSIVE NUMBER EXTRACTION
    # ========================================================

    def _numbers_from_value(
        self,
        value: Any,
    ) -> list[float]:

        if value is None:

            return []

        if isinstance(
            value,
            bool,
        ):

            return []

        if isinstance(
            value,
            int,
        ):

            return [
                float(value)
            ]

        if isinstance(
            value,
            float,
        ):

            return [
                float(value)
            ]

        if isinstance(
            value,
            str,
        ):

            return [
                number
                for _, number
                in self._extract_numbers(
                    value
                )
            ]

        if isinstance(
            value,
            dict,
        ):

            numbers: list[float] = []

            for nested in value.values():

                numbers.extend(
                    self._numbers_from_value(
                        nested
                    )
                )

            return numbers

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):

            numbers: list[float] = []

            for nested in value:

                numbers.extend(
                    self._numbers_from_value(
                        nested
                    )
                )

            return numbers

        return []

    # ========================================================
    # NUMBER SUPPORT
    # ========================================================

    @staticmethod
    def _number_supported(
        number: float,
        evidence_numbers: list[float],
    ) -> bool:

        tolerance = 0.01

        for evidence_number in evidence_numbers:

            # Direct numeric match.
            if (
                abs(
                    number
                    - evidence_number
                )
                <= tolerance
            ):

                return True

            # Percentage representation:
            #
            # 12.69 ↔ 0.1269
            #

            if (
                abs(
                    number
                    -
                    (
                        evidence_number
                        * 100
                    )
                )
                <= tolerance
            ):

                return True

            if (
                abs(
                    (
                        number
                        * 100
                    )
                    -
                    evidence_number
                )
                <= tolerance
            ):

                return True

        return False

    # ========================================================
    # IDENTIFIER EXTRACTION
    # ========================================================

    @staticmethod
    def _extract_identifiers(
        text: str,
    ) -> list[str]:

        pattern = re.compile(
            r"\b(?:C|B)\d{3,}\b",
            re.IGNORECASE,
        )

        identifiers = [
            identifier.lower()
            for identifier
            in pattern.findall(
                text
            )
        ]

        return list(
            dict.fromkeys(
                identifiers
            )
        )

    # ========================================================
    # EVIDENCE IDENTIFIERS
    # ========================================================

    def _extract_evidence_identifiers(
        self,
        evidence: Iterable[EvidenceItem],
    ) -> set[str]:

        identifiers: set[str] = set()

        for item in evidence:

            values = [
                item.value,
                item.detail,
                item.source_reference,
            ]

            for value in values:

                if value is None:

                    continue

                if isinstance(
                    value,
                    (
                        dict,
                        list,
                        tuple,
                        set,
                    ),
                ):

                    identifiers.update(
                        self._identifiers_from_nested(
                            value
                        )
                    )

                    continue

                if not isinstance(
                    value,
                    str,
                ):

                    continue

                identifiers.update(
                    self._extract_identifiers(
                        value
                    )
                )

        return identifiers

    # ========================================================
    # NESTED IDENTIFIER SEARCH
    # ========================================================

    def _identifiers_from_nested(
        self,
        value: Any,
    ) -> set[str]:

        identifiers: set[str] = set()

        if isinstance(
            value,
            str,
        ):

            identifiers.update(
                self._extract_identifiers(
                    value
                )
            )

            return identifiers

        if isinstance(
            value,
            dict,
        ):

            for nested in value.values():

                identifiers.update(
                    self._identifiers_from_nested(
                        nested
                    )
                )

            return identifiers

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):

            for nested in value:

                identifiers.update(
                    self._identifiers_from_nested(
                        nested
                    )
                )

        return identifiers


# ============================================================
# SERIALIZATION
# ============================================================


def grounded_recommendation_result_to_dict(
    result: GroundedRecommendationResult,
) -> dict[str, Any]:

    return {
        "recommendation": (
            result.recommendation
        ),
        "grounded": (
            result.grounded
        ),
        "finding_title": (
            result.finding_title
        ),
        "finding_evidence_ids": (
            result.finding_evidence_ids
        ),
        "matched_evidence_ids": (
            result.matched_evidence_ids
        ),
        "unsupported_references": (
            result.unsupported_references
        ),
        "reason": (
            result.reason
        ),
    }


def grounded_recommendation_summary_to_dict(
    summary: GroundedRecommendationSummary,
) -> dict[str, Any]:

    return {
        "grounded": (
            summary.grounded
        ),
        "total_recommendations": (
            summary.total_recommendations
        ),
        "grounded_recommendations": (
            summary.grounded_recommendations
        ),
        "ungrounded_recommendations": (
            summary.ungrounded_recommendations
        ),
        "summary": (
            summary.summary
        ),
        "results": [
            grounded_recommendation_result_to_dict(
                result
            )
            for result
            in summary.results
        ],
    }


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def validate_grounded_recommendation(
    finding: InvestigationFinding,
    recommendation: str,
    evidence_contract: EvidenceContract,
) -> GroundedRecommendationResult:

    validator = (
        GroundedRecommendationValidator()
    )

    return validator.validate(
        finding=finding,
        recommendation=recommendation,
        evidence_contract=evidence_contract,
    )


def validate_grounded_recommendations(
    recommendations: Iterable[
        tuple[
            InvestigationFinding,
            str,
        ]
    ],
    evidence_contract: EvidenceContract,
) -> GroundedRecommendationSummary:

    validator = (
        GroundedRecommendationValidator()
    )

    return validator.validate_all(
        recommendations=recommendations,
        evidence_contract=evidence_contract,
    )