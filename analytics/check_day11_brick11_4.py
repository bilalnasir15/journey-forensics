from __future__ import annotations

import sys
from pathlib import Path

from pydantic import ValidationError


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# IMPORTS
# ============================================================

from backend.ai.evidence_validator import (
    EvidenceValidator,
    validation_result_to_dict,
)

from backend.ai.schemas import (
    EvidenceContract,
    EvidenceItem,
    EvidenceProvenance,
    EvidenceSupportLevel,
    EvidenceType,
    ProvenanceSourceType,
)


# ============================================================
# TEST COUNTERS
# ============================================================

total_checks = 0
passed_checks = 0


def check(
    name: str,
    condition: bool,
    detail: str,
) -> None:

    global total_checks
    global passed_checks

    total_checks += 1

    if condition:

        passed_checks += 1

        print(
            f"{name}: PASS"
        )

        print(
            f"    {detail}"
        )

    else:

        print(
            f"{name}: FAIL"
        )

        print(
            f"    {detail}"
        )


# ============================================================
# VALID PROVENANCE
# ============================================================

valid_provenance = EvidenceProvenance(
    source_type=(
        ProvenanceSourceType.TOOL
    ),
    source_name="statistical_tool",
    tool_name="StatisticalTool",
    endpoint="/ai/investigate",
    dataset="journeys",
    table="journeys",
    field="journey_duration_minutes",
    retrieval_reference=(
        "statistical_tool.flagged_count"
    ),
)


# ============================================================
# VALID CONTRACT
# ============================================================

valid_contract = EvidenceContract(
    version="1.0",
    evidence=[
        EvidenceItem(
            evidence_id="stat_001",
            source="statistical_tool",
            category="statistical",
            evidence_type=(
                EvidenceType.STATISTICAL_RESULT
            ),
            support_level=(
                EvidenceSupportLevel.DIRECT
            ),
            metric="journey_duration_minutes",
            value=1015,
            unit="records",
            detail=(
                "1015 journeys exceeded "
                "the 90-minute threshold."
            ),
            available=True,
            source_reference=(
                "statistical_tool.flagged_count"
            ),
            record_count=8000,
            confidence=1.0,
            provenance=valid_provenance,
        ),
    ],
)


# ============================================================
# VALIDATOR
# ============================================================

validator = EvidenceValidator()


# ============================================================
# TEST 1
# VALID CONTRACT
# ============================================================

result = validator.validate(
    valid_contract
)

check(
    "Valid evidence contract passes",
    result.valid,
    result.summary,
)


# ============================================================
# TEST 2
# TOTAL COUNT
# ============================================================

check(
    "Total evidence count is correct",
    result.total_evidence == 1,
    (
        f"total_evidence="
        f"{result.total_evidence}"
    ),
)


# ============================================================
# TEST 3
# VALID COUNT
# ============================================================

check(
    "Valid evidence count is correct",
    result.valid_evidence == 1,
    (
        f"valid_evidence="
        f"{result.valid_evidence}"
    ),
)


# ============================================================
# TEST 4
# INVALID COUNT
# ============================================================

check(
    "Invalid evidence count is zero",
    result.invalid_evidence == 0,
    (
        f"invalid_evidence="
        f"{result.invalid_evidence}"
    ),
)


# ============================================================
# TEST 5
# VALID ID
# ============================================================

check(
    "Valid evidence ID is retained",
    (
        "stat_001"
        in result.validated_evidence_ids
    ),
    (
        "validated_ids="
        f"{result.validated_evidence_ids}"
    ),
)


# ============================================================
# TEST 6
# SCHEMA PROTECTS EMPTY SOURCE
# ============================================================

try:

    EvidenceItem(
        evidence_id="invalid_source",
        source="",
        category="statistical",
        evidence_type=(
            EvidenceType.STATISTICAL_RESULT
        ),
        support_level=(
            EvidenceSupportLevel.DIRECT
        ),
        metric="flagged_count",
        value=1015,
        detail="1015 records.",
    )

    check(
        "Schema rejects empty source",
        False,
        "Empty source was accepted.",
    )

except ValidationError:

    check(
        "Schema rejects empty source",
        True,
        (
            "Pydantic correctly rejects "
            "an empty source before validation."
        ),
    )


# ============================================================
# TEST 7
# SCHEMA PROTECTS EMPTY CATEGORY
# ============================================================

try:

    EvidenceItem(
        evidence_id="invalid_category",
        source="statistical_tool",
        category="",
        evidence_type=(
            EvidenceType.STATISTICAL_RESULT
        ),
        support_level=(
            EvidenceSupportLevel.DIRECT
        ),
        metric="flagged_count",
        value=1015,
        detail="1015 records.",
    )

    check(
        "Schema rejects empty category",
        False,
        "Empty category was accepted.",
    )

except ValidationError:

    check(
        "Schema rejects empty category",
        True,
        (
            "Pydantic correctly rejects "
            "an empty category before validation."
        ),
    )


# ============================================================
# TEST 8
# VALID UNAVAILABLE EVIDENCE
# ============================================================

unavailable = EvidenceItem(
    evidence_id="unavailable_001",
    source="complaint_tool",
    category="complaints",
    evidence_type=(
        EvidenceType.UNAVAILABLE
    ),
    support_level=(
        EvidenceSupportLevel.UNAVAILABLE
    ),
    available=False,
    value=None,
)

item_result = validator.validate_item(
    unavailable
)

check(
    "Valid unavailable evidence passes",
    item_result.valid,
    (
        f"issues="
        f"{len(item_result.issues)}"
    ),
)


# ============================================================
# TEST 9
# PYDANTIC NORMALIZES UNAVAILABLE EVIDENCE
# ============================================================

normalized_unavailable = EvidenceItem(
    evidence_id="unavailable_002",
    source="complaint_tool",
    category="complaints",
    evidence_type=(
        EvidenceType.METRIC
    ),
    support_level=(
        EvidenceSupportLevel.DIRECT
    ),
    available=False,
    value=123,
)

check(
    "Unavailable evidence is normalized",
    (
        normalized_unavailable.value is None
        and
        normalized_unavailable.evidence_type
        == EvidenceType.UNAVAILABLE
        and
        normalized_unavailable.support_level
        == EvidenceSupportLevel.UNAVAILABLE
    ),
    (
        f"value="
        f"{normalized_unavailable.value}; "
        f"type="
        f"{normalized_unavailable.evidence_type.value}; "
        f"support="
        f"{normalized_unavailable.support_level.value}"
    ),
)


# ============================================================
# TEST 10
# MISMATCHED PROVENANCE SOURCE
# ============================================================

bad_provenance_source = EvidenceItem(
    evidence_id="bad_provenance",
    source="statistical_tool",
    category="statistical",
    evidence_type=(
        EvidenceType.STATISTICAL_RESULT
    ),
    support_level=(
        EvidenceSupportLevel.DIRECT
    ),
    metric="flagged_count",
    value=1015,
    source_reference=(
        "statistical_tool.flagged_count"
    ),
    provenance=EvidenceProvenance(
        source_type=(
            ProvenanceSourceType.TOOL
        ),
        source_name="different_source",
        field="flagged_count",
        retrieval_reference=(
            "statistical_tool.flagged_count"
        ),
    ),
)

item_result = validator.validate_item(
    bad_provenance_source
)

check(
    "Mismatched provenance source is rejected",
    not item_result.valid,
    (
        f"issues="
        f"{len(item_result.issues)}"
    ),
)


# ============================================================
# TEST 11
# MISMATCHED PROVENANCE FIELD
# ============================================================

bad_provenance_field = EvidenceItem(
    evidence_id="bad_field",
    source="statistical_tool",
    category="statistical",
    evidence_type=(
        EvidenceType.STATISTICAL_RESULT
    ),
    support_level=(
        EvidenceSupportLevel.DIRECT
    ),
    metric="flagged_count",
    value=1015,
    provenance=EvidenceProvenance(
        source_type=(
            ProvenanceSourceType.TOOL
        ),
        source_name="statistical_tool",
        field="different_metric",
    ),
)

item_result = validator.validate_item(
    bad_provenance_field
)

check(
    "Mismatched provenance field is rejected",
    not item_result.valid,
    (
        f"issues="
        f"{len(item_result.issues)}"
    ),
)


# ============================================================
# TEST 12
# WARNING DOES NOT INVALIDATE
# ============================================================

warning_item = EvidenceItem(
    evidence_id="warning_item",
    source="test_tool",
    category="metric",
    evidence_type=(
        EvidenceType.METRIC
    ),
    support_level=(
        EvidenceSupportLevel.DIRECT
    ),
    value=100,
)

item_result = validator.validate_item(
    warning_item
)

warning_found = any(
    issue.severity == "WARNING"
    for issue in item_result.issues
)

check(
    "Non-critical issue becomes warning",
    item_result.valid
    and warning_found,
    (
        f"valid={item_result.valid}; "
        f"issues={len(item_result.issues)}"
    ),
)


# ============================================================
# TEST 13
# SERIALIZATION
# ============================================================

serialized = (
    validation_result_to_dict(
        result
    )
)

check(
    "Validation result is serializable",
    (
        isinstance(
            serialized,
            dict,
        )
        and "valid"
        in serialized
        and "issues"
        in serialized
        and "summary"
        in serialized
    ),
    (
        f"keys="
        f"{list(serialized.keys())}"
    ),
)


# ============================================================
# TEST 14
# SOURCE REFERENCE
# ============================================================

reference_item = EvidenceItem(
    evidence_id="reference_001",
    source="statistical_tool",
    category="statistical",
    evidence_type=(
        EvidenceType.STATISTICAL_RESULT
    ),
    support_level=(
        EvidenceSupportLevel.DIRECT
    ),
    metric="flagged_count",
    value=1015,
    detail="1015 journeys flagged.",
    source_reference=(
        "statistical_tool.flagged_count"
    ),
)

item_result = validator.validate_item(
    reference_item
)

check(
    "Source reference is accepted",
    item_result.valid,
    (
        f"issues="
        f"{len(item_result.issues)}"
    ),
)


# ============================================================
# TEST 15
# MULTIPLE VALID ITEMS
# ============================================================

multi_contract = EvidenceContract(
    version="1.0",
    evidence=[
        EvidenceItem(
            evidence_id="multi_001",
            source="tool_a",
            category="metric",
            evidence_type=(
                EvidenceType.METRIC
            ),
            support_level=(
                EvidenceSupportLevel.DIRECT
            ),
            metric="record_count",
            value=8000,
            detail="8000 records.",
        ),
        EvidenceItem(
            evidence_id="multi_002",
            source="tool_b",
            category="profile",
            evidence_type=(
                EvidenceType.PROFILE
            ),
            support_level=(
                EvidenceSupportLevel.DIRECT
            ),
            metric="customer_id",
            value="C004781",
            detail=(
                "Customer C004781 exists."
            ),
        ),
        EvidenceItem(
            evidence_id="multi_003",
            source="tool_c",
            category="journey",
            evidence_type=(
                EvidenceType.JOURNEY
            ),
            support_level=(
                EvidenceSupportLevel.DIRECT
            ),
            metric="booking_id",
            value="B007998",
            detail=(
                "Booking B007998 exists."
            ),
        ),
    ],
)

multi_result = validator.validate(
    multi_contract
)

check(
    "Multiple valid evidence items pass",
    (
        multi_result.valid
        and multi_result.total_evidence == 3
        and multi_result.valid_evidence == 3
    ),
    (
        f"total="
        f"{multi_result.total_evidence}; "
        f"valid="
        f"{multi_result.valid_evidence}; "
        f"invalid="
        f"{multi_result.invalid_evidence}"
    ),
)


# ============================================================
# FINAL SUMMARY
# ============================================================

failed_checks = (
    total_checks
    - passed_checks
)

pass_rate = (
    passed_checks
    / total_checks
    * 100
    if total_checks
    else 0.0
)

print()
print("=" * 60)
print(
    "DAY 11.4 — EVIDENCE VALIDATION"
)
print("=" * 60)

print(
    f"Total checks: {total_checks}"
)

print(
    f"Passed: {passed_checks}"
)

print(
    f"Failed: {failed_checks}"
)

print(
    f"Pass rate: {pass_rate:.2f}%"
)

print()

if failed_checks == 0:

    print(
        "DAY 11.4 — PASSED"
    )

    print(
        "Evidence validation is deterministically validated."
    )

    sys.exit(0)

else:

    print(
        "DAY 11.4 — FAILED"
    )

    sys.exit(1)