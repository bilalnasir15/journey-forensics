from __future__ import annotations

import sys
from pathlib import Path


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

from backend.ai.grounded_findings import (
    GroundedFindingValidator,
    grounded_finding_result_to_dict,
    grounded_findings_summary_to_dict,
)

from backend.ai.schemas import (
    EvidenceContract,
    EvidenceItem,
    EvidenceProvenance,
    EvidenceSupportLevel,
    EvidenceType,
    InvestigationFinding,
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
# PROVENANCE
# ============================================================

statistical_provenance = EvidenceProvenance(
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
# EVIDENCE CONTRACT
# ============================================================

evidence_contract = EvidenceContract(
    version="1.0",
    evidence=[
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
                "Investigation threshold is "
                "90 minutes."
            ),
            available=True,
            source_reference=(
                "statistical_tool.threshold"
            ),
            record_count=8000,
            confidence=1.0,
            provenance=statistical_provenance,
        ),
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
                "Flagged journey rate is 12.69%."
            ),
            available=True,
            source_reference=(
                "statistical_tool.flagged_rate"
            ),
            record_count=8000,
            confidence=1.0,
            provenance=statistical_provenance,
        ),
        EvidenceItem(
            evidence_id="customer_record",
            source="customer_profile_tool",
            category="profile",
            evidence_type=(
                EvidenceType.PROFILE
            ),
            support_level=(
                EvidenceSupportLevel.DIRECT
            ),
            metric="customer_id",
            value="C004781",
            unit=None,
            detail=(
                "Customer C004781 exists."
            ),
            available=True,
            source_reference=(
                "customer_profile.customer_id"
            ),
            confidence=1.0,
        ),
        EvidenceItem(
            evidence_id="unavailable_complaints",
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
        ),
    ],
)


# ============================================================
# VALIDATOR
# ============================================================

validator = GroundedFindingValidator()


# ============================================================
# TEST 1
# FULLY GROUNDED FINDING
# ============================================================

grounded_finding = InvestigationFinding(
    title=(
        "Journeys above 90 minutes"
    ),
    severity="HIGH",
    metric="flagged_count",
    value=1015,
    threshold=90.0,
    operator=">",
    evidence_sources=[
        "statistical_tool"
    ],
    evidence_ids=[
        "stat_flagged",
        "stat_threshold",
    ],
    detail=(
        "1015 journeys exceeded "
        "the 90-minute threshold."
    ),
)

result = validator.validate(
    grounded_finding,
    evidence_contract,
)

check(
    "Fully supported finding is grounded",
    result.grounded,
    result.reason,
)


# ============================================================
# TEST 2
# MATCHED EVIDENCE IDS
# ============================================================

check(
    "Grounded finding retains evidence IDs",
    (
        result.matched_evidence_ids
        == [
            "stat_flagged",
            "stat_threshold",
        ]
    ),
    (
        "matched="
        f"{result.matched_evidence_ids}"
    ),
)


# ============================================================
# TEST 3
# NO MISSING IDS
# ============================================================

check(
    "Grounded finding has no missing evidence",
    not result.missing_evidence_ids,
    (
        f"missing="
        f"{result.missing_evidence_ids}"
    ),
)


# ============================================================
# TEST 4
# NO UNAVAILABLE IDS
# ============================================================

check(
    "Grounded finding has no unavailable evidence",
    not result.unavailable_evidence_ids,
    (
        "unavailable="
        f"{result.unavailable_evidence_ids}"
    ),
)


# ============================================================
# TEST 5
# MISSING EVIDENCE ID
# ============================================================

missing_finding = InvestigationFinding(
    title=(
        "Unsupported journey finding"
    ),
    severity="HIGH",
    metric="flagged_count",
    value=1015,
    evidence_sources=[
        "statistical_tool"
    ],
    evidence_ids=[
        "stat_flagged",
        "fake_evidence_999",
    ],
    detail=(
        "Finding includes an invalid evidence reference."
    ),
)

result = validator.validate(
    missing_finding,
    evidence_contract,
)

check(
    "Missing evidence reference is rejected",
    not result.grounded
    and
    "fake_evidence_999"
    in result.missing_evidence_ids,
    (
        "missing="
        f"{result.missing_evidence_ids}"
    ),
)


# ============================================================
# TEST 6
# NO EVIDENCE IDS
# ============================================================

no_evidence_finding = InvestigationFinding(
    title=(
        "Ungrounded finding"
    ),
    severity="MEDIUM",
    metric="flagged_count",
    value=1015,
    evidence_sources=[
        "statistical_tool"
    ],
    evidence_ids=[],
    detail=(
        "Finding has no evidence links."
    ),
)

result = validator.validate(
    no_evidence_finding,
    evidence_contract,
)

check(
    "Finding without evidence IDs is rejected",
    not result.grounded,
    result.reason,
)


# ============================================================
# TEST 7
# UNAVAILABLE EVIDENCE
# ============================================================

unavailable_finding = InvestigationFinding(
    title=(
        "Complaint root cause"
    ),
    severity="MEDIUM",
    metric="complaints",
    value=None,
    evidence_sources=[
        "complaint_tool"
    ],
    evidence_ids=[
        "unavailable_complaints"
    ],
    detail=(
        "Complaint evidence was requested but "
        "is currently unavailable."
    ),
)

result = validator.validate(
    unavailable_finding,
    evidence_contract,
)

check(
    "Unavailable evidence cannot ground a finding",
    (
        not result.grounded
        and
        "unavailable_complaints"
        in result.unavailable_evidence_ids
    ),
    (
        "unavailable="
        f"{result.unavailable_evidence_ids}"
    ),
)


# ============================================================
# TEST 8
# METRIC MISMATCH
# ============================================================

metric_mismatch_finding = InvestigationFinding(
    title=(
        "Customer profile issue"
    ),
    severity="LOW",
    metric="customer_id",
    value="C004781",
    evidence_sources=[
        "statistical_tool"
    ],
    evidence_ids=[
        "stat_flagged"
    ],
    detail=(
        "This finding incorrectly references "
        "a statistical count for a customer metric."
    ),
)

result = validator.validate(
    metric_mismatch_finding,
    evidence_contract,
)

check(
    "Metric mismatch is rejected",
    (
        not result.grounded
        and
        len(result.metric_mismatches) > 0
    ),
    (
        f"mismatches="
        f"{result.metric_mismatches}"
    ),
)


# ============================================================
# TEST 9
# CUSTOMER FINDING WITH CUSTOMER EVIDENCE
# ============================================================

customer_finding = InvestigationFinding(
    title=(
        "Customer evidence"
    ),
    severity="INFO",
    metric="customer_id",
    value="C004781",
    evidence_sources=[
        "customer_profile_tool"
    ],
    evidence_ids=[
        "customer_record"
    ],
    detail=(
        "Customer C004781 is present in "
        "the available profile evidence."
    ),
)

result = validator.validate(
    customer_finding,
    evidence_contract,
)

check(
    "Customer finding is grounded",
    result.grounded,
    result.reason,
)


# ============================================================
# TEST 10
# MULTIPLE FINDINGS
# ============================================================

findings = [
    grounded_finding,
    customer_finding,
]

summary = validator.validate_all(
    findings,
    evidence_contract,
)

check(
    "Multiple grounded findings pass",
    (
        summary.grounded
        and
        summary.total_findings == 2
        and
        summary.grounded_findings == 2
        and
        summary.ungrounded_findings == 0
    ),
    (
        f"total={summary.total_findings}; "
        f"grounded={summary.grounded_findings}; "
        f"ungrounded={summary.ungrounded_findings}"
    ),
)


# ============================================================
# TEST 11
# MIXED FINDINGS
# ============================================================

mixed_findings = [
    grounded_finding,
    missing_finding,
]

summary = validator.validate_all(
    mixed_findings,
    evidence_contract,
)

check(
    "Mixed grounded and ungrounded findings are detected",
    (
        not summary.grounded
        and
        summary.total_findings == 2
        and
        summary.grounded_findings == 1
        and
        summary.ungrounded_findings == 1
    ),
    (
        f"total={summary.total_findings}; "
        f"grounded={summary.grounded_findings}; "
        f"ungrounded={summary.ungrounded_findings}"
    ),
)


# ============================================================
# TEST 12
# RESULT SERIALIZATION
# ============================================================

single_dict = (
    grounded_finding_result_to_dict(
        validator.validate(
            grounded_finding,
            evidence_contract,
        )
    )
)

check(
    "Single grounding result is serializable",
    (
        isinstance(
            single_dict,
            dict,
        )
        and
        "grounded"
        in single_dict
        and
        "evidence_ids"
        in single_dict
        and
        "matched_evidence_ids"
        in single_dict
    ),
    (
        f"keys="
        f"{list(single_dict.keys())}"
    ),
)


# ============================================================
# TEST 13
# SUMMARY SERIALIZATION
# ============================================================

summary_dict = (
    grounded_findings_summary_to_dict(
        summary
    )
)

check(
    "Grounding summary is serializable",
    (
        isinstance(
            summary_dict,
            dict,
        )
        and
        "grounded"
        in summary_dict
        and
        "results"
        in summary_dict
        and
        "grounded_findings"
        in summary_dict
    ),
    (
        f"keys="
        f"{list(summary_dict.keys())}"
    ),
)


# ============================================================
# TEST 14
# EVIDENCE ID ORDER IS PRESERVED
# ============================================================

ordered_finding = InvestigationFinding(
    title=(
        "Evidence order test"
    ),
    severity="INFO",
    metric="flagged_count",
    value=1015,
    evidence_sources=[
        "statistical_tool"
    ],
    evidence_ids=[
        "stat_threshold",
        "stat_flagged",
    ],
    detail=(
        "Finding references evidence in a defined order."
    ),
)

result = validator.validate(
    ordered_finding,
    evidence_contract,
)

check(
    "Evidence ID references remain traceable",
    (
        result.evidence_ids
        == [
            "stat_threshold",
            "stat_flagged",
        ]
    ),
    (
        f"evidence_ids="
        f"{result.evidence_ids}"
    ),
)


# ============================================================
# TEST 15
# DUPLICATE EVIDENCE IDs ARE NORMALIZED
# ============================================================

duplicate_reference_finding = InvestigationFinding(
    title=(
        "Duplicate evidence reference test"
    ),
    severity="INFO",
    metric="flagged_count",
    value=1015,
    evidence_sources=[
        "statistical_tool"
    ],
    evidence_ids=[
        "stat_flagged",
        "stat_flagged",
        "stat_threshold",
    ],
    detail=(
        "Duplicate evidence references should "
        "not create duplicate matching records."
    ),
)

result = validator.validate(
    duplicate_reference_finding,
    evidence_contract,
)

check(
    "Duplicate finding evidence IDs are normalized",
    (
        result.evidence_ids
        == [
            "stat_flagged",
            "stat_threshold",
        ]
        and
        result.grounded
    ),
    (
        f"evidence_ids="
        f"{result.evidence_ids}"
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
    "DAY 11.5 — GROUNDED FINDINGS VALIDATION"
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
        "DAY 11.5 — PASSED"
    )

    print(
        "Investigation findings are deterministically "
        "grounded against the evidence contract."
    )

    sys.exit(0)

else:

    print(
        "DAY 11.5 — FAILED"
    )

    sys.exit(1)