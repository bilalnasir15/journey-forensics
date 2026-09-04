from __future__ import annotations

import sys
from pathlib import Path

from pydantic import ValidationError


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.ai.schemas import (  # noqa: E402
    EvidenceContract,
    EvidenceItem,
    EvidenceSupportLevel,
    EvidenceType,
)


# ============================================================
# VALIDATION HELPERS
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
# TEST 1 — BASIC EVIDENCE ITEM
# ============================================================

try:

    evidence = EvidenceItem(
        evidence_id="stat_001",
        source="statistical_tool",
        category="statistical",
        evidence_type=EvidenceType.STATISTICAL_RESULT,
        support_level=EvidenceSupportLevel.DIRECT,
        metric="journey_duration_minutes",
        value=1015,
        unit="records",
        detail=(
            "1015 journeys meet or exceed the "
            "90-minute threshold."
        ),
        available=True,
        source_reference=(
            "statistical_tool.flagged_count"
        ),
        record_count=8000,
        confidence=1.0,
    )

    check(
        "EvidenceItem can be created",
        True,
        "Valid evidence object created",
    )

except Exception as exc:

    check(
        "EvidenceItem can be created",
        False,
        str(exc),
    )

    evidence = None


# ============================================================
# TEST 2 — STABLE EVIDENCE ID
# ============================================================

if evidence is not None:

    check(
        "Evidence ID exists",
        bool(evidence.evidence_id),
        f"evidence_id={evidence.evidence_id}",
    )


# ============================================================
# TEST 3 — SOURCE IS REQUIRED
# ============================================================

try:

    EvidenceItem(
        evidence_id="invalid_001",
        source="",
        category="statistical",
    )

    check(
        "Source cannot be empty",
        False,
        "Empty source was accepted",
    )

except ValidationError:

    check(
        "Source cannot be empty",
        True,
        "Validation correctly rejected empty source",
    )


# ============================================================
# TEST 4 — CATEGORY IS REQUIRED
# ============================================================

try:

    EvidenceItem(
        evidence_id="invalid_002",
        source="statistical_tool",
        category="",
    )

    check(
        "Category cannot be empty",
        False,
        "Empty category was accepted",
    )

except ValidationError:

    check(
        "Category cannot be empty",
        True,
        "Validation correctly rejected empty category",
    )


# ============================================================
# TEST 5 — CONFIDENCE RANGE
# ============================================================

try:

    EvidenceItem(
        evidence_id="invalid_003",
        source="statistical_tool",
        category="statistical",
        confidence=1.5,
    )

    check(
        "Confidence is bounded 0-1",
        False,
        "Invalid confidence was accepted",
    )

except ValidationError:

    check(
        "Confidence is bounded 0-1",
        True,
        "Confidence bounds are enforced",
    )


# ============================================================
# TEST 6 — RECORD COUNT CANNOT BE NEGATIVE
# ============================================================

try:

    EvidenceItem(
        evidence_id="invalid_004",
        source="statistical_tool",
        category="statistical",
        record_count=-1,
    )

    check(
        "Record count cannot be negative",
        False,
        "Negative record_count was accepted",
    )

except ValidationError:

    check(
        "Record count cannot be negative",
        True,
        "Negative record_count rejected",
    )


# ============================================================
# TEST 7 — UNAVAILABLE EVIDENCE NORMALIZATION
# ============================================================

try:

    unavailable = EvidenceItem(
        evidence_id="unavailable_001",
        source="complaint_system",
        category="complaints",
        available=False,
        value=None,
    )

    check(
        "Unavailable evidence is supported",
        unavailable.support_level
        == EvidenceSupportLevel.UNAVAILABLE,
        (
            "support_level="
            f"{unavailable.support_level.value}"
        ),
    )

except Exception as exc:

    check(
        "Unavailable evidence is supported",
        False,
        str(exc),
    )


# ============================================================
# TEST 8 — CONTRACT CREATION
# ============================================================

try:

    contract = EvidenceContract(
        version="1.0",
        evidence=[
            evidence,
            unavailable,
        ],
    )

    check(
        "EvidenceContract can be created",
        True,
        (
            f"version={contract.version}, "
            f"items={len(contract.evidence)}"
        ),
    )

except Exception as exc:

    check(
        "EvidenceContract can be created",
        False,
        str(exc),
    )

    contract = None


# ============================================================
# TEST 9 — AVAILABLE COUNT
# ============================================================

if contract is not None:

    check(
        "Available evidence count is correct",
        contract.available_count == 1,
        (
            f"available_count="
            f"{contract.available_count}"
        ),
    )


# ============================================================
# TEST 10 — UNAVAILABLE COUNT
# ============================================================

if contract is not None:

    check(
        "Unavailable evidence count is correct",
        contract.unavailable_count == 1,
        (
            f"unavailable_count="
            f"{contract.unavailable_count}"
        ),
    )


# ============================================================
# TEST 11 — DUPLICATE ID PROTECTION
# ============================================================

try:

    EvidenceContract(
        version="1.0",
        evidence=[
            EvidenceItem(
                evidence_id="duplicate_001",
                source="tool_a",
                category="metric",
            ),
            EvidenceItem(
                evidence_id="duplicate_001",
                source="tool_b",
                category="metric",
            ),
        ],
    )

    check(
        "Duplicate evidence IDs are rejected",
        False,
        "Duplicate evidence IDs were accepted",
    )

except ValidationError:

    check(
        "Duplicate evidence IDs are rejected",
        True,
        "Duplicate evidence IDs correctly rejected",
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

failed_checks = (
    total_checks - passed_checks
)

pass_rate = (
    passed_checks / total_checks * 100
    if total_checks
    else 0.0
)


print()
print("=" * 60)
print("DAY 11.1 — EVIDENCE CONTRACT VALIDATION")
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
        "DAY 11.1 — PASSED"
    )

    print(
        "Evidence contract is structurally validated."
    )

    sys.exit(0)

else:

    print(
        "DAY 11.1 — FAILED"
    )

    sys.exit(1)