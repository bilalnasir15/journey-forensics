from __future__ import annotations

import json
import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# IMPORTS
# ============================================================

from backend.ai.engine import (  # noqa: E402
    InvestigationEngine,
)

from backend.ai.llm import (  # noqa: E402
    DeterministicTestExplainer,
)

from backend.ai.schemas import (  # noqa: E402
    InvestigationRequest,
    InvestigationStage,
    ToolExecutionStatus,
)

from backend.ai.tools import (  # noqa: E402
    ToolExecutor,
)

from backend.ai.api import (  # noqa: E402
    ApplicationTransport,
)


# ============================================================
# GOLDEN INVESTIGATION
# ============================================================

GOLDEN_QUESTION = (
    "What journeys are above 90 minutes?"
)


EXPECTED_METRIC = (
    "journey_duration_minutes"
)


EXPECTED_RECORDS = 8000


EXPECTED_THRESHOLD = 90.0


EXPECTED_FLAGGED = 1015


EXPECTED_FLAGGED_RATE = 12.69


# ============================================================
# COUNTERS
# ============================================================

total_checks = 0

passed_checks = 0


# ============================================================
# CHECK
# ============================================================

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
# MAIN
# ============================================================

def main() -> None:

    print("=" * 68)

    print(
        "DAY 10.10 — FIRST AI INVESTIGATION VALIDATION"
    )

    print("=" * 68)


    # ========================================================
    # ENGINE
    # ========================================================

    print()

    print(
        "VALIDATING GOLDEN INVESTIGATION"
    )

    print(
        "-" * 40
    )


    test_explainer = (
        DeterministicTestExplainer()
    )


    transport = (
        ApplicationTransport()
    )


    tool_executor = (
        ToolExecutor(
            transport=transport
        )
    )


    engine = InvestigationEngine(

        tool_executor=
            tool_executor,

        llm_explainer=
            test_explainer,
    )


    request = InvestigationRequest(

        question=
            GOLDEN_QUESTION,

        include_explanation=
            True,
    )


    response = (
        engine.execute_investigation(
            request
        )
    )


    # ========================================================
    # RESPONSE CONTRACT
    # ========================================================

    check(
        "Investigation question is preserved",
        response.question
        == GOLDEN_QUESTION,
        (
            "Question="
            f"{response.question}"
        ),
    )


    check(
        "Investigation reaches EXPLANATION_READY",
        response.stage
        == InvestigationStage.EXPLANATION_READY,
        (
            "Stage="
            f"{response.stage.value}"
        ),
    )


    check(
        "Investigation plan exists",
        response.plan is not None,
        "Structured investigation plan returned.",
    )


    check(
        "Structured context exists",
        response.structured_context is not None,
        "Structured context returned.",
    )


    # ========================================================
    # PLAN
    # ========================================================

    plan = response.plan


    check(
        "Planner intent is journey",
        plan.intent == "journey",
        (
            "Intent="
            f"{plan.intent}"
        ),
    )


    check(
        "Planner metric is correct",
        plan.primary_metric
        == EXPECTED_METRIC,
        (
            "Metric="
            f"{plan.primary_metric}"
        ),
    )


    check(
        "Planner threshold is correct",
        plan.threshold
        == EXPECTED_THRESHOLD,
        (
            "Threshold="
            f"{plan.threshold}"
        ),
    )


    check(
        "Planner threshold operator is correct",
        plan.threshold_operator
        == ">=",
        (
            "Operator="
            f"{plan.threshold_operator}"
        ),
    )


    # ========================================================
    # TOOL EXECUTION
    # ========================================================

    tool_results = (
        response.tool_results
    )


    successful_tools = [
        item
        for item in tool_results
        if (
            item.status
            == ToolExecutionStatus.SUCCESS
        )
    ]


    check(
        "Investigation executes tools",
        len(tool_results) > 0,
        (
            "Tools="
            f"{len(tool_results)}"
        ),
    )


    check(
        "At least one tool succeeds",
        len(successful_tools) > 0,
        (
            "Successful="
            f"{len(successful_tools)}"
        ),
    )


    executed_tool_names = {
        item.tool_name
        for item in successful_tools
    }


    check(
        "Statistical tool executes",
        "run_statistical_analysis"
        in executed_tool_names,
        (
            "Executed="
            f"{sorted(executed_tool_names)}"
        ),
    )


    check(
        "Anomaly tool executes",
        "find_anomalies"
        in executed_tool_names,
        (
            "Executed="
            f"{sorted(executed_tool_names)}"
        ),
    )


    # ========================================================
    # STRUCTURED STATISTICAL EVIDENCE
    # ========================================================

    context = (
        response.structured_context
    )


    assert context is not None


    statistical = (
        context.statistical_evidence
    )


    check(
        "Statistical evidence is available",
        len(statistical) > 0,
        (
            "Statistical evidence="
            f"{len(statistical)}"
        ),
    )


    statistic = (
        statistical[0]
        if statistical
        else None
    )


    check(
        "Statistical metric matches",
        statistic is not None
        and statistic.metric
        == EXPECTED_METRIC,
        (
            "Metric="
            f"{statistic.metric if statistic else None}"
        ),
    )


    check(
        "Record count matches golden result",
        statistic is not None
        and statistic.record_count
        == EXPECTED_RECORDS,
        (
            "Expected="
            f"{EXPECTED_RECORDS}, "
            "Actual="
            f"{statistic.record_count if statistic else None}"
        ),
    )


    check(
        "Threshold matches golden result",
        statistic is not None
        and statistic.threshold
        == EXPECTED_THRESHOLD,
        (
            "Threshold="
            f"{statistic.threshold if statistic else None}"
        ),
    )


    check(
        "Flagged count matches golden result",
        statistic is not None
        and statistic.flagged_count
        == EXPECTED_FLAGGED,
        (
            "Expected="
            f"{EXPECTED_FLAGGED}, "
            "Actual="
            f"{statistic.flagged_count if statistic else None}"
        ),
    )


    check(
        "Flagged rate matches golden result",
        statistic is not None
        and statistic.flagged_rate is not None
        and abs(
            statistic.flagged_rate
            - EXPECTED_FLAGGED_RATE
        ) < 0.01,
        (
            "Expected="
            f"{EXPECTED_FLAGGED_RATE}, "
            "Actual="
            f"{statistic.flagged_rate if statistic else None}"
        ),
    )


    # ========================================================
    # FINDINGS
    # ========================================================

    findings = (
        context.findings
    )


    check(
        "Investigation finding is generated",
        len(findings) > 0,
        (
            "Findings="
            f"{len(findings)}"
        ),
    )


    if findings:

        finding = findings[0]


        check(
            "Finding has a title",
            bool(
                finding.title
            ),
            (
                "Title="
                f"{finding.title}"
            ),
        )


        check(
            "Finding contains metric",
            finding.metric
            == EXPECTED_METRIC,
            (
                "Metric="
                f"{finding.metric}"
            ),
        )


        check(
            "Finding preserves flagged value",
            finding.value
            == EXPECTED_FLAGGED,
            (
                "Value="
                f"{finding.value}"
            ),
        )


    # ========================================================
    # EVIDENCE PROVENANCE
    # ========================================================

    evidence = (
        context.evidence
    )


    check(
        "Evidence chain is populated",
        len(evidence) > 0,
        (
            "Evidence="
            f"{len(evidence)}"
        ),
    )


    evidence_sources = {
        item.source
        for item in evidence
        if item.source
    }


    check(
        "Evidence has source identifiers",
        len(evidence_sources) > 0,
        (
            "Sources="
            f"{sorted(evidence_sources)}"
        ),
    )


    evidence_categories = {
        item.category
        for item in evidence
        if item.category
    }


    check(
        "Evidence has categories",
        len(evidence_categories) > 0,
        (
            "Categories="
            f"{sorted(evidence_categories)}"
        ),
    )


    # ========================================================
    # TOOL SUMMARY
    # ========================================================

    summary = (
        context.tool_summary
    )


    check(
        "Tool summary total reconciles",
        summary.total
        == len(tool_results),
        (
            "Summary="
            f"{summary.total}, "
            "Actual="
            f"{len(tool_results)}"
        ),
    )


    check(
        "Tool summary successful reconciles",
        summary.successful
        == len(successful_tools),
        (
            "Summary="
            f"{summary.successful}, "
            "Actual="
            f"{len(successful_tools)}"
        ),
    )


    check(
        "Tool summary status distribution reconciles",
        (
            summary.total
            ==
            (
                summary.successful
                + summary.failed
                + summary.skipped
            )
        ),
        (
            "Successful="
            f"{summary.successful}, "
            "Failed="
            f"{summary.failed}, "
            "Skipped="
            f"{summary.skipped}"
        ),
    )


    # ========================================================
    # AI EXPLANATION
    # ========================================================

    explanation = (
        response.explanation
    )


    check(
        "AI explanation is generated",
        bool(
            explanation
        ),
        (
            "Characters="
            f"{len(explanation or '')}"
        ),
    )


    check(
        "AI explanation preserves golden metric",
        EXPECTED_METRIC
        in (
            explanation
            or ""
        ),
        "Metric appears in explanation.",
    )


    check(
        "AI explanation preserves flagged count",
        str(
            EXPECTED_FLAGGED
        )
        in (
            explanation
            or ""
        ),
        "Flagged count appears in explanation.",
    )


    check(
        "AI explanation preserves record count",
        str(
            EXPECTED_RECORDS
        )
        in (
            explanation
            or ""
        ),
        "Record count appears in explanation.",
    )


    check(
        "AI explanation has Finding section",
        "Finding:"
        in (
            explanation
            or ""
        ),
        "Finding section detected.",
    )


    check(
        "AI explanation has Evidence section",
        "Evidence:"
        in (
            explanation
            or ""
        ),
        "Evidence section detected.",
    )


    check(
        "AI explanation has Interpretation section",
        "Interpretation:"
        in (
            explanation
            or ""
        ),
        "Interpretation section detected.",
    )


    check(
        "AI explanation has Next investigation section",
        "Next investigation:"
        in (
            explanation
            or ""
        ),
        "Next investigation section detected.",
    )


    # ========================================================
    # METADATA
    # ========================================================

    check(
        "LLM provider metadata is present",
        response.llm_provider
        == "deterministic-test",
        (
            "Provider="
            f"{response.llm_provider}"
        ),
    )


    check(
        "LLM model metadata is present",
        response.llm_model
        == "deterministic-test-model",
        (
            "Model="
            f"{response.llm_model}"
        ),
    )


    check(
        "LLM error is empty",
        response.llm_error is None,
        (
            "Error="
            f"{response.llm_error}"
        ),
    )


    # ========================================================
    # SERIALIZATION
    # ========================================================

    print()

    print(
        "VALIDATING FINAL SERIALIZATION"
    )

    print(
        "-" * 40
    )


    serialized = (
        response.model_dump(
            mode="json"
        )
    )


    check(
        "Full investigation response is serializable",
        isinstance(
            serialized,
            dict,
        ),
        "Response converted to JSON-compatible dictionary.",
    )


    check(
        "Serialized response contains explanation",
        bool(
            serialized.get(
                "explanation"
            )
        ),
        "Explanation present in serialized response.",
    )


    check(
        "Serialized response contains structured context",
        isinstance(
            serialized.get(
                "structured_context"
            ),
            dict,
        ),
        "Structured context preserved.",
    )


    # Confirm it can actually be JSON encoded.
    json.dumps(
        serialized,
        ensure_ascii=False,
        default=str,
    )


    check(
        "Serialized investigation is valid JSON",
        True,
        "JSON encoding completed successfully.",
    )


    # ========================================================
    # GOLDEN RESULT LOCK
    # ========================================================

    print()

    print(
        "VALIDATING GOLDEN RESULT LOCK"
    )

    print(
        "-" * 40
    )


    check(
        "Golden metric is locked",
        EXPECTED_METRIC
        == "journey_duration_minutes",
        (
            "Metric="
            f"{EXPECTED_METRIC}"
        ),
    )


    check(
        "Golden record count is locked",
        EXPECTED_RECORDS
        == 8000,
        (
            "Records="
            f"{EXPECTED_RECORDS}"
        ),
    )


    check(
        "Golden flagged count is locked",
        EXPECTED_FLAGGED
        == 1015,
        (
            "Flagged="
            f"{EXPECTED_FLAGGED}"
        ),
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()

    print("=" * 68)

    print(
        "DAY 10.10 FIRST AI INVESTIGATION SUMMARY"
    )

    print("=" * 68)


    failed_checks = (
        total_checks
        - passed_checks
    )


    pass_rate = (

        (
            passed_checks
            /
            total_checks
        )
        * 100

        if total_checks

        else 0.0
    )


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


    if (
        total_checks > 0
        and passed_checks
        == total_checks
    ):

        print(
            "DAY 10 BRICK 10.10 — PASSED"
        )

        print()

        print(
            "The first end-to-end AI investigation "
            "is validated from natural-language question "
            "through planning, deterministic tools, "
            "statistical evidence, findings, structured "
            "context and AI explanation."
        )

    else:

        print(
            "DAY 10 BRICK 10.10 — FAILED"
        )

        raise SystemExit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()