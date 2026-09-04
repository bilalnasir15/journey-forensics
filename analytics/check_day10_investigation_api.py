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
# APP
# ============================================================

from backend.main import app  # noqa: E402


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
        "DAY 10.7 — INVESTIGATION API VALIDATION"
    )

    print("=" * 68)


    with TestClient(app) as client:

        # ====================================================
        # HEALTH
        # ====================================================

        print()

        print(
            "VALIDATING AI API HEALTH"
        )

        print(
            "-" * 40
        )


        health_response = client.get(
            "/ai/health"
        )


        check(
            "AI health endpoint responds",
            health_response.status_code == 200,
            (
                "Status="
                f"{health_response.status_code}"
            ),
        )


        try:

            health_payload = (
                health_response.json()
            )

        except Exception:

            health_payload = {}


        check(
            "AI health payload is structured",
            isinstance(
                health_payload,
                dict,
            ),
            (
                "Payload keys="
                f"{list(health_payload.keys())}"
            ),
        )


        check(
            "AI health reports OK",
            health_payload.get(
                "status"
            ) == "ok",
            (
                "Status="
                f"{health_payload.get('status')}"
            ),
        )


        # ====================================================
        # INVESTIGATION
        # ====================================================

        print()

        print(
            "VALIDATING INVESTIGATION ENDPOINT"
        )

        print(
            "-" * 40
        )


        question = (
            "What journeys are above 90 minutes?"
        )


        response = client.post(
            "/ai/investigate",
            json={
                "question": question
            },
        )


        check(
            "Investigation endpoint responds",
            response.status_code == 200,
            (
                "Status="
                f"{response.status_code}"
            ),
        )


        try:

            payload = response.json()

        except Exception:

            payload = {}


        check(
            "Investigation response is JSON",
            isinstance(
                payload,
                dict,
            ),
            (
                "JSON object returned."
            ),
        )


        # ====================================================
        # RESPONSE CONTRACT
        # ====================================================

        print()

        print(
            "VALIDATING RESPONSE CONTRACT"
        )

        print(
            "-" * 40
        )


        required_fields = [

            "question",

            "stage",

            "plan",

            "results",

            "tool_results",

            "structured_context",

            "explanation",

        ]


        for field in required_fields:

            check(
                (
                    "Response contains "
                    f"'{field}'"
                ),
                field in payload,
                (
                    f"Field '{field}' is present."
                ),
            )


        # ====================================================
        # QUESTION
        # ====================================================

        check(
            "Question is preserved",
            payload.get(
                "question"
            ) == question,
            (
                "Question="
                f"{payload.get('question')}"
            ),
        )


        # ====================================================
        # STAGE
        # ====================================================

        check(
            "Investigation reaches RESULTS_READY",
            payload.get(
                "stage"
            ) == "results_ready",
            (
                "Stage="
                f"{payload.get('stage')}"
            ),
        )


        # ====================================================
        # PLAN
        # ====================================================

        plan = payload.get(
            "plan"
        )


        check(
            "Plan is structured",
            isinstance(
                plan,
                dict,
            ),
            (
                "Plan keys="
                f"{list(plan.keys())}"
                if isinstance(
                    plan,
                    dict,
                )
                else "Plan is not an object."
            ),
        )


        if isinstance(
            plan,
            dict,
        ):

            check(
                "Plan intent is journey",
                plan.get(
                    "intent"
                ) == "journey",
                (
                    "Intent="
                    f"{plan.get('intent')}"
                ),
            )


            check(
                "Plan metric is correct",
                plan.get(
                    "primary_metric"
                )
                == "journey_duration_minutes",
                (
                    "Metric="
                    f"{plan.get('primary_metric')}"
                ),
            )


            check(
                "Plan threshold is correct",
                plan.get(
                    "threshold"
                ) == 90.0,
                (
                    "Threshold="
                    f"{plan.get('threshold')}"
                ),
            )


            check(
                "Plan operator is correct",
                plan.get(
                    "threshold_operator"
                ) == ">=",
                (
                    "Operator="
                    f"{plan.get('threshold_operator')}"
                ),
            )


        # ====================================================
        # RESULTS
        # ====================================================

        results = payload.get(
            "results"
        )


        check(
            "Results are returned as a list",
            isinstance(
                results,
                list,
            ),
            (
                "Results="
                f"{len(results)}"
                if isinstance(
                    results,
                    list,
                )
                else "Results is not a list."
            ),
        )


        # ====================================================
        # TOOL RESULTS
        # ====================================================

        tool_results = payload.get(
            "tool_results"
        )


        check(
            "Tool results are returned",
            isinstance(
                tool_results,
                list,
            )
            and len(
                tool_results
            ) > 0,
            (
                "Tool results="
                f"{len(tool_results)}"
                if isinstance(
                    tool_results,
                    list,
                )
                else "Tool results is not a list."
            ),
        )


        successful_tools = 0


        if isinstance(
            tool_results,
            list,
        ):

            for result in tool_results:

                if not isinstance(
                    result,
                    dict,
                ):
                    continue


                if (
                    result.get(
                        "status"
                    )
                    == "SUCCESS"
                ):

                    successful_tools += 1


        check(
            "At least one tool succeeds",
            successful_tools > 0,
            (
                "Successful tools="
                f"{successful_tools}"
            ),
        )


        # ====================================================
        # STRUCTURED CONTEXT
        # ====================================================

        context = payload.get(
            "structured_context"
        )


        check(
            "Structured context is returned",
            isinstance(
                context,
                dict,
            ),
            (
                "Context keys="
                f"{list(context.keys())}"
                if isinstance(
                    context,
                    dict,
                )
                else "Context is not an object."
            ),
        )


        if isinstance(
            context,
            dict,
        ):

            check(
                "Context question is preserved",
                context.get(
                    "question"
                ) == question,
                (
                    "Question="
                    f"{context.get('question')}"
                ),
            )


            check(
                "Context metric is correct",
                context.get(
                    "primary_metric"
                )
                == "journey_duration_minutes",
                (
                    "Metric="
                    f"{context.get('primary_metric')}"
                ),
            )


            check(
                "Context threshold is correct",
                context.get(
                    "threshold"
                ) == 90.0,
                (
                    "Threshold="
                    f"{context.get('threshold')}"
                ),
            )


            # ================================================
            # STATISTICAL EVIDENCE
            # ================================================

            statistical_evidence = (
                context.get(
                    "statistical_evidence"
                )
            )


            check(
                "Statistical evidence is exposed",
                isinstance(
                    statistical_evidence,
                    list,
                )
                and len(
                    statistical_evidence
                ) > 0,
                (
                    "Statistical evidence="
                    f"{len(statistical_evidence)}"
                    if isinstance(
                        statistical_evidence,
                        list,
                    )
                    else "Statistical evidence missing."
                ),
            )


            if (
                isinstance(
                    statistical_evidence,
                    list,
                )
                and statistical_evidence
            ):

                statistical = (
                    statistical_evidence[0]
                )


                if isinstance(
                    statistical,
                    dict,
                ):

                    check(
                        "API exposes record count",
                        statistical.get(
                            "record_count"
                        ) == 8000,
                        (
                            "Records="
                            f"{statistical.get('record_count')}"
                        ),
                    )


                    check(
                        "API exposes flagged count",
                        statistical.get(
                            "flagged_count"
                        ) == 1015,
                        (
                            "Flagged="
                            f"{statistical.get('flagged_count')}"
                        ),
                    )


                    check(
                        "API exposes threshold",
                        statistical.get(
                            "threshold"
                        ) == 90.0,
                        (
                            "Threshold="
                            f"{statistical.get('threshold')}"
                        ),
                    )


            # ================================================
            # KPI EVIDENCE
            # ================================================

            kpi_evidence = (
                context.get(
                    "kpi_evidence"
                )
            )


            check(
                "KPI evidence field is exposed",
                isinstance(
                    kpi_evidence,
                    list,
                ),
                (
                    "KPI evidence="
                    f"{len(kpi_evidence)}"
                    if isinstance(
                        kpi_evidence,
                        list,
                    )
                    else "KPI evidence is not a list."
                ),
            )


            # ================================================
            # FINDINGS
            # ================================================

            findings = context.get(
                "findings"
            )


            check(
                "Findings are exposed as a list",
                isinstance(
                    findings,
                    list,
                ),
                (
                    "Findings="
                    f"{len(findings)}"
                    if isinstance(
                        findings,
                        list,
                    )
                    else "Findings is not a list."
                ),
            )


            # ================================================
            # TOOL SUMMARY
            # ================================================

            tool_summary = context.get(
                "tool_summary"
            )


            check(
                "Tool summary is exposed",
                isinstance(
                    tool_summary,
                    dict,
                ),
                (
                    "Summary keys="
                    f"{list(tool_summary.keys())}"
                    if isinstance(
                        tool_summary,
                        dict,
                    )
                    else "Tool summary missing."
                ),
            )


        # ====================================================
        # LLM DEFERRED
        # ====================================================

        check(
            "LLM explanation is deferred",
            payload.get(
                "explanation"
            ) is None,
            (
                "Explanation="
                f"{payload.get('explanation')}"
            ),
        )


        # ====================================================
        # VALIDATION
        # ====================================================

        print()

        print(
            "VALIDATING REQUEST VALIDATION"
        )

        print(
            "-" * 40
        )


        invalid_response = client.post(
            "/ai/investigate",
            json={
                "question": ""
            },
        )


        check(
            "Invalid investigation request is rejected",
            invalid_response.status_code
            == 422,
            (
                "Status="
                f"{invalid_response.status_code}"
            ),
        )


        # ====================================================
        # HTTP METHOD
        # ====================================================

        get_response = client.get(
            "/ai/investigate"
        )


        check(
            "Investigation GET is rejected",
            get_response.status_code
            == 405,
            (
                "Status="
                f"{get_response.status_code}"
            ),
        )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()

    print("=" * 68)

    print(
        "DAY 10.7 INVESTIGATION API SUMMARY"
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
        and passed_checks
        == total_checks
    ):

        print(
            "DAY 10 BRICK 10.7 — PASSED"
        )

        print()

        print(
            "The AI investigation capability is exposed "
            "through a validated FastAPI endpoint with "
            "structured request/response contracts, "
            "deterministic tool execution and "
            "source-aware investigation evidence."
        )

    else:

        print(
            "DAY 10 BRICK 10.7 — FAILED"
        )

        raise SystemExit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()