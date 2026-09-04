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

from backend.ai.grounded_response import (
    EvidenceGroundedResponseBuilder,
    grounded_response_to_dict,
)

from backend.ai.schemas import (
    EvidenceContract,
    EvidenceItem,
    EvidenceProvenance,
    EvidenceSupportLevel,
    EvidenceType,
    InvestigationFinding,
    ProvenanceSourceType,
    StructuredInvestigationContext,
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

provenance = EvidenceProvenance(
    source_type=(
        ProvenanceSourceType.TOOL
    ),
    source_name="statistical_tool",
    tool_name="StatisticalTool",
    endpoint="/ai/investigate",
    dataset="journeys",
    table="journeys",
    field="flagged_count",
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
    ],
)


# ============================================================
# FINDING
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
# CONTEXT
# ============================================================

context = StructuredInvestigationContext(
    question=(
        "What journeys are above 90 minutes?"
    ),
    intent="threshold_investigation",
    primary_metric=(
        "journey_duration_minutes"
    ),
    threshold=90.0,
    threshold_operator=">",
    planner_confidence=1.0,
    entities={},
    evidence=[
        contract.evidence[0],
        contract.evidence[1],
        contract.evidence[2],
    ],
    findings=[
        finding
    ],
)


# ============================================================
# BUILDER
# ============================================================

builder = (
    EvidenceGroundedResponseBuilder()
)


# ============================================================
# GROUNDED RECOMMENDATION
# ============================================================

recommendation = (
    "Review the 1015 flagged journeys "
    "to identify common duration drivers."
)


# ============================================================
# BUILD RESPONSE
# ============================================================

result = builder.build(
    context=context,
    evidence_contract=contract,
    findings=[
        finding
    ],
    recommendations=[
        (
            finding,
            recommendation,
        )
    ],
)


# ============================================================
# TEST 1
# RESPONSE GENERATED
# ============================================================

check(
    "Grounded response is generated",
    bool(
        result.response.strip()
    ),
    (
        f"response_length="
        f"{len(result.response)}"
    ),
)


# ============================================================
# TEST 2
# RESPONSE GROUNDED
# ============================================================

check(
    "Final response is grounded",
    result.grounded,
    result.reason,
)


# ============================================================
# TEST 3
# QUESTION RETAINED
# ============================================================

check(
    "Investigation question is retained",
    (
        result.question
        ==
        "What journeys are above 90 minutes?"
    ),
    f"question={result.question}",
)


# ============================================================
# TEST 4
# FINDING RETAINED
# ============================================================

check(
    "Finding title is retained",
    (
        result.finding_titles
        ==
        [
            "Journeys above 90 minutes"
        ]
    ),
    (
        f"findings="
        f"{result.finding_titles}"
    ),
)


# ============================================================
# TEST 5
# EVIDENCE LINKAGE
# ============================================================

check(
    "Response links finding evidence",
    (
        set(result.evidence_ids)
        ==
        {
            "stat_flagged",
            "stat_threshold",
        }
    ),
    (
        f"evidence_ids="
        f"{result.evidence_ids}"
    ),
)


# ============================================================
# TEST 6
# RECOMMENDATION RETAINED
# ============================================================

check(
    "Grounded recommendation is retained",
    (
        result.recommendation
        ==
        recommendation
    ),
    (
        f"recommendation="
        f"{result.recommendation}"
    ),
)


# ============================================================
# TEST 7
# CLAIMS CREATED
# ============================================================

check(
    "Response contains structured claims",
    (
        len(result.claims)
        >= 3
    ),
    (
        f"claim_count="
        f"{len(result.claims)}"
    ),
)


# ============================================================
# TEST 8
# CLAIMS ARE GROUNDED
# ============================================================

check(
    "All response claims are grounded",
    all(
        claim.grounded
        for claim in result.claims
    ),
    (
        f"grounded_claims="
        f"{sum(1 for c in result.claims if c.grounded)}"
    ),
)


# ============================================================
# TEST 9
# NO UNSUPPORTED CLAIMS
# ============================================================

check(
    "No unsupported claims remain",
    (
        result.unsupported_claims
        == []
    ),
    (
        f"unsupported="
        f"{result.unsupported_claims}"
    ),
)


# ============================================================
# TEST 10
# RESPONSE CONTAINS FINDING
# ============================================================

check(
    "Response contains validated finding",
    (
        "1015"
        in result.response
        and
        "90.0"
        in result.response
    ),
    (
        "Response contains grounded "
        "finding values."
    ),
)


# ============================================================
# TEST 11
# RESPONSE CONTAINS RECOMMENDATION
# ============================================================

check(
    "Response contains grounded recommendation",
    (
        recommendation
        in result.response
    ),
    (
        "Recommendation is included "
        "in the final response."
    ),
)


# ============================================================
# TEST 12
# NO FABRICATED CUSTOMER ID
# ============================================================

check(
    "Response does not invent customer identifiers",
    (
        "C999999"
        not in result.response
    ),
    (
        "No unsupported customer identifier "
        "appears in the response."
    ),
)


# ============================================================
# TEST 13
# NO FABRICATED BOOKING ID
# ============================================================

check(
    "Response does not invent booking identifiers",
    (
        "B999999"
        not in result.response
    ),
    (
        "No unsupported booking identifier "
        "appears in the response."
    ),
)


# ============================================================
# TEST 14
# SERIALIZATION
# ============================================================

serialized = (
    grounded_response_to_dict(
        result
    )
)

check(
    "Grounded response is serializable",
    (
        isinstance(
            serialized,
            dict,
        )
        and
        "response"
        in serialized
        and
        "grounded"
        in serialized
        and
        "claims"
        in serialized
        and
        "evidence_ids"
        in serialized
    ),
    (
        f"keys="
        f"{list(serialized.keys())}"
    ),
)


# ============================================================
# TEST 15
# UNGROUNDED FINDING DOES NOT PRODUCE GROUNDED CLAIM
# ============================================================

bad_finding = InvestigationFinding(
    title=(
        "Payment provider root cause"
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


bad_context = StructuredInvestigationContext(
    question=(
        "Why are payments failing?"
    ),
    intent="root_cause_investigation",
    primary_metric="payment_failure",
    planner_confidence=1.0,
    evidence=[],
    findings=[
        bad_finding
    ],
)


bad_result = builder.build(
    context=bad_context,
    evidence_contract=contract,
    findings=[
        bad_finding
    ],
    recommendations=[
        (
            bad_finding,
            "Replace the payment provider immediately.",
        )
    ],
)


check(
    "Unsupported root-cause recommendation is blocked",
    (
        not bad_result.grounded
        or
        len(
            bad_result.unsupported_claims
        )
        > 0
        or
        len(
            bad_result.finding_titles
        )
        == 0
    ),
    (
        f"grounded={bad_result.grounded}; "
        f"unsupported="
        f"{bad_result.unsupported_claims}; "
        f"findings="
        f"{bad_result.finding_titles}"
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
    /
    total_checks
    *
    100
    if total_checks
    else 0.0
)

print()
print("=" * 60)
print(
    "DAY 11.8 — EVIDENCE-GROUNDED AI RESPONSE VALIDATION"
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
        "DAY 11.8 — PASSED"
    )

    print(
        "Final AI responses are composed from "
        "grounded evidence, findings and recommendations."
    )

    sys.exit(0)

else:

    print(
        "DAY 11.8 — FAILED"
    )

    sys.exit(1)