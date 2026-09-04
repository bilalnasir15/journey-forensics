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

from fastapi.testclient import TestClient

from backend.main import app

from backend.ai.engine import (
    InvestigationEngine,
)

from backend.ai.schemas import (
    InvestigationRequest,
    InvestigationStage,
    ToolExecutionStatus,
)

from backend.ai.tools import (
    ToolExecutor,
)


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
# TRANSPORT
# ============================================================

class TestClientTransport:

    def __init__(
        self,
        client: TestClient,
    ) -> None:

        self.client = client


    def request(
        self,
        method: str,
        path: str,
        *,
        params=None,
        json_body=None,
    ):

        method = method.upper()


        if method == "GET":

            response = self.client.get(
                path,
                params=params or {},
            )

        elif method == "POST":

            response = self.client.post(
                path,
                json=json_body or {},
            )

        else:

            raise ValueError(
                (
                    "Unsupported HTTP method "
                    f"'{method}'."
                )
            )


        if response.status_code >= 400:

            try:

                payload = response.json()

            except Exception:

                payload = {}


            raise RuntimeError(
                payload.get(
                    "message",
                    (
                        f"HTTP "
                        f"{response.status_code}"
                    ),
                )
            )


        return response.json()


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("=" * 68)

    print(
        "DAY 10.4 — STRUCTURED AI OUTPUT VALIDATION"
    )

    print("=" * 68)


    with TestClient(app) as client:

        transport = (
            TestClientTransport(
                client
            )
        )


        executor = ToolExecutor(
            transport=transport
        )


        engine = InvestigationEngine(
            tool_executor=executor
        )


        # ====================================================
        # BOOKING INVESTIGATION
        # ====================================================

        print()

        print(
            "VALIDATING BOOKING INVESTIGATION CONTEXT"
        )

        print(
            "-" * 40
        )


        request = InvestigationRequest(
            question=(
                "Investigate booking B007998 "
                "and explain the payment journey."
            )
        )


        response = (
            engine.execute_investigation(
                request
            )
        )


        context = (
            response.structured_context
        )


        check(
            "Investigation reaches RESULTS_READY",
            response.stage
            == InvestigationStage.RESULTS_READY,
            (
                "Stage="
                f"{response.stage.value}"
            ),
        )


        check(
            "Structured context is generated",
            context is not None,
            "LLM-ready structured context created.",
        )


        if context is not None:

            check(
                "Question is preserved",
                context.question
                == request.question,
                (
                    "Question="
                    f"{context.question}"
                ),
            )


            check(
                "Booking ID is preserved",
                context.booking_id
                == "B007998",
                (
                    "Booking="
                    f"{context.booking_id}"
                ),
            )


            check(
                "Primary metric is structured",
                context.primary_metric
                is not None,
                (
                    "Metric="
                    f"{context.primary_metric}"
                ),
            )


            check(
                "Evidence is populated",
                len(
                    context.evidence
                ) > 0,
                (
                    "Evidence items="
                    f"{len(context.evidence)}"
                ),
            )


            check(
                "Tool summary is populated",
                context.tool_summary.total > 0,
                (
                    "Tools="
                    f"{context.tool_summary.total}"
                ),
            )


            check(
                "Successful tool count is valid",
                context.tool_summary.successful > 0,
                (
                    "Successful="
                    f"{context.tool_summary.successful}"
                ),
            )


        # ====================================================
        # THRESHOLD INVESTIGATION
        # ====================================================

        print()

        print(
            "VALIDATING THRESHOLD CONTEXT"
        )

        print(
            "-" * 40
        )


        threshold_request = InvestigationRequest(
            question=(
                "What journeys are above 90 minutes?"
            )
        )


        threshold_response = (
            engine.execute_investigation(
                threshold_request
            )
        )


        threshold_context = (
            threshold_response.structured_context
        )


        check(
            "Threshold context is generated",
            threshold_context is not None,
            "Structured threshold context created.",
        )


        if threshold_context is not None:

            check(
                "Threshold metric is correct",
                threshold_context.primary_metric
                == "journey_duration_minutes",
                (
                    "Metric="
                    f"{threshold_context.primary_metric}"
                ),
            )


            check(
                "Threshold value is preserved",
                threshold_context.threshold
                == 90.0,
                (
                    "Threshold="
                    f"{threshold_context.threshold}"
                ),
            )


            check(
                "Threshold operator is preserved",
                threshold_context.threshold_operator
                == ">=",
                (
                    "Operator="
                    f"{threshold_context.threshold_operator}"
                ),
            )


            threshold_findings = (
                threshold_context.findings
            )


            check(
                "Threshold findings exist",
                isinstance(
                    threshold_findings,
                    list,
                ),
                (
                    "Findings="
                    f"{len(threshold_findings)}"
                ),
            )


        # ====================================================
        # PROVENANCE
        # ====================================================

        print()

        print(
            "VALIDATING EVIDENCE PROVENANCE"
        )

        print(
            "-" * 40
        )


        if context is not None:

            sources = {
                item.source
                for item
                in context.evidence
            }


            check(
                "Evidence contains source identifiers",
                all(
                    bool(
                        item.source
                    )
                    for item
                    in context.evidence
                ),
                (
                    "Distinct sources="
                    f"{len(sources)}"
                ),
            )


            categories = {
                item.category
                for item
                in context.evidence
            }


            check(
                "Evidence contains categories",
                all(
                    bool(
                        item.category
                    )
                    for item
                    in context.evidence
                ),
                (
                    "Categories="
                    f"{sorted(categories)}"
                ),
            )


        # ====================================================
        # NO HALLUCINATED EXPLANATION
        # ====================================================

        check(
            "Explanation remains empty before LLM",
            response.explanation is None,
            "No LLM explanation generated in Day 10.4.",
        )


        # ====================================================
        # SERIALIZATION
        # ====================================================

        serialized = response.model_dump()


        check(
            "Full response serializes",
            isinstance(
                serialized,
                dict,
            ),
            "Investigation response serializes to dictionary.",
        )


        check(
            "Structured context serializes",
            isinstance(
                serialized.get(
                    "structured_context"
                ),
                dict,
            ),
            "Structured context is JSON-compatible.",
        )


        # ====================================================
        # TOOL STATUS DISTRIBUTION
        # ====================================================

        successful = sum(
            1
            for result
            in response.tool_results
            if result.status
            == ToolExecutionStatus.SUCCESS
        )


        skipped = sum(
            1
            for result
            in response.tool_results
            if result.status
            == ToolExecutionStatus.SKIPPED
        )


        failed = sum(
            1
            for result
            in response.tool_results
            if result.status
            == ToolExecutionStatus.FAILED
        )


        check(
            "Tool status distribution reconciles",
            (
                successful
                + skipped
                + failed
                ==
                len(
                    response.tool_results
                )
            ),
            (
                f"Successful={successful}, "
                f"Skipped={skipped}, "
                f"Failed={failed}"
            ),
        )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()

    print("=" * 68)

    print(
        "DAY 10.4 STRUCTURED OUTPUT SUMMARY"
    )

    print("=" * 68)


    failed_checks = (
        total_checks -
        passed_checks
    )


    pass_rate = (
        (
            passed_checks /
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


    if passed_checks == total_checks:

        print(
            "DAY 10 BRICK 10.4 — PASSED"
        )

        print()

        print(
            "Investigation plans and deterministic tool "
            "results are now transformed into a structured, "
            "source-aware, LLM-ready investigation context."
        )

    else:

        print(
            "DAY 10 BRICK 10.4 — FAILED"
        )

        raise SystemExit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()