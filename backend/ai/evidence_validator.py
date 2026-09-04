from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .schemas import (
    EvidenceContract,
    EvidenceItem,
    EvidenceSupportLevel,
    EvidenceType,
)


# ============================================================
# VALIDATION ISSUE
# ============================================================


@dataclass
class EvidenceValidationIssue:
    """
    One validation issue associated with an evidence item.
    """

    evidence_id: str

    field: str

    message: str

    severity: str = "ERROR"


# ============================================================
# EVIDENCE ITEM VALIDATION RESULT
# ============================================================


@dataclass
class EvidenceItemValidationResult:
    """
    Validation result for one EvidenceItem.
    """

    evidence_id: str

    valid: bool

    issues: list[EvidenceValidationIssue] = field(
        default_factory=list
    )


# ============================================================
# CONTRACT VALIDATION RESULT
# ============================================================


@dataclass
class EvidenceValidationResult:
    """
    Validation result for a complete EvidenceContract.
    """

    valid: bool

    contract_version: str

    total_evidence: int

    valid_evidence: int

    invalid_evidence: int

    issues: list[EvidenceValidationIssue] = field(
        default_factory=list
    )

    validated_evidence_ids: list[str] = field(
        default_factory=list
    )

    invalid_evidence_ids: list[str] = field(
        default_factory=list
    )

    summary: str = ""


# ============================================================
# EVIDENCE VALIDATOR
# ============================================================


class EvidenceValidator:
    """
    Deterministic validation layer for Day 11.4.

    This validator checks the evidence itself before it is
    trusted by downstream grounding logic.

    It validates:

        - evidence ID
        - source
        - category
        - evidence type
        - support level
        - availability
        - value consistency
        - record count
        - confidence
        - source reference
        - provenance consistency
    """

    CONTRACT_VERSION = "1.0"

    VALID_EVIDENCE_TYPES = {
        item.value
        for item in EvidenceType
    }

    VALID_SUPPORT_LEVELS = {
        item.value
        for item in EvidenceSupportLevel
    }

    # ========================================================
    # PUBLIC API
    # ========================================================

    def validate(
        self,
        contract: EvidenceContract,
    ) -> EvidenceValidationResult:
        """
        Validate a complete EvidenceContract.
        """

        issues: list[
            EvidenceValidationIssue
        ] = []

        validated_ids: list[str] = []

        invalid_ids: list[str] = []

        evidence_items = list(
            contract.evidence
        )

        # ----------------------------------------------------
        # Contract version
        # ----------------------------------------------------

        if not contract.version.strip():

            issues.append(
                EvidenceValidationIssue(
                    evidence_id="__CONTRACT__",
                    field="version",
                    message=(
                        "Evidence contract version "
                        "cannot be empty."
                    ),
                )
            )

        # ----------------------------------------------------
        # Duplicate IDs
        # ----------------------------------------------------

        id_counts: dict[str, int] = {}

        for item in evidence_items:

            evidence_id = (
                item.evidence_id.strip()
            )

            if evidence_id:

                id_counts[evidence_id] = (
                    id_counts.get(
                        evidence_id,
                        0,
                    )
                    + 1
                )

        duplicate_ids = {
            evidence_id
            for (
                evidence_id,
                count,
            ) in id_counts.items()
            if count > 1
        }

        # ----------------------------------------------------
        # Validate each item
        # ----------------------------------------------------

        for item in evidence_items:

            item_result = (
                self.validate_item(
                    item,
                    duplicate_ids=duplicate_ids,
                )
            )

            issues.extend(
                item_result.issues
            )

            if item_result.valid:

                validated_ids.append(
                    item_result.evidence_id
                )

            else:

                invalid_ids.append(
                    item_result.evidence_id
                )

        invalid_ids = list(
            dict.fromkeys(
                invalid_ids
            )
        )

        validated_ids = list(
            dict.fromkeys(
                validated_ids
            )
        )

        invalid_count = len(
            invalid_ids
        )

        valid_count = (
            len(evidence_items)
            - invalid_count
        )

        contract_valid = (
            not issues
        )

        if contract_valid:

            summary = (
                "Evidence contract passed deterministic "
                "validation."
            )

        else:

            summary = (
                f"Evidence contract contains "
                f"{len(issues)} validation issue(s)."
            )

        return EvidenceValidationResult(
            valid=contract_valid,
            contract_version=contract.version,
            total_evidence=len(
                evidence_items
            ),
            valid_evidence=max(
                valid_count,
                0,
            ),
            invalid_evidence=invalid_count,
            issues=issues,
            validated_evidence_ids=(
                validated_ids
            ),
            invalid_evidence_ids=(
                invalid_ids
            ),
            summary=summary,
        )

    # ========================================================
    # SINGLE ITEM VALIDATION
    # ========================================================

    def validate_item(
        self,
        item: EvidenceItem,
        *,
        duplicate_ids: set[str] | None = None,
    ) -> EvidenceItemValidationResult:
        """
        Validate one evidence item.
        """

        issues: list[
            EvidenceValidationIssue
        ] = []

        evidence_id = (
            str(
                item.evidence_id
            ).strip()
        )

        # ----------------------------------------------------
        # Evidence ID
        # ----------------------------------------------------

        if not evidence_id:

            issues.append(
                EvidenceValidationIssue(
                    evidence_id=evidence_id
                    or "__MISSING__",
                    field="evidence_id",
                    message=(
                        "Evidence ID cannot be empty."
                    ),
                )
            )

        if duplicate_ids and (
            evidence_id in duplicate_ids
        ):

            issues.append(
                EvidenceValidationIssue(
                    evidence_id=evidence_id,
                    field="evidence_id",
                    message=(
                        "Evidence ID must be unique "
                        "within the contract."
                    ),
                )
            )

        # ----------------------------------------------------
        # Source
        # ----------------------------------------------------

        source = (
            str(
                item.source
            ).strip()
        )

        if not source:

            issues.append(
                EvidenceValidationIssue(
                    evidence_id=evidence_id,
                    field="source",
                    message=(
                        "Evidence source cannot be empty."
                    ),
                )
            )

        # ----------------------------------------------------
        # Category
        # ----------------------------------------------------

        category = (
            str(
                item.category
            ).strip()
        )

        if not category:

            issues.append(
                EvidenceValidationIssue(
                    evidence_id=evidence_id,
                    field="category",
                    message=(
                        "Evidence category cannot be empty."
                    ),
                )
            )

        # ----------------------------------------------------
        # Evidence type
        # ----------------------------------------------------

        evidence_type = self._enum_value(
            item.evidence_type
        )

        if (
            evidence_type
            not in self.VALID_EVIDENCE_TYPES
        ):

            issues.append(
                EvidenceValidationIssue(
                    evidence_id=evidence_id,
                    field="evidence_type",
                    message=(
                        f"Unsupported evidence type: "
                        f"{evidence_type}"
                    ),
                )
            )

        # ----------------------------------------------------
        # Support level
        # ----------------------------------------------------

        support_level = self._enum_value(
            item.support_level
        )

        if (
            support_level
            not in self.VALID_SUPPORT_LEVELS
        ):

            issues.append(
                EvidenceValidationIssue(
                    evidence_id=evidence_id,
                    field="support_level",
                    message=(
                        f"Unsupported evidence support "
                        f"level: {support_level}"
                    ),
                )
            )

        # ----------------------------------------------------
        # Availability consistency
        # ----------------------------------------------------

        if not item.available:

            if (
                item.value is not None
            ):

                issues.append(
                    EvidenceValidationIssue(
                        evidence_id=evidence_id,
                        field="value",
                        message=(
                            "Unavailable evidence must "
                            "not contain a value."
                        ),
                    )
                )

            if (
                support_level
                != EvidenceSupportLevel.UNAVAILABLE.value
            ):

                issues.append(
                    EvidenceValidationIssue(
                        evidence_id=evidence_id,
                        field="support_level",
                        message=(
                            "Unavailable evidence must "
                            "use UNAVAILABLE support level."
                        ),
                    )
                )

            if (
                evidence_type
                != EvidenceType.UNAVAILABLE.value
            ):

                issues.append(
                    EvidenceValidationIssue(
                        evidence_id=evidence_id,
                        field="evidence_type",
                        message=(
                            "Unavailable evidence must "
                            "use UNAVAILABLE evidence type."
                        ),
                    )
                )

        else:

            # Available evidence should normally provide
            # either a value, detail, metric, or reference.
            has_content = any(
                [
                    item.value is not None,
                    bool(
                        item.detail
                    ),
                    bool(
                        item.metric
                    ),
                    bool(
                        item.source_reference
                    ),
                ]
            )

            if not has_content:

                issues.append(
                    EvidenceValidationIssue(
                        evidence_id=evidence_id,
                        field="value",
                        message=(
                            "Available evidence must contain "
                            "at least one analytical field, "
                            "detail, or source reference."
                        ),
                    )
                )

        # ----------------------------------------------------
        # Confidence
        # ----------------------------------------------------

        if not (
            0.0
            <= float(
                item.confidence
            )
            <= 1.0
        ):

            issues.append(
                EvidenceValidationIssue(
                    evidence_id=evidence_id,
                    field="confidence",
                    message=(
                        "Confidence must be between "
                        "0 and 1."
                    ),
                )
            )

        # ----------------------------------------------------
        # Record count
        # ----------------------------------------------------

        if (
            item.record_count is not None
            and item.record_count < 0
        ):

            issues.append(
                EvidenceValidationIssue(
                    evidence_id=evidence_id,
                    field="record_count",
                    message=(
                        "Record count cannot be negative."
                    ),
                )
            )

        # ----------------------------------------------------
        # Source reference
        # ----------------------------------------------------

        if (
            item.source_reference is not None
            and not str(
                item.source_reference
            ).strip()
        ):

            issues.append(
                EvidenceValidationIssue(
                    evidence_id=evidence_id,
                    field="source_reference",
                    message=(
                        "Source reference cannot be "
                        "an empty string."
                    ),
                )
            )

        # ----------------------------------------------------
        # Provenance
        # ----------------------------------------------------

        if item.provenance is not None:

            provenance_issues = (
                self._validate_provenance(
                    item
                )
            )

            issues.extend(
                provenance_issues
            )

        # ----------------------------------------------------
        # Metric / value relationship
        # ----------------------------------------------------

        if (
            item.value is not None
            and item.metric is None
            and item.detail is None
        ):

            # This is not always invalid, but it is safer to
            # flag it as a warning rather than an error.
            issues.append(
                EvidenceValidationIssue(
                    evidence_id=evidence_id,
                    field="metric",
                    message=(
                        "Evidence has a value but no metric "
                        "or descriptive detail.",
                    ),
                    severity="WARNING",
                )
            )

        # ----------------------------------------------------
        # Final result
        # ----------------------------------------------------

        has_errors = any(
            issue.severity == "ERROR"
            for issue in issues
        )

        return EvidenceItemValidationResult(
            evidence_id=evidence_id,
            valid=not has_errors,
            issues=issues,
        )

    # ========================================================
    # PROVENANCE VALIDATION
    # ========================================================

    def _validate_provenance(
        self,
        item: EvidenceItem,
    ) -> list[EvidenceValidationIssue]:

        issues: list[
            EvidenceValidationIssue
        ] = []

        provenance = item.provenance

        if provenance is None:

            return issues

        # ----------------------------------------------------
        # Source name
        # ----------------------------------------------------

        if not (
            provenance.source_name
            and provenance.source_name.strip()
        ):

            issues.append(
                EvidenceValidationIssue(
                    evidence_id=item.evidence_id,
                    field="provenance.source_name",
                    message=(
                        "Provenance source name "
                        "cannot be empty."
                    ),
                )
            )

        # ----------------------------------------------------
        # Source vs provenance source name
        # ----------------------------------------------------

        if (
            item.source
            and provenance.source_name
            and (
                item.source.strip().lower()
                != provenance.source_name.strip().lower()
            )
        ):

            issues.append(
                EvidenceValidationIssue(
                    evidence_id=item.evidence_id,
                    field="provenance.source_name",
                    message=(
                        "Provenance source name does not "
                        "match the evidence source."
                    ),
                )
            )

        # ----------------------------------------------------
        # Metric propagation
        # ----------------------------------------------------

        if (
            item.metric is not None
            and provenance.field is not None
            and (
                item.metric.strip().lower()
                != provenance.field.strip().lower()
            )
        ):

            issues.append(
                EvidenceValidationIssue(
                    evidence_id=item.evidence_id,
                    field="provenance.field",
                    message=(
                        "Provenance field does not "
                        "match evidence metric."
                    ),
                )
            )

        # ----------------------------------------------------
        # Source reference propagation
        # ----------------------------------------------------

        if (
            item.source_reference is not None
            and provenance.retrieval_reference is not None
            and (
                item.source_reference.strip()
                != provenance.retrieval_reference.strip()
            )
        ):

            issues.append(
                EvidenceValidationIssue(
                    evidence_id=item.evidence_id,
                    field="provenance.retrieval_reference",
                    message=(
                        "Provenance retrieval reference does "
                        "not match evidence source reference."
                    ),
                )
            )

        return issues

    # ========================================================
    # ENUM HELPER
    # ========================================================

    @staticmethod
    def _enum_value(
        value: Any,
    ) -> str:

        if hasattr(
            value,
            "value",
        ):

            return str(
                value.value
            )

        return str(
            value
        )


# ============================================================
# SERIALIZATION
# ============================================================


def validation_result_to_dict(
    result: EvidenceValidationResult,
) -> dict[str, Any]:
    """
    Convert validation result to JSON-compatible dictionary.
    """

    return {
        "valid": result.valid,
        "contract_version": (
            result.contract_version
        ),
        "total_evidence": (
            result.total_evidence
        ),
        "valid_evidence": (
            result.valid_evidence
        ),
        "invalid_evidence": (
            result.invalid_evidence
        ),
        "validated_evidence_ids": (
            result.validated_evidence_ids
        ),
        "invalid_evidence_ids": (
            result.invalid_evidence_ids
        ),
        "summary": result.summary,
        "issues": [
            {
                "evidence_id": issue.evidence_id,
                "field": issue.field,
                "message": issue.message,
                "severity": issue.severity,
            }
            for issue in result.issues
        ],
    }