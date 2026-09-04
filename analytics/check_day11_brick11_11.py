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

from backend.ai.grounded_explanation import (
    GroundedExplanationGuard,
    validate_grounded_explanation,
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

flagged_provenance = EvidenceProvenance(
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


threshold_provenance = EvidenceProvenance(
    source_type=(
        ProvenanceSourceType.TOOL
    ),
    source_name="statistical_tool",
    tool_name="StatisticalTool",
    endpoint="/ai/investigate",
    dataset="journeys",
    table="journeys",
    field="threshold",
    retrieval_reference=(
        "statistical_tool.threshold"
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
            provenance=flagged_provenance,
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
            provenance=threshold_provenance,
        ),
    ],
)


# ============================================================
# GUARD
# ============================================================

guard = GroundedExplanationGuard()


# ============================================================
# TEST 1
# VALID STRUCTURED EXPLANATION
# ============================================================

valid_explanation = """
Finding:
1015 journeys exceeded the 90-minute threshold.

Evidence:
The statistical investigation evaluated 8000 records,
with 1015 records meeting or exceeding the 90-minute
threshold.

Interpretation:
The evidence shows that the investigated journeys include
a measurable set that exceeded the selected duration threshold.

Next investigation:
Review the flagged journeys and associated journey
characteristics to identify relevant patterns.
""".strip()


valid_result = guard.validate(
    explanation=valid_explanation,
    evidence_contract=contract,
)


check(
    "Grounded explanation is accepted",
    valid_result.accepted,
    valid_result.reason,
)


# ============================================================
# TEST 2
# HALLUCINATION
# ============================================================

check(
    "Valid explanation passes hallucination guard",
    valid_result.hallucination_valid,
    (
        f"hallucination_valid="
        f"{valid_result.hallucination_valid}"
    ),
)


# ============================================================
# TEST 3
# UNSUPPORTED CLAIMS
# ============================================================

check(
    "Valid explanation has no unsupported claims",
    (
        valid_result.unsupported_claims
        == []
    ),
    (
        f"unsupported="
        f"{valid_result.unsupported_claims}"
    ),
)


# ============================================================
# TEST 4
# FALLBACK
# ============================================================

check(
    "Valid explanation does not trigger fallback",
    (
        valid_result.fallback_used
        is False
    ),
    (
        f"fallback="
        f"{valid_result.fallback_used}"
    ),
)


# ============================================================
# TEST 5
# EVIDENCE IDS
# ============================================================

check(
    "Validated explanation exposes evidence IDs",
    (
        set(
            valid_result.evidence_ids
        )
        ==
        {
            "stat_flagged",
            "stat_threshold",
        }
    ),
    (
        f"evidence_ids="
        f"{valid_result.evidence_ids}"
    ),
)


# ============================================================
# TEST 6
# UNSUPPORTED NUMBER
# ============================================================

bad_number_explanation = """
Finding:
1200 journeys exceeded the threshold.

Evidence:
The analysis found 1200 affected journeys.

Interpretation:
This indicates a large operational issue.

Next investigation:
Review the affected population.
""".strip()


bad_number_result = guard.validate(
    explanation=bad_number_explanation,
    evidence_contract=contract,
)


check(
    "Unsupported numeric claim is rejected",
    (
        not bad_number_result.accepted
        and
        bad_number_result.fallback_used
    ),
    (
        f"accepted="
        f"{bad_number_result.accepted}; "
        f"fallback="
        f"{bad_number_result.fallback_used}; "
        f"unsupported="
        f"{bad_number_result.unsupported_claims}"
    ),
)


# ============================================================
# TEST 7
# UNSUPPORTED CUSTOMER
# ============================================================

bad_customer_explanation = """
Finding:
Customer C999999 experienced unusually long journeys.

Evidence:
The customer was responsible for the issue.

Interpretation:
The customer requires intervention.

Next investigation:
Review the customer account.
""".strip()


bad_customer_result = guard.validate(
    explanation=bad_customer_explanation,
    evidence_contract=contract,
)


check(
    "Unsupported customer identifier is rejected",
    (
        not bad_customer_result.accepted
        and
        bad_customer_result.fallback_used
    ),
    (
        f"accepted="
        f"{bad_customer_result.accepted}; "
        f"fallback="
        f"{bad_customer_result.fallback_used}"
    ),
)


# ============================================================
# TEST 8
# UNSUPPORTED PERCENTAGE
# ============================================================

bad_percentage_explanation = """
Finding:
17.42% of journeys exceeded the threshold.

Evidence:
The supplied evidence does not contain that percentage.

Interpretation:
This indicates significant operational risk.

Next investigation:
Investigate the affected journeys.
""".strip()


bad_percentage_result = guard.validate(
    explanation=bad_percentage_explanation,
    evidence_contract=contract,
)


check(
    "Unsupported percentage is rejected",
    (
        not bad_percentage_result.accepted
        and
        bad_percentage_result.fallback_used
    ),
    (
        f"accepted="
        f"{bad_percentage_result.accepted}; "
        f"fallback="
        f"{bad_percentage_result.fallback_used}"
    ),
)


# ============================================================
# TEST 9
# EMPTY
# ============================================================

empty_result = guard.validate(
    explanation="",
    evidence_contract=contract,
)


check(
    "Empty explanation is rejected",
    (
        not empty_result.accepted
        and
        empty_result.fallback_used
    ),
    (
        f"accepted="
        f"{empty_result.accepted}; "
        f"fallback="
        f"{empty_result.fallback_used}; "
        f"unsupported="
        f"{empty_result.unsupported_claims}"
    ),
)


# ============================================================
# TEST 10
# DETERMINISTIC SUMMARY
# ============================================================

deterministic_text = (
    "The investigation evaluated 8000 records "
    "and identified 1015 journeys meeting or "
    "exceeding the 90-minute threshold."
)


deterministic_result = guard.validate(
    explanation=deterministic_text,
    evidence_contract=contract,
)


check(
    "Deterministic evidence summary is accepted",
    deterministic_result.accepted,
    deterministic_result.reason,
)


# ============================================================
# TEST 11
# THRESHOLD
# ============================================================

threshold_result = guard.validate(
    explanation=(
        "The threshold used in the investigation "
        "was 90 minutes."
    ),
    evidence_contract=contract,
)


check(
    "Supported threshold is accepted",
    threshold_result.accepted,
    threshold_result.reason,
)


# ============================================================
# TEST 12
# STRUCTURED RESULT
# ============================================================

check(
    "Result exposes structured grounding fields",
    (
        hasattr(
            threshold_result,
            "explanation",
        )
        and
        hasattr(
            threshold_result,
            "accepted",
        )
        and
        hasattr(
            threshold_result,
            "hallucination_valid",
        )
        and
        hasattr(
            threshold_result,
            "fallback_used",
        )
        and
        hasattr(
            threshold_result,
            "reason",
        )
    ),
    "Structured result contract is available.",
)


# ============================================================
# TEST 13
# CONVENIENCE FUNCTION
# ============================================================

function_result = (
    validate_grounded_explanation(
        explanation=deterministic_text,
        evidence_contract=contract,
    )
)


check(
    "Convenience validation function works",
    function_result.accepted,
    function_result.reason,
)


# ============================================================
# TEST 14
# ACCEPTED TEXT PRESERVED
# ============================================================

check(
    "Accepted explanation text is preserved",
    (
        deterministic_result.explanation
        ==
        deterministic_text
    ),
    (
        f"length="
        f"{len(deterministic_result.explanation)}"
    ),
)


# ============================================================
# TEST 15
# REJECTION CONTRACT
# ============================================================

check(
    "Rejected explanation cannot be marked accepted",
    (
        not bad_number_result.accepted
        and
        not bad_number_result.hallucination_valid
    ),
    (
        f"accepted="
        f"{bad_number_result.accepted}; "
        f"hallucination_valid="
        f"{bad_number_result.hallucination_valid}"
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
    "DAY 11.11 — GROUNDED GEMINI EXPLANATION GUARD VALIDATION"
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
        "DAY 11.11 — PASSED"
    )

    print(
        "LLM explanations are accepted only when "
        "their factual claims are grounded in evidence."
    )

    sys.exit(0)

else:

    print(
        "DAY 11.11 — FAILED"
    )

    sys.exit(1)