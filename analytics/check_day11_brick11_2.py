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
    EvidenceProvenance,
    EvidenceSupportLevel,
    EvidenceType,
    InvestigationFinding,
    ProvenanceSourceType,
)


# ============================================================
# TEST HELPERS
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
# 1 — CREATE PROVENANCE
# ============================================================

try:

    provenance = EvidenceProvenance(
        source_type=ProvenanceSourceType.TOOL,
        source_name="statistical_tool",
        tool_name="StatisticalTool",
        endpoint="/ai/investigate",
        dataset="journey_dataset",
        table="journeys",
        field="journey_duration_minutes",
        retrieval_reference=(
            "statistical_tool.flagged_count"
        ),
    )

    check(
        "Provenance object can be created",
        True,
        "Structured provenance created successfully",
    )

except Exception as exc:

    check(
        "Provenance object can be created",
        False,
        str(exc),
    )

    provenance = None


# ============================================================
# 2 — SOURCE TYPE
# ============================================================

if provenance is not None:

    check(
        "Provenance source type is preserved",
        provenance.source_type
        == ProvenanceSourceType.TOOL,
        (
            "source_type="
            f"{provenance.source_type.value}"
        ),
    )


# ============================================================
# 3 — TOOL NAME
# ============================================================

if provenance is not None:

    check(
        "Tool name is preserved",
        provenance.tool_name == "StatisticalTool",
        (
            f"tool_name={provenance.tool_name}"
        ),
    )


# ============================================================
# 4 — FIELD
# ============================================================

if provenance is not None:

    check(
        "Source field is preserved",
        provenance.field
        == "journey_duration_minutes",
        (
            f"field={provenance.field}"
        ),
    )


# ============================================================
# 5 — RETRIEVAL REFERENCE
# ============================================================

if provenance is not None:

    check(
        "Retrieval reference is preserved",
        provenance.retrieval_reference
        == "statistical_tool.flagged_count",
        (
            "retrieval_reference="
            f"{provenance.retrieval_reference}"
        ),
    )


# ============================================================
# 6 — EVIDENCE WITH PROVENANCE
# ============================================================

try:

    evidence = EvidenceItem(
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
            "1015 journeys exceeded the 90-minute "
            "threshold."
        ),
        available=True,
        source_reference=(
            "statistical_tool.flagged_count"
        ),
        record_count=8000,
        confidence=1.0,
        provenance=provenance,
    )

    check(
        "Evidence accepts structured provenance",
        True,
        "EvidenceItem contains provenance",
    )

except Exception as exc:

    check(
        "Evidence accepts structured provenance",
        False,
        str(exc),
    )

    evidence = None


# ============================================================
# 7 — METRIC COPIES INTO PROVENANCE FIELD
# ============================================================

if evidence is not None:

    check(
        "Metric is propagated to provenance",
        evidence.provenance is not None
        and evidence.provenance.field
        == "journey_duration_minutes",
        (
            "provenance.field="
            f"{evidence.provenance.field}"
        ),
    )


# ============================================================
# 8 — FINDING LINKS TO EVIDENCE
# ============================================================

try:

    finding = InvestigationFinding(
        title=(
            "Journeys above 90 minutes"
        ),
        severity="HIGH",
        metric="journey_duration_minutes",
        value=1015,
        threshold=90.0,
        operator=">",
        evidence_sources=[
            "statistical_tool"
        ],
        evidence_ids=[
            "stat_001"
        ],
        detail=(
            "1015 out of 8000 journeys exceeded "
            "the threshold."
        ),
    )

    check(
        "Finding can reference evidence IDs",
        finding.evidence_ids == ["stat_001"],
        (
            f"evidence_ids={finding.evidence_ids}"
        ),
    )

except Exception as exc:

    check(
        "Finding can reference evidence IDs",
        False,
        str(exc),
    )


# ============================================================
# 9 — CONTRACT RETAINS PROVENANCE
# ============================================================

try:

    unavailable = EvidenceItem(
        evidence_id="quality_001",
        source="quality_tool",
        category="quality",
        available=False,
    )

    contract = EvidenceContract(
        version="1.0",
        evidence=[
            evidence,
            unavailable,
        ],
    )

    retained = (
        contract.evidence[0].provenance
        is not None
    )

    check(
        "EvidenceContract retains provenance",
        retained,
        "Provenance survives contract validation",
    )

except Exception as exc:

    check(
        "EvidenceContract retains provenance",
        False,
        str(exc),
    )


# ============================================================
# 10 — DUPLICATE EVIDENCE IDs STILL PROTECTED
# ============================================================

try:

    EvidenceContract(
        version="1.0",
        evidence=[
            EvidenceItem(
                evidence_id="same_id",
                source="tool_a",
                category="metric",
            ),
            EvidenceItem(
                evidence_id="same_id",
                source="tool_b",
                category="metric",
            ),
        ],
    )

    check(
        "Duplicate evidence IDs remain protected",
        False,
        "Duplicate IDs were accepted",
    )

except ValidationError:

    check(
        "Duplicate evidence IDs remain protected",
        True,
        "Duplicate IDs correctly rejected",
    )


# ============================================================
# 11 — INVALID SOURCE TYPE REJECTED
# ============================================================

try:

    EvidenceProvenance(
        source_type="INVALID_SOURCE",
        source_name="test",
    )

    check(
        "Invalid provenance type is rejected",
        False,
        "Invalid enum value was accepted",
    )

except ValidationError:

    check(
        "Invalid provenance type is rejected",
        True,
        "Invalid provenance source type rejected",
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
print("DAY 11.2 — EVIDENCE PROVENANCE VALIDATION")
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
        "DAY 11.2 — PASSED"
    )

    print(
        "Evidence provenance is structurally validated."
    )

    sys.exit(0)

else:

    print(
        "DAY 11.2 — FAILED"
    )

    sys.exit(1)