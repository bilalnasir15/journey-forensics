from __future__ import annotations

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

from backend.ai.engine import InvestigationEngine
from backend.ai.schemas import (
    InvestigationRequest,
    InvestigationStage,
)


# ============================================================
# VALIDATION COUNTERS
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
        "DAY 10.1 — AI INVESTIGATION ARCHITECTURE VALIDATION"
    )

    print("=" * 68)

    # ========================================================
    # ENGINE
    # ========================================================

    print()

    print(
        "VALIDATING AI ARCHITECTURE"
    )

    print(
        "-" * 40
    )

    try:

        engine = InvestigationEngine()

        check(
            "Investigation engine initializes",
            True,
            "Planner and orchestration layer initialized.",
        )

    except Exception as exc:

        check(
            "Investigation engine initializes",
            False,
            (
                f"{type(exc).__name__}: "
                f"{exc}"
            ),
        )

        return

    # ========================================================
    # REPEAT PURCHASE QUESTION
    # ========================================================

    question = (
        "Why are repeat purchases falling?"
    )

    request = InvestigationRequest(
        question=question
    )

    check(
        "Investigation request validates",
        request.question == question,
        "Natural-language question accepted.",
    )

    # ========================================================
    # CREATE PLAN
    # ========================================================

    response = engine.create_investigation(
        request
    )

    check(
        "Investigation stage is PLANNED",
        response.stage == InvestigationStage.PLANNED,
        (
            "Stage="
            f"{response.stage.value}"
        ),
    )

    check(
        "Plan preserves user question",
        response.plan.question == question,
        (
            "Question="
            f"{response.plan.question}"
        ),
    )

    check(
        "Planner identifies repeat-purchase intent",
        response.plan.intent == "repeat_purchase",
        (
            "Intent="
            f"{response.plan.intent}"
        ),
    )

    check(
        "Planner identifies repeat-purchase metric",
        response.plan.primary_metric
        == "repeat_customer_rate",
        (
            "Metric="
            f"{response.plan.primary_metric}"
        ),
    )

    # ========================================================
    # TOOL PLAN
    # ========================================================

    tool_names = [
        tool.name
        for tool in response.plan.tools
    ]

    check(
        "Plan contains KPI tool",
        "get_kpi" in tool_names,
        (
            "Tools="
            f"{tool_names}"
        ),
    )

    check(
        "Plan contains statistical tool",
        "run_statistical_analysis" in tool_names,
        (
            "Tools="
            f"{tool_names}"
        ),
    )

    # ========================================================
    # DAY 10.1 BOUNDARY
    # ========================================================

    check(
        "LLM explanation is not generated yet",
        response.explanation is None,
        (
            "Explanation remains empty "
            "by design for Day 10.1."
        ),
    )

    check(
        "Tool results are empty before execution",
        response.results == [],
        "No tools have been executed yet.",
    )

    # ========================================================
    # PAYMENT QUESTION
    # ========================================================

    payment_question = (
        "Why are payment retries increasing?"
    )

    payment_request = InvestigationRequest(
        question=payment_question
    )

    payment_response = (
        engine.create_investigation(
            payment_request
        )
    )

    payment_tools = [
        tool.name
        for tool in payment_response.plan.tools
    ]

    check(
        "Payment question receives payment investigation plan",
        payment_response.plan.intent == "payment",
        (
            "Intent="
            f"{payment_response.plan.intent}"
        ),
    )

    check(
        "Payment plan includes journey tool",
        "get_journey" in payment_tools,
        (
            "Tools="
            f"{payment_tools}"
        ),
    )

    check(
        "Payment plan includes statistical tool",
        "run_statistical_analysis" in payment_tools,
        (
            "Tools="
            f"{payment_tools}"
        ),
    )

    # ========================================================
    # STRUCTURED OUTPUT
    # ========================================================

    serialized = response.model_dump()

    check(
        "Structured investigation output serializes",
        isinstance(
            serialized,
            dict,
        ),
        "Pydantic response serialized successfully.",
    )

    check(
        "Structured plan contains reasoning",
        isinstance(
            response.plan.reasoning,
            list,
        )
        and len(
            response.plan.reasoning
        ) > 0,
        (
            "Reasoning items="
            f"{len(response.plan.reasoning)}"
        ),
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()

    print("=" * 68)

    print(
        "DAY 10.1 ARCHITECTURE SUMMARY"
    )

    print("=" * 68)

    failed_checks = (
        total_checks -
        passed_checks
    )

    if total_checks > 0:
        pass_rate = (
            passed_checks /
            total_checks *
            100
        )
    else:
        pass_rate = 0.0

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

    if passed_checks == total_checks:

        print(
            "DAY 10 BRICK 10.1 — PASSED"
        )

        print()

        print(
            "The AI investigation architecture, "
            "structured request/plan models, "
            "deterministic planning layer and "
            "orchestration contract are working correctly."
        )

    else:

        print(
            "DAY 10 BRICK 10.1 — FAILED"
        )

        raise SystemExit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()