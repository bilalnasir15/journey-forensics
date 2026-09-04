from __future__ import annotations

import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORTS
# ============================================================

from backend.ai.evidence_guard import HallucinationGuard
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
    """
    Print one validation result.
    """

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
# BUILD PROVENANCE
# ============================================================

statistical_provenance = EvidenceProvenance(
    source_type=ProvenanceSourceType.TOOL,
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
# BUILD EVIDENCE CONTRACT
# ============================================================

evidence_contract = EvidenceContract(
    version="1.0",
    evidence=[
        # ----------------------------------------------------
        # TOTAL RECORDS
        # ----------------------------------------------------

        EvidenceItem(
            evidence_id="stat_records",
            source="statistical_tool",
            category="statistical",
            evidence_type=(
                EvidenceType.STATISTICAL_RESULT
            ),
            support_level=(
                EvidenceSupportLevel.DIRECT
            ),
            metric="record_count",
            value=8000,
            unit="records",
            detail=(
                "8000 journey records were analyzed."
            ),
            available=True,
            source_reference=(
                "statistical_tool.record_count"
            ),
            record_count=8000,
            confidence=1.0,
            provenance=statistical_provenance,
        ),

        # ----------------------------------------------------
        # FLAGGED COUNT
        # ----------------------------------------------------

        EvidenceItem(
            evidence_id="stat_flagged",
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
            unit="records",
            detail=(
                "1015 journeys exceeded the "
                "90-minute threshold."
            ),
            available=True,
            source_reference=(
                "statistical_tool.flagged_count"
            ),
            record_count=8000,
            confidence=1.0,
            provenance=statistical_provenance,
        ),

        # ----------------------------------------------------
        # THRESHOLD
        # ----------------------------------------------------

        EvidenceItem(
            evidence_id="stat_threshold",
            source="statistical_tool",
            category="statistical",
            evidence_type=(
                EvidenceType.STATISTICAL_RESULT
            ),
            support_level=(
                EvidenceSupportLevel.DIRECT
            ),
            metric="threshold",
            value=90.0,
            unit="minutes",
            detail=(
                "The investigation threshold "
                "is 90 minutes."
            ),
            available=True,
            source_reference=(
                "statistical_tool.threshold"
            ),
            record_count=8000,
            confidence=1.0,
            provenance=statistical_provenance,
        ),

        # ----------------------------------------------------
        # FLAGGED RATE
        #
        # Important:
        # Stored as string "12.69%" so the percentage
        # handling is explicitly tested.
        # ----------------------------------------------------

        EvidenceItem(
            evidence_id="stat_rate",
            source="statistical_tool",
            category="statistical",
            evidence_type=(
                EvidenceType.STATISTICAL_RESULT
            ),
            support_level=(
                EvidenceSupportLevel.DERIVED
            ),
            metric="flagged_rate",
            value="12.69%",
            unit="percent",
            detail=(
                "The flagged journey rate "
                "is 12.69%."
            ),
            available=True,
            source_reference=(
                "statistical_tool.flagged_rate"
            ),
            record_count=8000,
            confidence=1.0,
            provenance=statistical_provenance,
        ),

        # ----------------------------------------------------
        # CUSTOMER
        # ----------------------------------------------------

        EvidenceItem(
            evidence_id="customer_record",
            source="customer_profile_tool",
            category="profile",
            evidence_type=EvidenceType.PROFILE,
            support_level=(
                EvidenceSupportLevel.DIRECT
            ),
            metric="customer_id",
            value="C004781",
            unit=None,
            detail=(
                "Customer C004781 exists in "
                "the available profile evidence."
            ),
            available=True,
            source_reference=(
                "customer_profile.customer_id"
            ),
            confidence=1.0,
        ),

        # ----------------------------------------------------
        # BOOKING
        # ----------------------------------------------------

        EvidenceItem(
            evidence_id="booking_record",
            source="journey_tool",
            category="journey",
            evidence_type=EvidenceType.JOURNEY,
            support_level=(
                EvidenceSupportLevel.DIRECT
            ),
            metric="booking_id",
            value="B007998",
            unit=None,
            detail=(
                "Booking B007998 is available "
                "in the journey evidence."
            ),
            available=True,
            source_reference=(
                "journey.booking_id"
            ),
            confidence=1.0,
        ),
    ],
)


# ============================================================
# CREATE GUARD
# ============================================================

guard = HallucinationGuard(
    numeric_tolerance=0.01,
    require_numeric_support=True,
)


# ============================================================
# TEST 1
# VALID NUMERICAL EXPLANATION
# ============================================================

result = guard.validate(
    (
        "1015 journeys exceeded the "
        "90-minute threshold. "
        "The analyzed population contains "
        "8000 records."
    ),
    evidence_contract,
)

check(
    "Valid numerical explanation is supported",
    result.supported,
    result.reason,
)


# ============================================================
# TEST 2
# UNSUPPORTED NUMERIC CLAIM
# ============================================================

result = guard.validate(
    (
        "1200 journeys exceeded the "
        "90-minute threshold."
    ),
    evidence_contract,
)

check(
    "Unsupported numeric claim is rejected",
    not result.supported,
    (
        "Unsupported claims="
        f"{result.unsupported_claims}"
    ),
)


# ============================================================
# TEST 3
# SUPPORTED PERCENTAGE
# ============================================================

result = guard.validate(
    (
        "Exactly 12.69% of journeys were flagged."
    ),
    evidence_contract,
)

check(
    "Supported percentage is accepted",
    result.supported,
    (
        f"reason={result.reason}; "
        f"evidence_ids="
        f"{result.evidence_ids_used}"
    ),
)


# ============================================================
# TEST 4
# UNSUPPORTED PERCENTAGE
# ============================================================

result = guard.validate(
    (
        "Exactly 17.42% of journeys were flagged."
    ),
    evidence_contract,
)

check(
    "Unsupported percentage is rejected",
    not result.supported,
    (
        "Unsupported claims="
        f"{result.unsupported_claims}"
    ),
)


# ============================================================
# TEST 5
# SUPPORTED CUSTOMER
# ============================================================

result = guard.validate(
    (
        "Customer C004781 is represented "
        "in the available evidence."
    ),
    evidence_contract,
)

check(
    "Supported customer identifier is accepted",
    result.supported,
    result.reason,
)


# ============================================================
# TEST 6
# UNSUPPORTED CUSTOMER
# ============================================================

result = guard.validate(
    (
        "Customer C999999 is represented "
        "in the evidence."
    ),
    evidence_contract,
)

check(
    "Unsupported customer identifier is rejected",
    not result.supported,
    (
        "Unsupported claims="
        f"{result.unsupported_claims}"
    ),
)


# ============================================================
# TEST 7
# SUPPORTED BOOKING
# ============================================================

result = guard.validate(
    (
        "Booking B007998 is available "
        "in the journey evidence."
    ),
    evidence_contract,
)

check(
    "Supported booking identifier is accepted",
    result.supported,
    result.reason,
)


# ============================================================
# TEST 8
# UNSUPPORTED BOOKING
# ============================================================

result = guard.validate(
    (
        "Booking B123456 is available "
        "in the journey evidence."
    ),
    evidence_contract,
)

check(
    "Unsupported booking identifier is rejected",
    not result.supported,
    (
        "Unsupported claims="
        f"{result.unsupported_claims}"
    ),
)


# ============================================================
# TEST 9
# SUPPORTED THRESHOLD
# ============================================================

result = guard.validate(
    (
        "The threshold is 90 minutes."
    ),
    evidence_contract,
)

check(
    "Supported threshold is accepted",
    result.supported,
    result.reason,
)


# ============================================================
# TEST 10
# UNSUPPORTED THRESHOLD
# ============================================================

result = guard.validate(
    (
        "The threshold is 150 minutes."
    ),
    evidence_contract,
)

check(
    "Unsupported threshold is rejected",
    not result.supported,
    (
        "Unsupported claims="
        f"{result.unsupported_claims}"
    ),
)


# ============================================================
# TEST 11
# SUPPORTED FINDING
# ============================================================

result = guard.validate(
    (
        "1015 journeys exceeded the threshold."
    ),
    evidence_contract,
)

check(
    "Finding using supported evidence is accepted",
    result.supported,
    result.reason,
)


# ============================================================
# TEST 12
# MIXED VALID + INVALID CLAIM
# ============================================================

result = guard.validate(
    (
        "1015 journeys exceeded the threshold, "
        "and 1200 customers were affected."
    ),
    evidence_contract,
)

check(
    "Mixed supported/unsupported claim is rejected",
    not result.supported,
    (
        "Unsupported claims="
        f"{result.unsupported_claims}"
    ),
)


# ============================================================
# TEST 13
# NO EVIDENCE
# ============================================================

empty_contract = EvidenceContract(
    version="1.0",
    evidence=[],
)

result = guard.validate(
    "8000 records were analyzed.",
    empty_contract,
)

check(
    "No-evidence response is rejected",
    not result.supported,
    result.reason,
)


# ============================================================
# TEST 14
# EMPTY RESPONSE
# ============================================================

result = guard.validate(
    "",
    evidence_contract,
)

check(
    "Empty LLM response is rejected",
    not result.supported,
    result.reason,
)


# ============================================================
# TEST 15
# SERIALIZATION
# ============================================================

result = guard.validate(
    (
        "1015 journeys exceeded the "
        "90-minute threshold."
    ),
    evidence_contract,
)

serialized = HallucinationGuard.to_dict(
    result
)

check(
    "Guard result is serializable",
    (
        isinstance(
            serialized,
            dict,
        )
        and "supported" in serialized
        and "claims" in serialized
        and "evidence_ids_used" in serialized
    ),
    (
        f"keys={list(serialized.keys())}"
    ),
)


# ============================================================
# TEST 16
# EVIDENCE ID CONNECTION
# ============================================================

result = guard.validate(
    (
        "1015 journeys exceeded the "
        "90-minute threshold."
    ),
    evidence_contract,
)

check(
    "Supported claim exposes evidence IDs",
    (
        "stat_flagged"
        in result.evidence_ids_used
        and
        "stat_threshold"
        in result.evidence_ids_used
    ),
    (
        "evidence_ids_used="
        f"{result.evidence_ids_used}"
    ),
)


# ============================================================
# TEST 17
# DECIMAL PERCENTAGE REPRESENTATION
# ============================================================

decimal_percentage_contract = EvidenceContract(
    version="1.0",
    evidence=[
        EvidenceItem(
            evidence_id="decimal_rate",
            source="test_tool",
            category="statistical",
            evidence_type=(
                EvidenceType.STATISTICAL_RESULT
            ),
            support_level=(
                EvidenceSupportLevel.DERIVED
            ),
            metric="flagged_rate",
            value=0.1269,
            unit="ratio",
            detail=(
                "Flagged rate is stored as "
                "decimal ratio 0.1269."
            ),
            available=True,
            source_reference=(
                "test_tool.flagged_rate"
            ),
            confidence=1.0,
        ),
    ],
)

result = guard.validate(
    "The flagged rate is 12.69%.",
    decimal_percentage_contract,
)

check(
    "Percentage matches decimal representation",
    result.supported,
    (
        f"reason={result.reason}; "
        f"evidence_ids="
        f"{result.evidence_ids_used}"
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
    "DAY 11.3 — HALLUCINATION GUARD VALIDATION"
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
        "DAY 11.3 — PASSED"
    )

    print(
        "Hallucination guard is deterministically validated."
    )

    sys.exit(0)

else:

    print(
        "DAY 11.3 — FAILED"
    )

    sys.exit(1)