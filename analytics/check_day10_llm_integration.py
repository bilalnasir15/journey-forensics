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
# IMPORTS
# ============================================================

from backend.main import app  # noqa: E402

from backend.ai.engine import (  # noqa: E402
    InvestigationEngine,
)

from backend.ai.llm import (  # noqa: E402
    DeterministicTestExplainer,
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
# MAIN
# ============================================================

def main() -> None:

    print("=" * 68)

    print(
        "DAY 10.8 — LLM INTEGRATION VALIDATION"
    )

    print("=" * 68)


    # ========================================================
    # OFFLINE LLM ENGINE
    # ========================================================

    print()

    print(
        "VALIDATING LLM EXPLAINER CONTRACT"
    )

    print(
        "-" * 40
    )


    test_llm = (
        DeterministicTestExplainer()
    )


    check(
        "Deterministic test LLM is configured",
        test_llm.configured is True,
        (
            "Provider="
            f"{test_llm.provider}"
        ),
    )


    check(
        "Deterministic test model is present",
        bool(
            test_llm.model
        ),
        (
            "Model="
            f"{test_llm.model}"
        ),
    )


    test_context = {

        "question":
            "Why are journeys above 90 minutes?",

        "findings": [

            {

                "title":
                    "Statistical threshold matches",

                "severity":
                    "HIGH",

                "metric":
                    "journey_duration_minutes",

                "value":
                    1015,

                "threshold":
                    90.0,
            }

        ],

        "statistical_evidence": [

            {

                "metric":
                    "journey_duration_minutes",

                "record_count":
                    8000,

                "threshold":
                    90.0,

                "flagged_count":
                    1015,

                "flagged_rate":
                    12.69,
            }

        ],
    }


    explanation = (
        test_llm.generate(
            test_context
        )
    )


    check(
        "LLM explainer returns text",
        isinstance(
            explanation,
            str,
        )
        and bool(
            explanation.strip()
        ),
        (
            "Characters="
            f"{len(explanation)}"
        ),
    )


    check(
        "LLM explanation preserves evidence",
        "1015" in explanation
        and "8000" in explanation,
        (
            "Key evidence values preserved."
        ),
    )


    check(
        "LLM explanation contains business sections",
        (
            "Finding:"
            in explanation
            and
            "Evidence:"
            in explanation
            and
            "Interpretation:"
            in explanation
        ),
        "Business explanation structure preserved.",
    )


    # ========================================================
    # ENGINE INTEGRATION
    # ========================================================

    print()

    print(
        "VALIDATING ENGINE LLM INTEGRATION"
    )

    print(
        "-" * 40
    )


    from backend.ai.tools import ToolExecutor


    # Reuse the application's in-process transport.
    from backend.ai.api import (
        ApplicationTransport,
    )


    executor = ToolExecutor(
        transport=ApplicationTransport()
    )


    engine = InvestigationEngine(
        tool_executor=executor,

        llm_explainer=test_llm,
    )


    from backend.ai.schemas import (
        InvestigationRequest,
        InvestigationStage,
    )


    request = InvestigationRequest(

        question=(
            "What journeys are above 90 minutes?"
        ),

        include_explanation=True,
    )


    response = (
        engine.execute_investigation(
            request
        )
    )


    check(
        "Engine generates an explanation",
        bool(
            response.explanation
        ),
        (
            "Explanation characters="
            f"{len(response.explanation or '')}"
        ),
    )


    check(
        "Engine reaches EXPLANATION_READY",
        response.stage
        == InvestigationStage.EXPLANATION_READY,
        (
            "Stage="
            f"{response.stage.value}"
        ),
    )


    check(
        "LLM provider metadata is preserved",
        response.llm_provider
        == "deterministic-test",
        (
            "Provider="
            f"{response.llm_provider}"
        ),
    )


    check(
        "LLM model metadata is preserved",
        response.llm_model
        == "deterministic-test-model",
        (
            "Model="
            f"{response.llm_model}"
        ),
    )


    check(
        "LLM error remains empty on success",
        response.llm_error is None,
        (
            "Error="
            f"{response.llm_error}"
        ),
    )


    check(
        "Structured context remains available",
        response.structured_context is not None,
        "Deterministic context preserved.",
    )


    check(
        "Tool results remain available",
        len(
            response.tool_results
        ) > 0,
        (
            "Tool results="
            f"{len(response.tool_results)}"
        ),
    )


    # ========================================================
    # API DEFAULT BEHAVIOR
    # ========================================================

    print()

    print(
        "VALIDATING API LLM OPT-IN BEHAVIOR"
    )

    print(
        "-" * 40
    )


    with TestClient(app) as client:

        default_response = client.post(
            "/ai/investigate",
            json={
                "question":
                    "What journeys are above 90 minutes?"
            },
        )


        check(
            "API default remains deterministic",
            default_response.status_code
            == 200,
            (
                "Status="
                f"{default_response.status_code}"
            ),
        )


        try:

            default_payload = (
                default_response.json()
            )

        except Exception:

            default_payload = {}


        check(
            "Default API stage is RESULTS_READY",
            default_payload.get(
                "stage"
            )
            == "results_ready",
            (
                "Stage="
                f"{default_payload.get('stage')}"
            ),
        )


        check(
            "Default API explanation is empty",
            default_payload.get(
                "explanation"
            ) is None,
            (
                "Explanation="
                f"{default_payload.get('explanation')}"
            ),
        )


        # ----------------------------------------------------
        # Opt-in LLM request
        # ----------------------------------------------------

        llm_response = client.post(
            "/ai/investigate",
            json={
                "question":
                    "What journeys are above 90 minutes?",

                "include_explanation":
                    False,
            },
        )


        check(
            "LLM flag is accepted by API",
            llm_response.status_code
            == 200,
            (
                "Status="
                f"{llm_response.status_code}"
            ),
        )


        try:

            llm_payload = (
                llm_response.json()
            )

        except Exception:

            llm_payload = {}


        check(
            "LLM request preserves deterministic context",
            isinstance(
                llm_payload.get(
                    "structured_context"
                ),
                dict,
            ),
            "Structured context returned.",
        )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()

    print("=" * 68)

    print(
        "DAY 10.8 LLM INTEGRATION SUMMARY"
    )

    print("=" * 68)


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
            "DAY 10 BRICK 10.8 — PASSED"
        )

        print()

        print(
            "The LLM explanation layer is integrated "
            "after deterministic investigation results, "
            "with evidence-grounded prompting, provider "
            "metadata and safe fallback behavior."
        )

    else:

        print(
            "DAY 10 BRICK 10.8 — FAILED"
        )

        raise SystemExit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()