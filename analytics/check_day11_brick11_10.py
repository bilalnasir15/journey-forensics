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

from backend.ai.api import (
    ai_health,
    ai_investigate,
)

from backend.ai.schemas import (
    InvestigationRequest,
    InvestigationStage,
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
# TEST 1
# AI HEALTH
# ============================================================

health = ai_health()

check(
    "AI health endpoint remains healthy",
    (
        isinstance(
            health,
            dict,
        )
        and
        health.get("status") == "ok"
        and
        health.get("service")
        == "ai-investigation"
    ),
    str(health),
)


# ============================================================
# TEST 2
# REQUEST CREATION
# ============================================================

request = InvestigationRequest(
    question=(
        "What journeys are above 90 minutes?"
    ),
    include_explanation=False,
)

check(
    "Real investigation request is accepted",
    (
        request.question
        ==
        "What journeys are above 90 minutes?"
        and
        request.include_explanation is False
    ),
    (
        f"question={request.question}; "
        f"include_explanation="
        f"{request.include_explanation}"
    ),
)


# ============================================================
# RUN REAL API HANDLER
# ============================================================

try:

    response = ai_investigate(
        request
    )

    api_error = None

except Exception as exc:

    response = None

    api_error = exc


# ============================================================
# TEST 3
# API RESPONSE GENERATED
# ============================================================

check(
    "Real AI investigation response is generated",
    (
        response is not None
        and
        api_error is None
    ),
    (
        f"error={api_error}"
    ),
)


# ============================================================
# STOP SAFELY IF API FAILED
# ============================================================

if response is None:

    print()
    print("=" * 60)
    print(
        "DAY 11.10 — END-TO-END VALIDATION"
    )
    print("=" * 60)

    print(
        f"Total checks: {total_checks}"
    )

    print(
        f"Passed: {passed_checks}"
    )

    print(
        f"Failed: "
        f"{total_checks - passed_checks}"
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

    print(
        f"Pass rate: {pass_rate:.2f}%"
    )

    print()
    print(
        "DAY 11.10 — FAILED"
    )

    if api_error is not None:
        print(
            f"API error: {api_error}"
        )

    sys.exit(1)


# ============================================================
# TEST 4
# QUESTION PRESERVED
# ============================================================

check(
    "API preserves investigation question",
    (
        response.question
        ==
        request.question
    ),
    (
        f"question={response.question}"
    ),
)


# ============================================================
# TEST 5
# PLAN GENERATED
# ============================================================

check(
    "Planner generated an investigation plan",
    (
        response.plan is not None
        and
        response.plan.question
        ==
        request.question
        and
        len(response.plan.tools)
        > 0
    ),
    (
        f"intent={response.plan.intent}; "
        f"tools={len(response.plan.tools)}"
    ),
)


# ============================================================
# TEST 6
# TOOL RESULTS EXIST
# ============================================================

check(
    "Deterministic tool execution completed",
    (
        len(
            response.tool_results
        )
        > 0
    ),
    (
        f"tool_results="
        f"{len(response.tool_results)}"
    ),
)


# ============================================================
# TEST 7
# STRUCTURED CONTEXT EXISTS
# ============================================================

check(
    "Structured investigation context exists",
    (
        response.structured_context
        is not None
    ),
    (
        "structured_context="
        + (
            "present"
            if response.structured_context
            is not None
            else "missing"
        )
    ),
)


# ============================================================
# TEST 8
# EVIDENCE EXISTS
# ============================================================

evidence_count = 0

if response.structured_context is not None:

    evidence_count = len(
        response.structured_context.evidence
    )

check(
    "Investigation produced evidence",
    (
        evidence_count
        > 0
    ),
    (
        f"evidence_count="
        f"{evidence_count}"
    ),
)


# ============================================================
# TEST 9
# FINDINGS EXIST
# ============================================================

finding_count = 0

if response.structured_context is not None:

    finding_count = len(
        response.structured_context.findings
    )

check(
    "Investigation produced findings",
    (
        finding_count
        > 0
    ),
    (
        f"finding_count="
        f"{finding_count}"
    ),
)


# ============================================================
# FIND GROUNDED RESPONSE RESULT
# ============================================================

grounded_entry = None

for result in response.results:

    if (
        isinstance(
            result,
            dict,
        )
        and
        result.get("type")
        == "grounded_response"
    ):

        grounded_entry = result

        break


# ============================================================
# TEST 10
# GROUNDED RESPONSE EXISTS
# ============================================================

check(
    "Grounded response is included in API results",
    (
        grounded_entry is not None
    ),
    (
        "grounded_response entry="
        + (
            "found"
            if grounded_entry
            is not None
            else "missing"
        )
    ),
)


# ============================================================
# GROUNDED DATA
# ============================================================

grounded_data = {}

if grounded_entry is not None:

    grounded_data = (
        grounded_entry.get(
            "data",
            {},
        )
    )


# ============================================================
# TEST 11
# GROUNDED FLAG
# ============================================================

check(
    "API grounded response is marked grounded",
    (
        grounded_data.get(
            "grounded"
        )
        is True
    ),
    (
        f"grounded="
        f"{grounded_data.get('grounded')}"
    ),
)


# ============================================================
# TEST 12
# EVIDENCE IDS LINKED
# ============================================================

grounded_evidence_ids = (
    grounded_data.get(
        "evidence_ids",
        [],
    )
)

check(
    "Grounded response exposes evidence IDs",
    (
        isinstance(
            grounded_evidence_ids,
            list,
        )
        and
        len(
            grounded_evidence_ids
        )
        > 0
    ),
    (
        f"evidence_ids="
        f"{grounded_evidence_ids}"
    ),
)


# ============================================================
# TEST 13
# FINDINGS LINKED
# ============================================================

grounded_findings = (
    grounded_data.get(
        "finding_titles",
        [],
    )
)

check(
    "Grounded response exposes findings",
    (
        isinstance(
            grounded_findings,
            list,
        )
        and
        len(
            grounded_findings
        )
        > 0
    ),
    (
        f"finding_titles="
        f"{grounded_findings}"
    ),
)


# ============================================================
# TEST 14
# RECOMMENDATION PRESENT
# ============================================================

recommendation = (
    grounded_data.get(
        "recommendation"
    )
)

check(
    "Grounded response exposes recommendation",
    (
        isinstance(
            recommendation,
            str,
        )
        and
        bool(
            recommendation.strip()
        )
    ),
    (
        f"recommendation="
        f"{recommendation}"
    ),
)


# ============================================================
# TEST 15
# NO UNSUPPORTED CLAIMS
# ============================================================

unsupported_claims = (
    grounded_data.get(
        "unsupported_claims",
        [],
    )
)

check(
    "End-to-end response has no unsupported claims",
    (
        unsupported_claims
        == []
    ),
    (
        f"unsupported_claims="
        f"{unsupported_claims}"
    ),
)


# ============================================================
# TEST 16
# FINAL RESPONSE TEXT
# ============================================================

final_response_text = (
    grounded_data.get(
        "response",
        "",
    )
)

check(
    "Final grounded response contains text",
    (
        isinstance(
            final_response_text,
            str,
        )
        and
        bool(
            final_response_text.strip()
        )
    ),
    (
        f"response_length="
        f"{len(final_response_text)}"
    ),
)


# ============================================================
# TEST 17
# RESPONSE CONTAINS GOLDEN RESULT
# ============================================================

check(
    "Golden investigation result is preserved",
    (
        "1015"
        in final_response_text
        and
        "90.0"
        in final_response_text
    ),
    (
        "Response contains the validated "
        "90-minute / 1015-journey result."
    ),
)


# ============================================================
# TEST 18
# STAGE
# ============================================================

check(
    "API returns RESULTS_READY without LLM",
    (
        response.stage
        ==
        InvestigationStage.RESULTS_READY
    ),
    (
        f"stage="
        f"{response.stage.value}"
    ),
)


# ============================================================
# TEST 19
# NO EXPLANATION REQUESTED
# ============================================================

check(
    "LLM is not required for deterministic flow",
    (
        request.include_explanation is False
    ),
    (
        f"llm_requested="
        f"{request.include_explanation}"
    ),
)


# ============================================================
# TEST 20
# EXISTING TOOL SUMMARY
# ============================================================

summary = (
    response.model_dump(
        mode="json"
    )
)

tool_results_payload = (
    summary.get(
        "tool_results",
        [],
    )
)

check(
    "API preserves serialized tool results",
    (
        isinstance(
            tool_results_payload,
            list,
        )
        and
        len(
            tool_results_payload
        )
        > 0
    ),
    (
        f"serialized_tool_results="
        f"{len(tool_results_payload)}"
    ),
)


# ============================================================
# TEST 21
# GROUNDED RESPONSE SERIALIZATION
# ============================================================

check(
    "Grounded response survives API serialization",
    (
        isinstance(
            grounded_data,
            dict,
        )
        and
        "grounded"
        in grounded_data
        and
        "evidence_ids"
        in grounded_data
        and
        "claims"
        in grounded_data
    ),
    (
        f"grounded_keys="
        f"{list(grounded_data.keys())}"
    ),
)


# ============================================================
# TEST 22
# CLAIM STRUCTURE
# ============================================================

claims = (
    grounded_data.get(
        "claims",
        [],
    )
)

check(
    "Grounded response exposes structured claims",
    (
        isinstance(
            claims,
            list,
        )
        and
        len(
            claims
        )
        > 0
        and
        all(
            isinstance(
                claim,
                dict,
            )
            for claim
            in claims
        )
    ),
    (
        f"claim_count="
        f"{len(claims)}"
    ),
)


# ============================================================
# TEST 23
# ALL CLAIMS GROUNDED
# ============================================================

all_claims_grounded = (
    all(
        claim.get(
            "grounded"
        )
        is True
        for claim
        in claims
    )
)

check(
    "All API response claims are grounded",
    all_claims_grounded,
    (
        f"grounded_claims="
        f"{sum(1 for claim in claims if claim.get('grounded') is True)}"
    ),
)


# ============================================================
# TEST 24
# NO FABRICATED CUSTOMER ID
# ============================================================

check(
    "API response does not invent customer ID",
    (
        "C999999"
        not in final_response_text
    ),
    (
        "No fabricated customer identifier found."
    ),
)


# ============================================================
# TEST 25
# NO FABRICATED BOOKING ID
# ============================================================

check(
    "API response does not invent booking ID",
    (
        "B999999"
        not in final_response_text
    ),
    (
        "No fabricated booking identifier found."
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
    "DAY 11.10 — END-TO-END VALIDATION"
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
        "DAY 11.10 — PASSED"
    )

    print(
        "The complete evidence-grounded investigation "
        "flow works through the AI API layer."
    )

    sys.exit(0)

else:

    print(
        "DAY 11.10 — FAILED"
    )

    sys.exit(1)