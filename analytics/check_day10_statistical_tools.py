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

from backend.ai.engine import InvestigationEngine
from backend.ai.schemas import (
    InvestigationRequest,
    InvestigationStage,
)
from backend.ai.statistics import StatisticalTool
from backend.ai.tools import ToolExecutor


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
# TEST CLIENT TRANSPORT
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
                f"Unsupported HTTP method '{method}'."
            )

        if response.status_code >= 400:

            try:
                payload = response.json()
            except Exception:
                payload = {}

            raise RuntimeError(
                payload.get(
                    "message",
                    f"HTTP {response.status_code}",
                )
            )

        return response.json()


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("=" * 68)

    print(
        "DAY 10.5 — STATISTICAL TOOL INTEGRATION VALIDATION"
    )

    print("=" * 68)


    with TestClient(app) as client:

        transport = TestClientTransport(
            client
        )

        executor = ToolExecutor(
            transport=transport
        )

        statistical_tool = StatisticalTool(
            tool_executor=executor
        )


        # ====================================================
        # BASIC STATISTICAL TOOL
        # ====================================================

        print()

        print(
            "VALIDATING STATISTICAL TOOL"
        )

        print(
            "-" * 40
        )


        evidence = statistical_tool.run(
            metric="journey_duration_minutes",
            threshold=90,
        )


        check(
            "Statistical tool returns evidence",
            evidence is not None,
            "Normalized statistical evidence returned.",
        )


        check(
            "Metric is preserved",
            evidence.metric
            == "journey_duration_minutes",
            (
                "Metric="
                f"{evidence.metric}"
            ),
        )


        check(
            "Record count is available",
            evidence.record_count is not None,
            (
                "Records="
                f"{evidence.record_count}"
            ),
        )


        check(
            "Record count reconciles to journey dataset",
            evidence.record_count == 8000,
            (
                "Expected=8000, "
                f"Actual={evidence.record_count}"
            ),
        )


        check(
            "Threshold is preserved",
            evidence.threshold == 90.0,
            (
                "Threshold="
                f"{evidence.threshold}"
            ),
        )


        check(
            "Flagged count is available",
            evidence.flagged_count is not None,
            (
                "Flagged="
                f"{evidence.flagged_count}"
            ),
        )


        check(
            "Flagged count reconciles",
            evidence.flagged_count == 1015,
            (
                "Expected=1015, "
                f"Actual={evidence.flagged_count}"
            ),
        )


        check(
            "Flagged rate is derived deterministically",
            evidence.flagged_rate is not None,
            (
                "Flagged rate="
                f"{evidence.flagged_rate}"
            ),
        )


        expected_rate = (
            1015 / 8000 * 100
        )


        if evidence.flagged_rate is not None:

            check(
                "Flagged rate calculation reconciles",
                abs(
                    evidence.flagged_rate
                    - expected_rate
                ) < 0.01,
                (
                    "Expected="
                    f"{expected_rate:.4f}, "
                    "Actual="
                    f"{evidence.flagged_rate:.4f}"
                ),
            )

        else:

            check(
                "Flagged rate calculation reconciles",
                False,
                "Flagged rate is missing.",
            )


        check(
            "Raw deterministic result is retained",
            isinstance(
                evidence.raw_result,
                dict,
            )
            and len(
                evidence.raw_result
            ) > 0,
            (
                "Raw fields="
                f"{len(evidence.raw_result)}"
            ),
        )


        check(
            "Source is explicitly identified",
            evidence.source == "/investigate",
            (
                "Source="
                f"{evidence.source}"
            ),
        )


        # ====================================================
        # ENGINE INTEGRATION
        # ====================================================

        print()

        print(
            "VALIDATING ENGINE STATISTICAL INTEGRATION"
        )

        print(
            "-" * 40
        )


        engine = InvestigationEngine(
            tool_executor=executor
        )


        request = InvestigationRequest(
            question=(
                "What journeys are above 90 minutes?"
            )
        )


        response = engine.execute_investigation(
            request
        )


        context = response.structured_context


        check(
            "Engine reaches RESULTS_READY",
            response.stage
            == InvestigationStage.RESULTS_READY,
            (
                "Stage="
                f"{response.stage.value}"
            ),
        )


        if context is None:

            check(
                "Structured context contains statistical evidence",
                False,
                "Structured context is missing.",
            )

            check(
                "Context metric is correct",
                False,
                "Structured context is missing.",
            )

            check(
                "Context record count is correct",
                False,
                "Structured context is missing.",
            )

            check(
                "Context threshold is correct",
                False,
                "Structured context is missing.",
            )

            check(
                "Context flagged count is correct",
                False,
                "Structured context is missing.",
            )

            check(
                "Context statistical source is preserved",
                False,
                "Structured context is missing.",
            )

            check(
                "Statistical evidence is JSON serializable",
                False,
                "Structured context is missing.",
            )

        else:

            statistical_records = (
                context.statistical_evidence
            )


            check(
                "Structured context contains statistical evidence",
                len(
                    statistical_records
                ) > 0,
                (
                    "Statistical evidence="
                    f"{len(statistical_records)}"
                ),
            )


            if len(statistical_records) > 0:

                statistical = (
                    statistical_records[0]
                )


                check(
                    "Context metric is correct",
                    statistical.metric
                    == "journey_duration_minutes",
                    (
                        "Metric="
                        f"{statistical.metric}"
                    ),
                )


                check(
                    "Context record count is correct",
                    statistical.record_count
                    == 8000,
                    (
                        "Records="
                        f"{statistical.record_count}"
                    ),
                )


                check(
                    "Context threshold is correct",
                    statistical.threshold
                    == 90.0,
                    (
                        "Threshold="
                        f"{statistical.threshold}"
                    ),
                )


                check(
                    "Context flagged count is correct",
                    statistical.flagged_count
                    == 1015,
                    (
                        "Flagged="
                        f"{statistical.flagged_count}"
                    ),
                )


                check(
                    "Context statistical source is preserved",
                    statistical.source
                    == "run_statistical_analysis",
                    (
                        "Source="
                        f"{statistical.source}"
                    ),
                )


            else:

                check(
                    "Context metric is correct",
                    False,
                    "No statistical evidence record exists.",
                )

                check(
                    "Context record count is correct",
                    False,
                    "No statistical evidence record exists.",
                )

                check(
                    "Context threshold is correct",
                    False,
                    "No statistical evidence record exists.",
                )

                check(
                    "Context flagged count is correct",
                    False,
                    "No statistical evidence record exists.",
                )

                check(
                    "Context statistical source is preserved",
                    False,
                    "No statistical evidence record exists.",
                )


            serialized_context = (
                context.model_dump(
                    mode="json"
                )
            )


            check(
                "Statistical evidence is JSON serializable",
                isinstance(
                    serialized_context.get(
                        "statistical_evidence"
                    ),
                    list,
                ),
                "Structured statistical evidence is serializable.",
            )


        # ====================================================
        # NO LLM
        # ====================================================

        check(
            "No LLM explanation is generated",
            response.explanation is None,
            "LLM remains intentionally deferred.",
        )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()

    print("=" * 68)

    print(
        "DAY 10.5 STATISTICAL TOOL SUMMARY"
    )

    print("=" * 68)


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
            "DAY 10 BRICK 10.5 — PASSED"
        )

        print()

        print(
            "The deterministic statistical investigation "
            "layer is integrated with the AI engine, "
            "normalized into structured evidence, and "
            "reconciled against validated journey results."
        )

    else:

        print(
            "DAY 10 BRICK 10.5 — FAILED"
        )

        raise SystemExit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()