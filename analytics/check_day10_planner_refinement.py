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

from backend.ai.planner import (  # noqa: E402
    InvestigationPlanner,
)

from backend.ai.schemas import (  # noqa: E402
    InvestigationRequest,
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
        "DAY 10.3 — INVESTIGATION PLANNER REFINEMENT"
    )

    print("=" * 68)


    planner = InvestigationPlanner()


    # ========================================================
    # CASE 1 — CUSTOMER + PAYMENT
    # ========================================================

    print()

    print(
        "VALIDATING CUSTOMER-SPECIFIC PAYMENT QUESTION"
    )

    print(
        "-" * 40
    )


    request_1 = InvestigationRequest(
        question=(
            "Why are payment retries increasing "
            "for C004781?"
        )
    )


    plan_1 = planner.create_plan(
        request_1
    )


    tool_names_1 = [
        tool.name
        for tool
        in plan_1.tools
    ]


    check(
        "Payment intent is detected",
        plan_1.intent == "payment",
        f"Intent={plan_1.intent}",
    )


    check(
        "Customer ID is extracted",
        plan_1.customer_id == "C004781",
        f"Customer={plan_1.customer_id}",
    )


    check(
        "Retry metric is canonicalized",
        plan_1.primary_metric == "retry_count",
        f"Metric={plan_1.primary_metric}",
    )


    check(
        "Customer profile tool receives customer ID",
        any(
            tool.name ==
            "get_customer_profile"
            and tool.parameters.get(
                "customer_id"
            )
            == "C004781"
            for tool
            in plan_1.tools
        ),
        f"Tools={tool_names_1}",
    )


    check(
        "Statistical tool is selected",
        "run_statistical_analysis"
        in tool_names_1,
        f"Tools={tool_names_1}",
    )


    check(
        "Anomaly tool is selected",
        "find_anomalies"
        in tool_names_1,
        f"Tools={tool_names_1}",
    )


    # ========================================================
    # CASE 2 — BOOKING + JOURNEY
    # ========================================================

    print()

    print(
        "VALIDATING BOOKING-SPECIFIC JOURNEY QUESTION"
    )

    print(
        "-" * 40
    )


    request_2 = InvestigationRequest(
        question=(
            "Investigate booking B007998 "
            "and explain its journey."
        )
    )


    plan_2 = planner.create_plan(
        request_2
    )


    tool_names_2 = [
        tool.name
        for tool
        in plan_2.tools
    ]


    check(
        "Journey intent is detected",
        plan_2.intent == "journey",
        f"Intent={plan_2.intent}",
    )


    check(
        "Booking ID is extracted",
        plan_2.booking_id == "B007998",
        f"Booking={plan_2.booking_id}",
    )


    check(
        "Journey tool receives booking ID",
        any(
            tool.name ==
            "get_journey"
            and tool.parameters.get(
                "booking_id"
            )
            == "B007998"
            for tool
            in plan_2.tools
        ),
        f"Tools={tool_names_2}",
    )


    # ========================================================
    # CASE 3 — THRESHOLD
    # ========================================================

    print()

    print(
        "VALIDATING THRESHOLD EXTRACTION"
    )

    print(
        "-" * 40
    )


    request_3 = InvestigationRequest(
        question=(
            "What journeys are above 90 minutes?"
        )
    )


    plan_3 = planner.create_plan(
        request_3
    )


    tool_names_3 = [
        tool.name
        for tool
        in plan_3.tools
    ]


    check(
        "Journey-duration metric is detected",
        plan_3.primary_metric
        == "journey_duration_minutes",
        f"Metric={plan_3.primary_metric}",
    )


    check(
        "Threshold 90 is extracted",
        plan_3.threshold == 90.0,
        f"Threshold={plan_3.threshold}",
    )


    check(
        "Threshold operator is >= ",
        plan_3.threshold_operator == ">=",
        (
            "Operator="
            f"{plan_3.threshold_operator}"
        ),
    )


    check(
        "Anomaly investigation is planned",
        "find_anomalies"
        in tool_names_3,
        f"Tools={tool_names_3}",
    )


    # ========================================================
    # CASE 4 — COMPARISON DIMENSION
    # ========================================================

    print()

    print(
        "VALIDATING COMPARISON DIMENSION"
    )

    print(
        "-" * 40
    )


    request_4 = InvestigationRequest(
        question=(
            "Which customer segment has the "
            "highest repeat purchases?"
        )
    )


    plan_4 = planner.create_plan(
        request_4
    )


    check(
        "Repeat-purchase intent is detected",
        plan_4.intent == "repeat_purchase",
        f"Intent={plan_4.intent}",
    )


    check(
        "Repeat-purchase metric is identified",
        plan_4.primary_metric
        == "repeat_customer_rate",
        f"Metric={plan_4.primary_metric}",
    )


    check(
        "Segment comparison is detected",
        plan_4.comparison_dimension
        == "customer_segment",
        (
            "Comparison="
            f"{plan_4.comparison_dimension}"
        ),
    )


    # ========================================================
    # CASE 5 — DATA QUALITY
    # ========================================================

    print()

    print(
        "VALIDATING DATA QUALITY QUESTION"
    )

    print(
        "-" * 40
    )


    request_5 = InvestigationRequest(
        question=(
            "What data quality issues do we have?"
        )
    )


    plan_5 = planner.create_plan(
        request_5
    )


    quality_tools = [
        tool.name
        for tool
        in plan_5.tools
    ]


    check(
        "Data-quality intent is detected",
        plan_5.intent == "data_quality",
        f"Intent={plan_5.intent}",
    )


    check(
        "Data-quality tool is selected",
        "get_data_quality"
        in quality_tools,
        f"Tools={quality_tools}",
    )


    # ========================================================
    # CASE 6 — ENTITY COLLECTION
    # ========================================================

    print()

    print(
        "VALIDATING ENTITY COLLECTION"
    )

    print(
        "-" * 40
    )


    request_6 = InvestigationRequest(
        question=(
            "Why are retry counts above 2 "
            "for booking B007998 and customer C004781?"
        )
    )


    plan_6 = planner.create_plan(
        request_6
    )


    check(
        "Customer ID is preserved",
        plan_6.customer_id == "C004781",
        f"Customer={plan_6.customer_id}",
    )


    check(
        "Booking ID is preserved",
        plan_6.booking_id == "B007998",
        f"Booking={plan_6.booking_id}",
    )


    check(
        "Retry metric is preserved",
        plan_6.primary_metric == "retry_count",
        f"Metric={plan_6.primary_metric}",
    )


    check(
        "Threshold 2 is extracted",
        plan_6.threshold == 2.0,
        f"Threshold={plan_6.threshold}",
    )


    check(
        "Detected entities are structured",
        (
            plan_6.detected_entities.get(
                "customer_id"
            )
            == "C004781"
            and
            plan_6.detected_entities.get(
                "booking_id"
            )
            == "B007998"
            and
            plan_6.detected_entities.get(
                "metric"
            )
            == "retry_count"
            and
            plan_6.detected_entities.get(
                "threshold"
            )
            == "2.0"
        ),
        (
            "Entities="
            f"{plan_6.detected_entities}"
        ),
    )


    # ========================================================
    # CONFIDENCE
    # ========================================================

    check(
        "Planner confidence is bounded",
        0.0 <= plan_6.confidence <= 1.0,
        (
            "Confidence="
            f"{plan_6.confidence}"
        ),
    )


    # ========================================================
    # REASONING
    # ========================================================

    check(
        "Planner reasoning is populated",
        len(
            plan_6.reasoning
        ) >= 4,
        (
            "Reasoning items="
            f"{len(plan_6.reasoning)}"
        ),
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()

    print("=" * 68)

    print(
        "DAY 10.3 PLANNER REFINEMENT SUMMARY"
    )

    print("=" * 68)


    failed_checks = (
        total_checks -
        passed_checks
    )


    pass_rate = (
        passed_checks /
        total_checks *
        100
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


    if passed_checks == total_checks:

        print(
            "DAY 10 BRICK 10.3 — PASSED"
        )

        print()

        print(
            "The refined investigation planner now "
            "extracts customer IDs, booking IDs, metrics, "
            "thresholds, comparison dimensions, structured "
            "entities and planning confidence."
        )

    else:

        print(
            "DAY 10 BRICK 10.3 — FAILED"
        )

        raise SystemExit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()