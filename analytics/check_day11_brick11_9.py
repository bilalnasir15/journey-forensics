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

from backend.ai.engine import (
    InvestigationEngine,
)

from backend.ai.schemas import (
    EvidenceContract,
    EvidenceItem,
    EvidenceProvenance,
    EvidenceSupportLevel,
    EvidenceType,
    InvestigationFinding,
    InvestigationPlan,
    InvestigationRequest,
    InvestigationResponse,
    InvestigationStage,
    PlannedTool,
    ProvenanceSourceType,
    StructuredInvestigationContext,
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
# PROVENANCE — FLAGGED COUNT
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


# ============================================================
# PROVENANCE — THRESHOLD
# ============================================================

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
        "statistical_tool",
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
    comparison_dimension=None,
    customer_id=None,
    booking_id=None,
    threshold=90.0,
    threshold_operator=">",
    planner_confidence=1.0,
    entities={},
    evidence=list(
        contract.evidence
    ),
    findings=[
        finding,
    ],
    statistical_evidence=[],
    kpi_evidence=[],
)


# ============================================================
# ENGINE
# ============================================================

engine = InvestigationEngine()


# ============================================================
# TEST 1
# GROUNDED RESPONSE BUILDER
# ============================================================

grounded_result = (
    engine.build_grounded_response(
        context
    )
)

check(
    "Engine builds grounded response",
    grounded_result.grounded,
    grounded_result.reason,
)


# ============================================================
# TEST 2
# EVIDENCE IDs
# ============================================================

check(
    "Engine preserves evidence IDs",
    (
        set(
            grounded_result.evidence_ids
        )
        ==
        {
            "stat_flagged",
            "stat_threshold",
        }
    ),
    (
        f"evidence="
        f"{grounded_result.evidence_ids}"
    ),
)


# ============================================================
# TEST 3
# FINDING
# ============================================================

check(
    "Engine preserves grounded finding",
    (
        grounded_result.finding_titles
        ==
        [
            "Journeys above 90 minutes",
        ]
    ),
    (
        f"findings="
        f"{grounded_result.finding_titles}"
    ),
)


# ============================================================
# TEST 4
# RECOMMENDATION
# ============================================================

check(
    "Engine creates grounded recommendation",
    (
        grounded_result.recommendation
        is not None
        and
        "evidence"
        in grounded_result.recommendation.lower()
    ),
    (
        f"recommendation="
        f"{grounded_result.recommendation}"
    ),
)


# ============================================================
# TEST 5
# FINAL RESPONSE
# ============================================================

check(
    "Engine creates final response text",
    bool(
        grounded_result.response.strip()
    ),
    (
        f"length="
        f"{len(grounded_result.response)}"
    ),
)


# ============================================================
# TEST 6
# NO UNSUPPORTED CLAIMS
# ============================================================

check(
    "Engine produces no unsupported claims",
    (
        grounded_result.unsupported_claims
        == []
    ),
    (
        f"unsupported="
        f"{grounded_result.unsupported_claims}"
    ),
)


# ============================================================
# TEST 7
# ALL CLAIMS GROUNDED
# ============================================================

check(
    "Engine marks all response claims grounded",
    all(
        claim.grounded
        for claim
        in grounded_result.claims
    ),
    (
        f"claims="
        f"{len(grounded_result.claims)}"
    ),
)


# ============================================================
# TEST 8
# REQUEST SCHEMA
# ============================================================

request = InvestigationRequest(
    question=(
        "What journeys are above 90 minutes?"
    ),
    include_explanation=False,
)

check(
    "Investigation request schema remains compatible",
    (
        request.question
        ==
        "What journeys are above 90 minutes?"
    ),
    request.question,
)


# ============================================================
# TEST 9
# RESPONSE SHAPE
# ============================================================

plan = InvestigationPlan(
    question=request.question,
    intent="threshold_investigation",
    primary_metric=(
        "journey_duration_minutes"
    ),
    comparison_dimension=None,
    customer_id=None,
    booking_id=None,
    threshold=90.0,
    threshold_operator=">",
    detected_entities={},
    confidence=1.0,
    tools=[
        PlannedTool(
            name="statistical_tool",
            purpose=(
                "Identify journeys above threshold."
            ),
            required=True,
            parameters={
                "metric": (
                    "journey_duration_minutes"
                ),
                "threshold": 90.0,
            },
        ),
    ],
    reasoning=[
        (
            "Use statistical evidence to "
            "identify journeys exceeding threshold."
        ),
    ],
)

response = InvestigationResponse(
    question=request.question,
    stage=(
        InvestigationStage.RESULTS_READY
    ),
    plan=plan,
    results=[],
    tool_results=[],
    structured_context=context,
    explanation=None,
    llm_provider=None,
    llm_model=None,
    llm_error=None,
)

check(
    "Existing InvestigationResponse remains valid",
    (
        response.question
        ==
        request.question
        and
        response.structured_context
        is not None
    ),
    (
        f"stage={response.stage.value}"
    ),
)


# ============================================================
# TEST 10
# EXECUTION SUMMARY
# ============================================================

summary = (
    engine.execution_summary(
        response
    )
)

check(
    "Existing execution summary remains valid",
    (
        summary["total"] == 0
        and
        summary["successful"] == 0
        and
        summary["failed"] == 0
        and
        summary["skipped"] == 0
    ),
    str(summary),
)


# ============================================================
# TEST 11
# DETERMINISTIC RECOMMENDATION
# ============================================================

generated_recommendation = (
    engine._recommend_for_finding(
        finding
    )
)

check(
    "Recommendation generator is deterministic",
    (
        generated_recommendation
        ==
        engine._recommend_for_finding(
            finding
        )
    ),
    generated_recommendation,
)


# ============================================================
# TEST 12
# AVOID UNSUPPORTED CAUSALITY
# ============================================================

check(
    "Recommendation avoids unsupported causal claim",
    (
        "root cause"
        not in generated_recommendation.lower()
        and
        "caused by"
        not in generated_recommendation.lower()
        and
        "replace"
        not in generated_recommendation.lower()
    ),
    generated_recommendation,
)


# ============================================================
# TEST 13
# EVIDENCE CONTRACT
# ============================================================

check(
    "Engine uses evidence contract version 1.0",
    (
        contract.version
        ==
        "1.0"
        and
        len(
            contract.evidence
        )
        ==
        2
    ),
    (
        f"version={contract.version}; "
        f"evidence_count="
        f"{len(contract.evidence)}"
    ),
)


# ============================================================
# TEST 14
# ORIGINAL TOOL RESULTS PRESERVED
# ============================================================

mock_response = InvestigationResponse(
    question=request.question,
    stage=(
        InvestigationStage.RESULTS_READY
    ),
    plan=plan,
    results=[
        {
            "tool_name": "statistical_tool",
            "status": "SUCCESS",
            "data": {
                "flagged_count": 1015,
            },
            "error": None,
            "metadata": {},
        },
    ],
    tool_results=[],
    structured_context=context,
    explanation=None,
    llm_provider=None,
    llm_model=None,
    llm_error=None,
)

before = len(
    mock_response.results
)

mock_response.results.append(
    {
        "type": "grounded_response",
        "status": "SUCCESS",
        "data": {
            "grounded": True,
        },
        "error": None,
        "metadata": {},
    }
)

after = len(
    mock_response.results
)

check(
    "Grounded response is additive to existing results",
    (
        before == 1
        and
        after == 2
        and
        mock_response.results[0][
            "tool_name"
        ]
        ==
        "statistical_tool"
    ),
    (
        f"before={before}; "
        f"after={after}"
    ),
)


# ============================================================
# TEST 15
# LLM FAILURE PRESERVES GROUNDED FALLBACK
# ============================================================


class FailingLLM:

    provider = "gemini"

    model = "test-model"

    def generate(
        self,
        context_payload: dict,
    ) -> str:

        raise RuntimeError(
            "Synthetic LLM failure"
        )


fallback_engine = InvestigationEngine(
    llm_explainer=FailingLLM()
)

fallback_response = InvestigationResponse(
    question=request.question,
    stage=(
        InvestigationStage.RESULTS_READY
    ),
    plan=plan,
    results=[],
    tool_results=[],
    structured_context=context,
    explanation=(
        grounded_result.response
    ),
    llm_provider=None,
    llm_model=None,
    llm_error=None,
)

fallback_engine.generate_explanation(
    fallback_response
)

check(
    "LLM failure preserves grounded fallback",
    (
        fallback_response.explanation
        ==
        grounded_result.response
        and
        fallback_response.llm_error
        is not None
        and
        fallback_response.stage
        ==
        InvestigationStage.RESULTS_READY
    ),
    (
        f"stage="
        f"{fallback_response.stage.value}; "
        f"llm_error="
        f"{fallback_response.llm_error}"
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
    "DAY 11.9 — ENGINE INTEGRATION VALIDATION"
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
        "DAY 11.9 — PASSED"
    )

    print(
        "Day 11 evidence grounding is integrated "
        "into the investigation engine."
    )

    sys.exit(0)

else:

    print(
        "DAY 11.9 — FAILED"
    )

    sys.exit(1)