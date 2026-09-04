from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient


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
# APPLICATION IMPORTS
# ============================================================

from backend.main import app  # noqa: E402
from backend.ai.kpi import KPITool  # noqa: E402
from backend.ai.tools import ToolExecutor  # noqa: E402


# ============================================================
# VALIDATION COUNTERS
# ============================================================

total_checks = 0
passed_checks = 0


# ============================================================
# CHECK HELPER
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
        """
        Adapter used by ToolExecutor to call FastAPI
        endpoints through an in-process TestClient.
        """

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


            message = (
                payload.get("message")
                or payload.get("detail")
                or f"HTTP {response.status_code}"
            )


            raise RuntimeError(
                message
            )


        return response.json()


# ============================================================
# KPI LIST EXTRACTION
# ============================================================

def extract_kpi_list(
    payload,
) -> list[dict]:

    if isinstance(
        payload,
        list,
    ):
        return payload


    if not isinstance(
        payload,
        dict,
    ):
        return []


    candidate_keys = (
        "kpis",
        "metrics",
        "data",
        "results",
    )


    for key in candidate_keys:

        value = payload.get(
            key
        )


        if isinstance(
            value,
            list,
        ):
            return value


    return []


# ============================================================
# STATUS EXTRACTION
# ============================================================

def get_kpi_status(
    kpi: dict,
) -> str | None:

    value = (
        kpi.get("status")
        or kpi.get("availability")
        or kpi.get("kpi_status")
    )


    if value is None:
        return None


    return str(
        value
    ).strip().upper()


# ============================================================
# CANONICAL STATUS
# ============================================================

def canonical_kpi_status(
    status: str | None,
) -> str | None:
    """
    Normalize presentation/API status values into the
    validation vocabulary.

    NOT_SUPPORTED and NOT SUPPORTED both represent the
    unsupported KPI state.
    """

    if status is None:
        return None


    normalized = (
        status
        .strip()
        .upper()
        .replace(
            " ",
            "_",
        )
    )


    if normalized in {
        "NOT_SUPPORTED",
        "UNSUPPORTED",
    }:

        return "UNSUPPORTED"


    if normalized == "AVAILABLE":

        return "AVAILABLE"


    if normalized == "PROXY":

        return "PROXY"


    return normalized


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("=" * 68)

    print(
        "DAY 10.6 — KPI TOOL INTEGRATION VALIDATION"
    )

    print("=" * 68)


    with TestClient(app) as client:

        # ====================================================
        # TRANSPORT
        # ====================================================

        transport = TestClientTransport(
            client
        )


        # ====================================================
        # TOOL EXECUTOR
        # ====================================================

        executor = ToolExecutor(
            transport=transport
        )


        # ====================================================
        # KPI TOOL
        # ====================================================

        kpi_tool = KPITool(
            tool_executor=executor
        )


        # ====================================================
        # KPI TOOL VALIDATION
        # ====================================================

        print()

        print(
            "VALIDATING KPI TOOL"
        )

        print(
            "-" * 40
        )


        try:

            result = kpi_tool.run(
                "TOTAL_BOOKINGS"
            )

            tool_exception = None

        except Exception as exc:

            result = None

            tool_exception = str(
                exc
            )


        check(
            "KPI evidence is returned",
            result is not None,
            (
                "Normalized KPI evidence returned."
                if result is not None
                else f"Error={tool_exception}"
            ),
        )


        if result is not None:

            check(
                "Requested metric is preserved",
                result.requested_metric
                == "TOTAL_BOOKINGS",
                (
                    "Requested="
                    f"{result.requested_metric}"
                ),
            )


            check(
                "Matched KPI name is present",
                result.matched_name is not None,
                (
                    "Matched="
                    f"{result.matched_name}"
                ),
            )


            check(
                "KPI raw payload is preserved",
                isinstance(
                    result.raw_kpi,
                    dict,
                )
                and len(
                    result.raw_kpi
                ) > 0,
                (
                    "Raw fields="
                    f"{len(result.raw_kpi)}"
                ),
            )


            check(
                "KPI source is correct",
                result.source == "/kpis",
                (
                    "Source="
                    f"{result.source}"
                ),
            )


            check(
                "KPI status is present",
                result.status is not None,
                (
                    "Status="
                    f"{result.status}"
                ),
            )


            check(
                "KPI definition is preserved",
                result.definition is not None,
                (
                    "Definition="
                    f"{result.definition}"
                ),
            )


        else:

            for name in [
                "Requested metric is preserved",
                "Matched KPI name is present",
                "KPI raw payload is preserved",
                "KPI source is correct",
                "KPI status is present",
                "KPI definition is preserved",
            ]:

                check(
                    name,
                    False,
                    (
                        "KPI tool execution failed: "
                        f"{tool_exception}"
                    ),
                )


        # ====================================================
        # KPI CATALOG
        # ====================================================

        print()

        print(
            "VALIDATING KPI CATALOG"
        )

        print(
            "-" * 40
        )


        try:

            catalog_payload = transport.request(
                "GET",
                "/kpis",
            )

            catalog_exception = None

        except Exception as exc:

            catalog_payload = {}

            catalog_exception = str(
                exc
            )


        kpis = extract_kpi_list(
            catalog_payload
        )


        check(
            "KPI catalog returns a list",
            isinstance(
                kpis,
                list,
            ),
            (
                f"Records={len(kpis)}"
                if isinstance(
                    kpis,
                    list,
                )
                else (
                    "Error="
                    f"{catalog_exception}"
                )
            ),
        )


        check(
            "KPI catalog contains 22 records",
            len(kpis) == 22,
            (
                "Expected=22, "
                f"Actual={len(kpis)}"
            ),
        )


        # ====================================================
        # STATUS DISTRIBUTION
        # ====================================================

        print()

        print(
            "VALIDATING KPI STATUS DISTRIBUTION"
        )

        print(
            "-" * 40
        )


        status_values: list[str] = []


        for item in kpis:

            if not isinstance(
                item,
                dict,
            ):
                continue


            raw_status = get_kpi_status(
                item
            )


            normalized_status = (
                canonical_kpi_status(
                    raw_status
                )
            )


            if normalized_status is not None:

                status_values.append(
                    normalized_status
                )


        available_count = sum(
            status == "AVAILABLE"
            for status
            in status_values
        )


        proxy_count = sum(
            status == "PROXY"
            for status
            in status_values
        )


        unsupported_count = sum(
            status == "UNSUPPORTED"
            for status
            in status_values
        )


        check(
            "AVAILABLE KPI count reconciles",
            available_count == 19,
            (
                "Expected=19, "
                f"Actual={available_count}"
            ),
        )


        check(
            "PROXY KPI count reconciles",
            proxy_count == 1,
            (
                "Expected=1, "
                f"Actual={proxy_count}"
            ),
        )


        check(
            "UNSUPPORTED KPI count reconciles",
            unsupported_count == 2,
            (
                "Expected=2, "
                f"Actual={unsupported_count}"
            ),
        )


        # ====================================================
        # STATUS COVERAGE
        # ====================================================

        check(
            "All KPI records have a status",
            len(status_values) == len(kpis),
            (
                "Status-bearing records="
                f"{len(status_values)} / "
                f"{len(kpis)}"
            ),
        )


        check(
            "Status distribution reconciles to catalog",
            (
                available_count
                + proxy_count
                + unsupported_count
                == len(kpis)
            ),
            (
                f"AVAILABLE={available_count}, "
                f"PROXY={proxy_count}, "
                f"UNSUPPORTED={unsupported_count}, "
                f"TOTAL={len(kpis)}"
            ),
        )


        # ====================================================
        # UNSUPPORTED KPI SAFETY
        # ====================================================

        print()

        print(
            "VALIDATING KPI SAFETY"
        )

        print(
            "-" * 40
        )


        unsupported_result = executor.execute(
            "get_kpi",
            {
                "metric": "customer_complaint_rate",
            },
        )


        check(
            "Unsupported KPI is rejected safely",
            unsupported_result.status.value
            == "FAILED",
            (
                "Status="
                f"{unsupported_result.status.value}"
            ),
        )


        check(
            "Unsupported KPI returns an error",
            bool(
                unsupported_result.error
            ),
            (
                "Error="
                f"{unsupported_result.error}"
            ),
        )


        # ====================================================
        # KPI EVIDENCE SERIALIZATION
        # ====================================================

        print()

        print(
            "VALIDATING KPI EVIDENCE SERIALIZATION"
        )

        print(
            "-" * 40
        )


        if result is not None:

            try:

                serialized = result.model_dump(
                    mode="json"
                )

                serialization_error = None

            except Exception as exc:

                serialized = {}

                serialization_error = str(
                    exc
                )


            check(
                "KPI evidence is JSON serializable",
                isinstance(
                    serialized,
                    dict,
                )
                and serialization_error is None,
                (
                    "Serialized successfully."
                    if serialization_error is None
                    else (
                        "Error="
                        f"{serialization_error}"
                    )
                ),
            )


            check(
                "Serialized evidence contains source",
                serialized.get(
                    "source"
                ) == "/kpis",
                (
                    "Source="
                    f"{serialized.get('source')}"
                ),
            )


        else:

            check(
                "KPI evidence is JSON serializable",
                False,
                "KPI evidence object was not created.",
            )


            check(
                "Serialized evidence contains source",
                False,
                "KPI evidence object was not created.",
            )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()

    print("=" * 68)

    print(
        "DAY 10.6 KPI TOOL SUMMARY"
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


    if (
        total_checks > 0
        and passed_checks == total_checks
    ):

        print(
            "DAY 10 BRICK 10.6 — PASSED"
        )

        print()

        print(
            "The validated KPI catalog is now "
            "normalized into structured AI evidence "
            "with status handling, provenance and "
            "unsupported-KPI protection."
        )

    else:

        print(
            "DAY 10 BRICK 10.6 — FAILED"
        )

        raise SystemExit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()