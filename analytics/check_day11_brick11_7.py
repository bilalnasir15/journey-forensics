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

from backend.ai.grounded_recommendations import (
    GroundedRecommendationValidator,
    grounded_recommendation_result_to_dict,
    grounded_recommendation_summary_to_dict,
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
# COUNTERS
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

provenance = EvidenceProvenance(
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

contract = EvidenceContract(
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
                "1015 journeys exceeded "
                "the 90-minute threshold."
            ),
            available=True,
            source_reference=(
                "statistical_tool.flagged_count"
            ),
            record_count=8000,
            confidence=1.0,
            provenance=provenance,
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
                "Investigation threshold "
                "is 90 minutes."
            ),
            available=True,
            source_reference=(
                "statistical_tool.threshold"
            ),
            record_count=8000,
            confidence=1.0,
            provenance=provenance,
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
                "Flagged journey rate "
                "is 12.69%."
            ),
            available=True,
            source_reference=(
                "statistical_tool.flagged_rate"
            ),
            record_count=8000,
            confidence=1.0,
            provenance=provenance,
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
            detail=(
                "Customer C004781 exists."
            ),
            available=True,
            source_reference=(
                "customer_profile.customer_id"
            ),
            confidence=1.0,
        ),
    ],
)


# ============================================================
# VALIDATOR
# ============================================================

validator = (
    GroundedRecommendationValidator()
)


# ============================================================
# VALID FINDING
# ============================================================

finding = InvestigationFinding(
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


# ============================================================
# TEST 1
# GROUNDED RECOMMENDATION
# ============================================================

recommendation = (
    "Break down the 1015 flagged journeys "
    "above the 90-minute threshold to identify "
    "the main drivers."
)

result = validator.validate(
    finding,
    recommendation,
    contract,
)

check(
    "Evidence-grounded recommendation passes",
    result.grounded,
    result.reason,
)


# ============================================================
# TEST 2
# EVIDENCE IDS RETAINED
# ============================================================

check(
    "Recommendation retains finding evidence IDs",
    (
        result.finding_evidence_ids
        ==
        [
            "stat_flagged",
            "stat_threshold",
        ]
    ),
    (
        f"evidence_ids="
        f"{result.finding_evidence_ids}"
    ),
)


# ============================================================
# TEST 3
# MATCHED EVIDENCE EXISTS
# ============================================================

check(
    "Recommendation resolves evidence",
    (
        set(
            result.matched_evidence_ids
        )
        ==
        {
            "stat_flagged",
            "stat_threshold",
        }
    ),
    (
        f"matched="
        f"{result.matched_evidence_ids}"
    ),
)


# ============================================================
# TEST 4
# UNSUPPORTED NUMBER
# ============================================================

bad_number_recommendation = (
    "Immediately investigate 1200 journeys "
    "as the primary source of operational loss."
)

result = validator.validate(
    finding,
    bad_number_recommendation,
    contract,
)

check(
    "Unsupported numeric recommendation is rejected",
    not result.grounded,
    (
        f"unsupported="
        f"{result.unsupported_references}"
    ),
)


# ============================================================
# TEST 5
# UNSUPPORTED CUSTOMER
# ============================================================

bad_customer_recommendation = (
    "Prioritize customer C999999 because "
    "this customer drove the long journeys."
)

result = validator.validate(
    finding,
    bad_customer_recommendation,
    contract,
)

check(
    "Unsupported identifier recommendation is rejected",
    not result.grounded,
    (
        f"unsupported="
        f"{result.unsupported_references}"
    ),
)


# ============================================================
# TEST 6
# EMPTY RECOMMENDATION
# ============================================================

result = validator.validate(
    finding,
    "",
    contract,
)

check(
    "Empty recommendation is rejected",
    not result.grounded,
    result.reason,
)


# ============================================================
# TEST 7
# UNGROUNDED FINDING
# ============================================================

ungrounded_finding = InvestigationFinding(
    title=(
        "Payment root cause"
    ),
    severity="HIGH",
    metric="payment_failure",
    value=None,
    evidence_sources=[
        "payment_tool"
    ],
    evidence_ids=[],
    detail=(
        "No payment evidence is available."
    ),
)

result = validator.validate(
    ungrounded_finding,
    (
        "Replace the payment provider "
        "immediately."
    ),
    contract,
)

check(
    "Recommendation for ungrounded finding is rejected",
    not result.grounded,
    result.reason,
)


# ============================================================
# TEST 8
# MISSING EVIDENCE REFERENCE
# ============================================================

missing_evidence_finding = (
    InvestigationFinding(
        title=(
            "Invalid evidence finding"
        ),
        severity="HIGH",
        metric="flagged_count",
        value=1015,
        evidence_sources=[
            "statistical_tool"
        ],
        evidence_ids=[
            "fake_evidence_999"
        ],
        detail=(
            "Finding contains an invalid "
            "evidence reference."
        ),
    )
)

result = validator.validate(
    missing_evidence_finding,
    (
        "Review the flagged journey population."
    ),
    contract,
)

check(
    "Recommendation with missing evidence is rejected",
    not result.grounded,
    (
        f"unsupported="
        f"{result.unsupported_references}"
    ),
)


# ============================================================
# TEST 9
# CUSTOMER-SPECIFIC GROUNDED RECOMMENDATION
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
        "Customer C004781 exists."
    ),
)

result = validator.validate(
    customer_finding,
    (
        "Review customer C004781's available "
        "journey history for related signals."
    ),
    contract,
)

check(
    "Supported customer recommendation passes",
    result.grounded,
    result.reason,
)


# ============================================================
# TEST 10
# MULTIPLE RECOMMENDATIONS
# ============================================================

recommendation_pairs = [
    (
        finding,
        (
            "Review the 1015 flagged journeys "
            "to identify common duration drivers."
        ),
    ),
    (
        customer_finding,
        (
            "Review customer C004781's "
            "available evidence."
        ),
    ),
]

summary = validator.validate_all(
    recommendation_pairs,
    contract,
)

check(
    "Multiple grounded recommendations pass",
    (
        summary.grounded
        and
        summary.total_recommendations == 2
        and
        summary.grounded_recommendations == 2
        and
        summary.ungrounded_recommendations == 0
    ),
    (
        f"total="
        f"{summary.total_recommendations}; "
        f"grounded="
        f"{summary.grounded_recommendations}; "
        f"ungrounded="
        f"{summary.ungrounded_recommendations}"
    ),
)


# ============================================================
# TEST 11
# MIXED RECOMMENDATIONS
# ============================================================

mixed_pairs = [
    (
        finding,
        (
            "Review the 1015 flagged journeys."
        ),
    ),
    (
        finding,
        (
            "Investigate the 1200 affected journeys."
        ),
    ),
]

summary = validator.validate_all(
    mixed_pairs,
    contract,
)

check(
    "Mixed recommendations are detected",
    (
        not summary.grounded
        and
        summary.total_recommendations == 2
        and
        summary.grounded_recommendations == 1
        and
        summary.ungrounded_recommendations == 1
    ),
    (
        f"total="
        f"{summary.total_recommendations}; "
        f"grounded="
        f"{summary.grounded_recommendations}; "
        f"ungrounded="
        f"{summary.ungrounded_recommendations}"
    ),
)


# ============================================================
# TEST 12
# SERIALIZATION
# ============================================================

single_result = validator.validate(
    finding,
    recommendation,
    contract,
)

single_dict = (
    grounded_recommendation_result_to_dict(
        single_result
    )
)

check(
    "Single recommendation result is serializable",
    (
        isinstance(
            single_dict,
            dict,
        )
        and
        "grounded"
        in single_dict
        and
        "recommendation"
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
    grounded_recommendation_summary_to_dict(
        summary
    )
)

check(
    "Recommendation summary is serializable",
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
        "grounded_recommendations"
        in summary_dict
    ),
    (
        f"keys="
        f"{list(summary_dict.keys())}"
    ),
)


# ============================================================
# TEST 14
# AVAILABLE EVIDENCE IS REQUIRED
# ============================================================

unavailable_contract = EvidenceContract(
    version="1.0",
    evidence=[
        EvidenceItem(
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
    ],
)

unavailable_finding = InvestigationFinding(
    title=(
        "Complaint investigation"
    ),
    severity="MEDIUM",
    metric="complaints",
    value=None,
    evidence_sources=[
        "complaint_tool"
    ],
    evidence_ids=[
        "unavailable_001"
    ],
    detail=(
        "Complaint evidence is unavailable."
    ),
)

result = validator.validate(
    unavailable_finding,
    (
        "Review complaint trends immediately."
    ),
    unavailable_contract,
)

check(
    "Unavailable evidence cannot ground recommendation",
    not result.grounded,
    result.reason,
)


# ============================================================
# TEST 15
# NUMBER TOLERANCE
# ============================================================

tolerance_result = validator.validate(
    finding,
    (
        "Review approximately 1015 flagged journeys."
    ),
    contract,
)

check(
    "Equivalent numeric formatting is accepted",
    tolerance_result.grounded,
    tolerance_result.reason,
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
    "DAY 11.7 — GROUNDED RECOMMENDATIONS VALIDATION"
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
        "DAY 11.7 — PASSED"
    )

    print(
        "Recommendations are deterministically grounded "
        "against investigation evidence."
    )

    sys.exit(0)

else:

    print(
        "DAY 11.7 — FAILED"
    )

    sys.exit(1)