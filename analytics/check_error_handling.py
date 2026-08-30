import os
import sys

import pandas as pd


# ============================================================
# MAKE PROJECT ROOT IMPORTABLE
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


from fastapi.testclient import TestClient

from backend.main import app


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "day8_error_handling_validation_report.csv"
)

UNKNOWN_CUSTOMER = "C999999"
UNKNOWN_BOOKING = "B999999"
INVALID_METRIC = "customer_happiness"


# ============================================================
# VALIDATION STORAGE
# ============================================================

results = []


def check(
    name,
    condition,
    detail=""
):

    status = (
        "PASS"
        if condition
        else "FAIL"
    )

    results.append(
        {
            "check": name,
            "status": status,
            "detail": detail
        }
    )

    print(
        f"{name}: {status}"
    )

    if detail:
        print(
            f"    {detail}"
        )


# ============================================================
# ERROR RESPONSE VALIDATOR
# ============================================================

def validate_error_response(
    response,
    expected_status,
    expected_error,
    expected_path,
    expected_message_text
):

    check(
        f"HTTP status is {expected_status}",
        response.status_code == expected_status,
        f"HTTP={response.status_code}"
    )

    try:

        payload = response.json()

        check(
            "Error response is valid JSON",
            isinstance(
                payload,
                dict
            ),
            "JSON object received"
        )

    except Exception as exc:

        check(
            "Error response is valid JSON",
            False,
            str(exc)
        )

        return

    required_fields = {
        "error",
        "message",
        "status_code",
        "path"
    }

    missing = (
        required_fields
        -
        set(payload.keys())
    )

    check(
        "Error response contains standard fields",
        len(missing) == 0,
        (
            "All standard error fields present"
            if not missing
            else f"Missing={sorted(missing)}"
        )
    )

    check(
        "Error type is correct",
        payload.get(
            "error"
        )
        ==
        expected_error,
        (
            f"Expected={expected_error}, "
            f"Actual={payload.get('error')}"
        )
    )

    check(
        "Error status_code matches HTTP status",
        payload.get(
            "status_code"
        )
        ==
        expected_status,
        (
            f"Expected={expected_status}, "
            f"Actual={payload.get('status_code')}"
        )
    )

    check(
        "Error path is correct",
        payload.get(
            "path"
        )
        ==
        expected_path,
        (
            f"Expected={expected_path}, "
            f"Actual={payload.get('path')}"
        )
    )

    message = str(
        payload.get(
            "message",
            ""
        )
    )

    check(
        "Error message contains expected detail",
        expected_message_text.lower()
        in
        message.lower(),
        message
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 8 — ERROR HANDLING VALIDATION")
    print("=" * 60)

    # ========================================================
    # TEST CLIENT
    # ========================================================

    try:

        client = TestClient(
            app
        )

        check(
            "FastAPI test client initialized",
            True,
            "Application loaded"
        )

    except Exception as exc:

        check(
            "FastAPI test client initialized",
            False,
            str(exc)
        )

        return 1

    # ========================================================
    # 404 PROFILE
    # ========================================================

    print()
    print("VALIDATING UNKNOWN CUSTOMER")
    print("-" * 40)

    profile_response = client.get(
        "/profile",
        params={
            "customer_id": UNKNOWN_CUSTOMER
        }
    )

    validate_error_response(
        response=profile_response,
        expected_status=404,
        expected_error="HTTP_ERROR",
        expected_path="/profile",
        expected_message_text=UNKNOWN_CUSTOMER
    )

    # ========================================================
    # 404 JOURNEY
    # ========================================================

    print()
    print("VALIDATING UNKNOWN JOURNEY")
    print("-" * 40)

    journey_response = client.get(
        f"/journey/{UNKNOWN_BOOKING}"
    )

    validate_error_response(
        response=journey_response,
        expected_status=404,
        expected_error="HTTP_ERROR",
        expected_path=f"/journey/{UNKNOWN_BOOKING}",
        expected_message_text=UNKNOWN_BOOKING
    )

    # ========================================================
    # 404 CUSTOMERS PAGE
    # ========================================================

    print()
    print("VALIDATING OUT-OF-RANGE CUSTOMER PAGE")
    print("-" * 40)

    customers_response = client.get(
        "/customers",
        params={
            "page": 9999,
            "page_size": 10
        }
    )

    validate_error_response(
        response=customers_response,
        expected_status=404,
        expected_error="HTTP_ERROR",
        expected_path="/customers",
        expected_message_text="Page 9999"
    )

    # ========================================================
    # 400 INVALID INVESTIGATION METRIC
    # ========================================================

    print()
    print("VALIDATING INVALID INVESTIGATION METRIC")
    print("-" * 40)

    investigation_response = client.post(
        "/investigate",
        json={
            "metric": INVALID_METRIC,
            "threshold": 50
        }
    )

    validate_error_response(
        response=investigation_response,
        expected_status=400,
        expected_error="HTTP_ERROR",
        expected_path="/investigate",
        expected_message_text=INVALID_METRIC
    )

    try:

        investigation_json = (
            investigation_response.json()
        )

        investigation_message = str(
            investigation_json.get(
                "message",
                ""
            )
        )

        check(
            "Invalid investigation error lists supported metrics",
            "Supported metrics" in investigation_message,
            investigation_message
        )

    except Exception as exc:

        check(
            "Invalid investigation error lists supported metrics",
            False,
            str(exc)
        )

    # ========================================================
    # 422 MISSING PROFILE PARAMETER
    # ========================================================

    print()
    print("VALIDATING MISSING PROFILE PARAMETER")
    print("-" * 40)

    missing_profile_response = client.get(
        "/profile"
    )

    validate_error_response(
        response=missing_profile_response,
        expected_status=422,
        expected_error="VALIDATION_ERROR",
        expected_path="/profile",
        expected_message_text="validation"
    )

    # ========================================================
    # 422 INVALID CUSTOMER PAGE
    # ========================================================

    print()
    print("VALIDATING INVALID CUSTOMER PAGE PARAMETER")
    print("-" * 40)

    invalid_page_response = client.get(
        "/customers",
        params={
            "page": 0,
            "page_size": 10
        }
    )

    validate_error_response(
        response=invalid_page_response,
        expected_status=422,
        expected_error="VALIDATION_ERROR",
        expected_path="/customers",
        expected_message_text="validation"
    )

    # ========================================================
    # 422 INVALID PAGE SIZE
    # ========================================================

    print()
    print("VALIDATING INVALID PAGE SIZE")
    print("-" * 40)

    invalid_page_size_response = client.get(
        "/customers",
        params={
            "page": 1,
            "page_size": 501
        }
    )

    validate_error_response(
        response=invalid_page_size_response,
        expected_status=422,
        expected_error="VALIDATION_ERROR",
        expected_path="/customers",
        expected_message_text="validation"
    )

    # ========================================================
    # 422 MISSING INVESTIGATION BODY
    # ========================================================

    print()
    print("VALIDATING MISSING INVESTIGATION BODY")
    print("-" * 40)

    missing_investigation_response = client.post(
        "/investigate"
    )

    validate_error_response(
        response=missing_investigation_response,
        expected_status=422,
        expected_error="VALIDATION_ERROR",
        expected_path="/investigate",
        expected_message_text="validation"
    )

    # ========================================================
    # 422 EMPTY INVESTIGATION METRIC
    # ========================================================

    print()
    print("VALIDATING EMPTY INVESTIGATION METRIC")
    print("-" * 40)

    empty_metric_response = client.post(
        "/investigate",
        json={
            "metric": "",
            "threshold": 50
        }
    )

    validate_error_response(
        response=empty_metric_response,
        expected_status=422,
        expected_error="VALIDATION_ERROR",
        expected_path="/investigate",
        expected_message_text="validation"
    )

    # ========================================================
    # 404 UNKNOWN ROUTE
    # ========================================================

    print()
    print("VALIDATING UNKNOWN ROUTE")
    print("-" * 40)

    unknown_route_response = client.get(
        "/this-route-does-not-exist"
    )

    validate_error_response(
        response=unknown_route_response,
        expected_status=404,
        expected_error="HTTP_ERROR",
        expected_path="/this-route-does-not-exist",
        expected_message_text="Not Found"
    )

    # ========================================================
    # STANDARDIZATION ACROSS RESPONSES
    # ========================================================

    print()
    print("VALIDATING ERROR RESPONSE STANDARDIZATION")
    print("-" * 40)

    standardized_responses = [
        profile_response,
        journey_response,
        customers_response,
        investigation_response,
        missing_profile_response,
        invalid_page_response,
        invalid_page_size_response,
        missing_investigation_response,
        empty_metric_response,
        unknown_route_response
    ]

    required_standard_fields = {
        "error",
        "message",
        "status_code",
        "path"
    }

    inconsistent = 0

    for response in standardized_responses:

        try:

            payload = response.json()

            if not required_standard_fields.issubset(
                set(payload.keys())
            ):

                inconsistent += 1

        except Exception:

            inconsistent += 1

    check(
        "All tested errors use standardized response structure",
        inconsistent == 0,
        (
            f"Inconsistent responses={inconsistent}"
        )
    )

    # ========================================================
    # SUCCESS ENDPOINTS REMAIN HEALTHY
    # ========================================================

    print()
    print("VALIDATING SUCCESS ENDPOINTS REMAIN HEALTHY")
    print("-" * 40)

    root_response = client.get(
        "/"
    )

    check(
        "Root endpoint still returns 200",
        root_response.status_code == 200,
        f"HTTP={root_response.status_code}"
    )

    health_response = client.get(
        "/health"
    )

    check(
        "Health endpoint still returns 200",
        health_response.status_code == 200,
        f"HTTP={health_response.status_code}"
    )

    customers_success_response = client.get(
        "/customers",
        params={
            "page": 1,
            "page_size": 1
        }
    )

    check(
        "Customers endpoint still returns 200",
        customers_success_response.status_code == 200,
        f"HTTP={customers_success_response.status_code}"
    )

    kpis_success_response = client.get(
        "/kpis"
    )

    check(
        "KPI endpoint still returns 200",
        kpis_success_response.status_code == 200,
        f"HTTP={kpis_success_response.status_code}"
    )

    journey_success_response = client.get(
        "/journey/B007998"
    )

    check(
        "Journey endpoint still returns 200",
        journey_success_response.status_code == 200,
        f"HTTP={journey_success_response.status_code}"
    )

    investigate_success_response = client.post(
        "/investigate",
        json={
            "metric": "journey_duration_minutes",
            "threshold": 90
        }
    )

    check(
        "Investigation endpoint still returns 200",
        investigate_success_response.status_code == 200,
        f"HTTP={investigate_success_response.status_code}"
    )

    # ========================================================
    # OPENAPI
    # ========================================================

    print()
    print("VALIDATING OPENAPI")
    print("-" * 40)

    openapi_response = client.get(
        "/openapi.json"
    )

    check(
        "OpenAPI specification is available",
        openapi_response.status_code == 200,
        f"HTTP={openapi_response.status_code}"
    )

    try:

        openapi = (
            openapi_response.json()
        )

        paths = openapi.get(
            "paths",
            {}
        )

        required_routes = {
            "/",
            "/health",
            "/profile",
            "/customers",
            "/journey/{booking_id}",
            "/kpis",
            "/upload",
            "/investigate"
        }

        missing_routes = (
            required_routes
            -
            set(paths.keys())
        )

        check(
            "All production API routes remain registered",
            len(missing_routes) == 0,
            (
                "All routes registered"
                if not missing_routes
                else f"Missing={sorted(missing_routes)}"
            )
        )

    except Exception as exc:

        check(
            "OpenAPI route inspection succeeds",
            False,
            str(exc)
        )

    # ========================================================
    # SAVE REPORT
    # ========================================================

    validation_df = pd.DataFrame(
        results
    )

    validation_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    total = len(
        validation_df
    )

    passed = int(
        (
            validation_df[
                "status"
            ]
            ==
            "PASS"
        ).sum()
    )

    failed = (
        total
        -
        passed
    )

    pass_rate = round(
        passed
        /
        total
        *
        100,
        2
    )

    print()
    print("=" * 60)
    print("DAY 8 ERROR HANDLING VALIDATION SUMMARY")
    print("=" * 60)

    print(
        f"Total checks: {total}"
    )

    print(
        f"Passed: {passed}"
    )

    print(
        f"Failed: {failed}"
    )

    print(
        f"Pass rate: {pass_rate:.2f}%"
    )

    print()

    if failed == 0:

        print("=" * 60)
        print(
            "DAY 8 BRICK 8.9 — ERROR HANDLING: PASSED"
        )
        print("=" * 60)

        print()
        print(
            "404, 400, 422 handling, standardized "
            "error responses, route handling, request "
            "validation, and regression checks are "
            "independently validated."
        )

        print()
        print(
            "Validation report:"
        )

        print(
            OUTPUT_FILE
        )

        return 0

    print("=" * 60)
    print(
        "DAY 8 BRICK 8.9 — ERROR HANDLING: FAILED"
    )
    print("=" * 60)

    print()

    print(
        validation_df[
            validation_df[
                "status"
            ]
            ==
            "FAIL"
        ].to_string(
            index=False
        )
    )

    print()
    print(
        "Validation report:"
    )

    print(
        OUTPUT_FILE
    )

    return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )