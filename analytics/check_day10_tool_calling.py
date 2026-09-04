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
    ToolExecutionStatus,
)

from backend.ai.tools import (
    TOOL_DEFINITIONS,
    ToolExecutor,
)


# ============================================================
# TEST COUNTERS
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
# TEST TRANSPORT
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

        if method.upper() == "GET":

            response = self.client.get(
                path,
                params=params or {},
            )

        elif method.upper() == "POST":

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
                    (
                        f"HTTP {response.status_code}"
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
        "DAY 10.2 — TOOL CALLING VALIDATION"
    )

    print("=" * 68)


    with TestClient(app) as client:

        transport = TestClientTransport(
            client
        )

        executor = ToolExecutor(
            transport=transport
        )

        engine = InvestigationEngine(
            tool_executor=executor
        )


        # ====================================================
        # REGISTRY
        # ====================================================

        print()

        print(
            "VALIDATING TOOL REGISTRY"
        )

        print(
            "-" * 40
        )

        expected_tools = {
            "get_kpi",
            "get_customer_profile",
            "get_journey",
            "run_statistical_analysis",
            "find_anomalies",
            "get_data_quality",
        }

        actual_tools = set(
            executor.available_tools()
        )

        check(
            "Tool registry contains all Day 10.2 tools",
            expected_tools.issubset(
                actual_tools
            ),
            f"Tools={sorted(actual_tools)}",
        )

        check(
            "Tool definitions are structured",
            all(
                isinstance(
                    definition.description,
                    str,
                )
                and definition.name
                for definition
                in TOOL_DEFINITIONS.values()
            ),
            (
                "Registered definitions="
                f"{len(TOOL_DEFINITIONS)}"
            ),
        )


        # ====================================================
        # CUSTOMER PROFILE TOOL
        # ====================================================

        print()

        print(
            "VALIDATING CUSTOMER PROFILE TOOL"
        )

        print(
            "-" * 40
        )

        profile_result = executor.execute(
            "get_customer_profile",
            {
                "customer_id": "C004781",
            },
        )

        check(
            "Customer profile tool executes",
            profile_result.status
            == ToolExecutionStatus.SUCCESS,
            (
                "Status="
                f"{profile_result.status.value}"
            ),
        )

        check(
            "Customer profile returns correct customer",
            profile_result.data.get(
                "customer_id"
            )
            == "C004781",
            (
                "Customer="
                f"{profile_result.data.get('customer_id')}"
            ),
        )


        # ====================================================
        # JOURNEY TOOL
        # ====================================================

        print()

        print(
            "VALIDATING JOURNEY TOOL"
        )

        print(
            "-" * 40
        )

        journey_result = executor.execute(
            "get_journey",
            {
                "booking_id": "B007998",
            },
        )

        check(
            "Journey tool executes",
            journey_result.status
            == ToolExecutionStatus.SUCCESS,
            (
                "Status="
                f"{journey_result.status.value}"
            ),
        )

        check(
            "Journey tool returns correct booking",
            journey_result.data.get(
                "booking_id"
            )
            == "B007998",
            (
                "Booking="
                f"{journey_result.data.get('booking_id')}"
            ),
        )


        # ====================================================
        # KPI TOOL
        # ====================================================

        print()

        print(
            "VALIDATING KPI TOOL"
        )

        print(
            "-" * 40
        )

        kpi_result = executor.execute(
            "get_kpi",
            {
                "metric": "TOTAL_BOOKINGS",
            },
        )

        check(
            "KPI tool executes",
            kpi_result.status
            == ToolExecutionStatus.SUCCESS,
            (
                "Status="
                f"{kpi_result.status.value}"
            ),
        )

        check(
            "KPI tool returns matched metric",
            kpi_result.data.get(
                "matched_kpi"
            )
            is not None,
            "Validated KPI match returned.",
        )


        # ====================================================
        # STATISTICAL TOOL
        # ====================================================

        print()

        print(
            "VALIDATING STATISTICAL TOOL"
        )

        print(
            "-" * 40
        )

        statistical_result = executor.execute(
            "run_statistical_analysis",
            {
                "metric": (
                    "journey_duration_minutes"
                ),
            },
        )

        check(
            "Statistical tool executes",
            statistical_result.status
            == ToolExecutionStatus.SUCCESS,
            (
                "Status="
                f"{statistical_result.status.value}"
            ),
        )

        check(
            "Statistical result contains metric",
            statistical_result.data.get(
                "metric"
            )
            == "journey_duration_minutes",
            (
                "Metric="
                f"{statistical_result.data.get('metric')}"
            ),
        )


        # ====================================================
        # ANOMALY TOOL
        # ====================================================

        print()

        print(
            "VALIDATING ANOMALY TOOL"
        )

        print(
            "-" * 40
        )

        anomaly_result = executor.execute(
            "find_anomalies",
            {
                "metric": (
                    "journey_duration_minutes"
                ),
                "threshold": 90,
            },
        )

        check(
            "Anomaly tool executes",
            anomaly_result.status
            == ToolExecutionStatus.SUCCESS,
            (
                "Status="
                f"{anomaly_result.status.value}"
            ),
        )

        check(
            "Anomaly tool preserves threshold",
            anomaly_result.data.get(
                "threshold"
            )
            == 90.0,
            (
                "Threshold="
                f"{anomaly_result.data.get('threshold')}"
            ),
        )


        # ====================================================
        # DATA QUALITY TOOL
        # ====================================================

        print()

        print(
            "VALIDATING DATA QUALITY TOOL"
        )

        print(
            "-" * 40
        )

        quality_result = executor.execute(
            "get_data_quality"
        )

        check(
            "Data quality tool executes",
            quality_result.status
            == ToolExecutionStatus.SUCCESS,
            (
                "Status="
                f"{quality_result.status.value}"
            ),
        )

        check(
            "Data quality returns dataset collection",
            isinstance(
                quality_result.data.get(
                    "datasets"
                ),
                list,
            ),
            (
                "Datasets="
                f"{len(quality_result.data.get('datasets', []))}"
            ),
        )


        # ====================================================
        # INVALID TOOL
        # ====================================================

        print()

        print(
            "VALIDATING TOOL ERROR HANDLING"
        )

        print(
            "-" * 40
        )

        invalid_result = executor.execute(
            "does_not_exist",
            {},
        )

        check(
            "Unknown tool is rejected",
            invalid_result.status
            == ToolExecutionStatus.FAILED,
            (
                "Status="
                f"{invalid_result.status.value}"
            ),
        )

        check(
            "Unknown tool returns error",
            bool(
                invalid_result.error
            ),
            (
                "Error="
                f"{invalid_result.error}"
            ),
        )


        # ====================================================
        # MISSING PARAMETER
        # ====================================================

        missing_parameter_result = (
            executor.execute(
                "get_journey",
                {},
            )
        )

        check(
            "Missing tool parameters are rejected",
            missing_parameter_result.status
            == ToolExecutionStatus.FAILED,
            (
                "Status="
                f"{missing_parameter_result.status.value}"
            ),
        )


        # ====================================================
        # ENGINE END-TO-END TOOL EXECUTION
        # ====================================================

        print()

        print(
            "VALIDATING ENGINE TOOL EXECUTION"
        )

        print(
            "-" * 40
        )

        request = InvestigationRequest(
            question=(
                "Why are payment retries increasing?"
            )
        )

        response = (
            engine.execute_investigation(
                request
            )
        )

        summary = (
            engine.execution_summary(
                response
            )
        )

        check(
            "Engine executes planned tools",
            len(
                response.tool_results
            ) > 0,
            (
                "Executed tools="
                f"{len(response.tool_results)}"
            ),
        )

        check(
            "Engine reaches TOOLS_EXECUTED stage",
            response.stage.value
            == "tools_executed",
            (
                "Stage="
                f"{response.stage.value}"
            ),
        )

        check(
            "Engine has successful tool results",
            summary["successful"] > 0,
            (
                "Successful="
                f"{summary['successful']}"
            ),
        )

        check(
            "Engine stores tool results in response",
            len(
                response.results
            )
            == len(
                response.tool_results
            ),
            (
                "Results="
                f"{len(response.results)}"
            ),
        )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()

    print("=" * 68)

    print(
        "DAY 10.2 TOOL CALLING SUMMARY"
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
        ) * 100
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
            "DAY 10 BRICK 10.2 — PASSED"
        )

        print()

        print(
            "Tool registry, parameter validation, "
            "real API-backed tool execution, deterministic "
            "statistical/anomaly analysis and engine-level "
            "tool orchestration are working correctly."
        )

    else:

        print(
            "DAY 10 BRICK 10.2 — FAILED"
        )

        raise SystemExit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()