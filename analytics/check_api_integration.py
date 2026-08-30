import os
import sys
from io import BytesIO

import numpy as np
import pandas as pd


# ============================================================
# PROJECT ROOT
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

PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

PROFILE_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_segmentation_final.csv"
)

JOURNEY_FILE = os.path.join(
    PROCESSED_DIR,
    "customer_journey_features.csv"
)

KPI_FILE = os.path.join(
    PROCESSED_DIR,
    "day5_kpi_report.csv"
)

UPLOAD_DIR = os.path.join(
    BASE_DIR,
    "data",
    "uploads"
)

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day8_full_api_validation_report.csv"
)

VALID_CUSTOMER = "C004781"
VALID_BOOKING = "B007998"

UNKNOWN_CUSTOMER = "C999999"
UNKNOWN_BOOKING = "B999999"


# ============================================================
# RESULTS
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
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 8 — FULL API INTEGRATION VALIDATION")
    print("=" * 60)

    # ========================================================
    # LOAD SOURCE DATASETS
    # ========================================================

    print()
    print("LOADING SOURCE DATASETS")
    print("-" * 40)

    try:

        profile_df = pd.read_csv(
            PROFILE_FILE
        )

        journey_df = pd.read_csv(
            JOURNEY_FILE
        )

        kpi_df = pd.read_csv(
            KPI_FILE
        )

        check(
            "Profile source loads",
            True,
            f"Rows={len(profile_df):,}"
        )

        check(
            "Journey source loads",
            True,
            f"Rows={len(journey_df):,}"
        )

        check(
            "KPI source loads",
            True,
            f"Rows={len(kpi_df):,}"
        )

    except Exception as exc:

        check(
            "Source datasets load",
            False,
            str(exc)
        )

        return 1

    # ========================================================
    # SOURCE BASELINE
    # ========================================================

    check(
        "Profile source has 5,000 customers",
        len(profile_df) == 5000,
        f"Actual={len(profile_df):,}"
    )

    check(
        "Journey source has 8,000 journeys",
        len(journey_df) == 8000,
        f"Actual={len(journey_df):,}"
    )

    check(
        "KPI source has 22 records",
        len(kpi_df) == 22,
        f"Actual={len(kpi_df):,}"
    )

    # ========================================================
    # CLIENT
    # ========================================================

    try:

        client = TestClient(
            app
        )

        check(
            "FastAPI application initializes",
            True,
            "Application loaded"
        )

    except Exception as exc:

        check(
            "FastAPI application initializes",
            False,
            str(exc)
        )

        return 1

    # ========================================================
    # ROOT
    # ========================================================

    print()
    print("VALIDATING ROOT")
    print("-" * 40)

    root_response = client.get(
        "/"
    )

    check(
        "GET / returns 200",
        root_response.status_code == 200,
        f"HTTP={root_response.status_code}"
    )

    try:

        root_json = root_response.json()

        check(
            "Root response is valid JSON",
            isinstance(
                root_json,
                dict
            ),
            "JSON object received"
        )

        check(
            "Root identifies Journey Forensics",
            root_json.get(
                "project"
            )
            ==
            "Journey Forensics",
            (
                f"Project="
                f"{root_json.get('project')}"
            )
        )

    except Exception as exc:

        check(
            "Root response is valid JSON",
            False,
            str(exc)
        )

    # ========================================================
    # HEALTH
    # ========================================================

    print()
    print("VALIDATING HEALTH")
    print("-" * 40)

    health_response = client.get(
        "/health"
    )

    check(
        "GET /health returns 200",
        health_response.status_code == 200,
        f"HTTP={health_response.status_code}"
    )

    try:

        health_json = health_response.json()

        check(
            "Health status is healthy",
            health_json.get(
                "status"
            )
            ==
            "healthy",
            (
                f"Status="
                f"{health_json.get('status')}"
            )
        )

    except Exception as exc:

        check(
            "Health response is valid JSON",
            False,
            str(exc)
        )

    # ========================================================
    # PROFILE
    # ========================================================

    print()
    print("VALIDATING PROFILE")
    print("-" * 40)

    source_customer = profile_df[
        profile_df["customer_id"].astype(str)
        ==
        VALID_CUSTOMER
    ]

    profile_response = client.get(
        "/profile",
        params={
            "customer_id": VALID_CUSTOMER
        }
    )

    check(
        "GET /profile returns 200",
        profile_response.status_code == 200,
        f"HTTP={profile_response.status_code}"
    )

    profile_json = profile_response.json()

    check(
        "Profile customer ID is correct",
        profile_json.get(
            "customer_id"
        )
        ==
        VALID_CUSTOMER,
        (
            f"Customer="
            f"{profile_json.get('customer_id')}"
        )
    )

    if not source_customer.empty:

        source_row = source_customer.iloc[0]

        check(
            "Profile revenue reconciles",
            np.isclose(
                float(
                    profile_json["total_revenue"]
                ),
                float(
                    source_row["total_revenue"]
                ),
                atol=0.01
            ),
            (
                f"API={profile_json['total_revenue']}, "
                f"Source={source_row['total_revenue']}"
            )
        )

        check(
            "Profile segment reconciles",
            profile_json.get(
                "customer_segment"
            )
            ==
            str(
                source_row["customer_segment"]
            ),
            (
                f"API={profile_json.get('customer_segment')}, "
                f"Source={source_row['customer_segment']}"
            )
        )

    # ========================================================
    # CUSTOMERS
    # ========================================================

    print()
    print("VALIDATING CUSTOMERS")
    print("-" * 40)

    customers_response = client.get(
        "/customers",
        params={
            "page": 1,
            "page_size": 10
        }
    )

    check(
        "GET /customers returns 200",
        customers_response.status_code == 200,
        f"HTTP={customers_response.status_code}"
    )

    customers_json = customers_response.json()

    check(
        "Customers total is 5,000",
        customers_json.get(
            "total"
        )
        ==
        5000,
        (
            f"Total="
            f"{customers_json.get('total')}"
        )
    )

    check(
        "Customers page contains 10 records",
        len(
            customers_json.get(
                "customers",
                []
            )
        )
        ==
        10,
        (
            f"Records="
            f"{len(customers_json.get('customers', []))}"
        )
    )

    check(
        "Customers page size is 10",
        customers_json.get(
            "page_size"
        )
        ==
        10,
        (
            f"Page size="
            f"{customers_json.get('page_size')}"
        )
    )

    # ========================================================
    # JOURNEY
    # ========================================================

    print()
    print("VALIDATING JOURNEY")
    print("-" * 40)

    source_booking = journey_df[
        journey_df["booking_id"].astype(str)
        ==
        VALID_BOOKING
    ]

    journey_response = client.get(
        f"/journey/{VALID_BOOKING}"
    )

    check(
        "GET /journey/{booking_id} returns 200",
        journey_response.status_code == 200,
        f"HTTP={journey_response.status_code}"
    )

    journey_json = journey_response.json()

    check(
        "Journey booking ID is correct",
        journey_json.get(
            "booking_id"
        )
        ==
        VALID_BOOKING,
        (
            f"Booking="
            f"{journey_json.get('booking_id')}"
        )
    )

    if not source_booking.empty:

        booking_row = source_booking.iloc[0]

        check(
            "Journey duration reconciles",
            np.isclose(
                float(
                    journey_json[
                        "journey_duration_minutes"
                    ]
                ),
                float(
                    booking_row[
                        "journey_duration_minutes"
                    ]
                ),
                atol=0.01
            ),
            (
                f"API="
                f"{journey_json['journey_duration_minutes']}, "
                f"Source="
                f"{booking_row['journey_duration_minutes']}"
            )
        )

        check(
            "Journey friction reconciles",
            np.isclose(
                float(
                    journey_json[
                        "friction_score"
                    ]
                ),
                float(
                    booking_row[
                        "friction_score"
                    ]
                ),
                atol=0.01
            ),
            (
                f"API="
                f"{journey_json['friction_score']}, "
                f"Source="
                f"{booking_row['friction_score']}"
            )
        )

    # ========================================================
    # KPIs
    # ========================================================

    print()
    print("VALIDATING KPIS")
    print("-" * 40)

    kpi_response = client.get(
        "/kpis"
    )

    check(
        "GET /kpis returns 200",
        kpi_response.status_code == 200,
        f"HTTP={kpi_response.status_code}"
    )

    kpi_json = kpi_response.json()

    check(
        "KPI total is 22",
        kpi_json.get(
            "total_kpis"
        )
        ==
        22,
        (
            f"Total="
            f"{kpi_json.get('total_kpis')}"
        )
    )

    check(
        "KPI AVAILABLE count is 19",
        kpi_json.get(
            "available_kpis"
        )
        ==
        19,
        (
            f"Available="
            f"{kpi_json.get('available_kpis')}"
        )
    )

    check(
        "KPI PROXY count is 1",
        kpi_json.get(
            "proxy_kpis"
        )
        ==
        1,
        (
            f"Proxy="
            f"{kpi_json.get('proxy_kpis')}"
        )
    )

    check(
        "KPI unsupported count is 2",
        kpi_json.get(
            "unsupported_kpis"
        )
        ==
        2,
        (
            f"Unsupported="
            f"{kpi_json.get('unsupported_kpis')}"
        )
    )

    # ========================================================
    # UPLOAD
    # ========================================================

    print()
    print("VALIDATING UPLOAD")
    print("-" * 40)

    test_csv = (
        "customer_id,name\n"
        "INTEGRATION001,Test User\n"
        "INTEGRATION002,Second User\n"
    )

    upload_response = client.post(
        "/upload",
        files={
            "file": (
                "integration_test.csv",
                BytesIO(
                    test_csv.encode(
                        "utf-8"
                    )
                ),
                "text/csv"
            )
        }
    )

    check(
        "POST /upload returns 200",
        upload_response.status_code == 200,
        f"HTTP={upload_response.status_code}"
    )

    upload_json = upload_response.json()

    check(
        "Upload status is UPLOADED",
        upload_json.get(
            "status"
        )
        ==
        "UPLOADED",
        (
            f"Status="
            f"{upload_json.get('status')}"
        )
    )

    check(
        "Upload reports 2 rows",
        upload_json.get(
            "rows"
        )
        ==
        2,
        (
            f"Rows="
            f"{upload_json.get('rows')}"
        )
    )

    check(
        "Upload reports 2 columns",
        upload_json.get(
            "columns"
        )
        ==
        2,
        (
            f"Columns="
            f"{upload_json.get('columns')}"
        )
    )

    stored_filename = upload_json.get(
        "stored_filename"
    )

    stored_path = os.path.join(
        UPLOAD_DIR,
        str(
            stored_filename
        )
    )

    check(
        "Uploaded file exists",
        os.path.isfile(
            stored_path
        ),
        stored_path
    )

    # ========================================================
    # INVESTIGATION
    # ========================================================

    print()
    print("VALIDATING INVESTIGATION")
    print("-" * 40)

    investigation_response = client.post(
        "/investigate",
        json={
            "metric": "journey_duration_minutes",
            "threshold": 90
        }
    )

    check(
        "POST /investigate returns 200",
        investigation_response.status_code == 200,
        f"HTTP={investigation_response.status_code}"
    )

    investigation_json = (
        investigation_response.json()
    )

    investigation_result = (
        investigation_json.get(
            "result",
            {}
        )
    )

    check(
        "Investigation metric is correct",
        investigation_json.get(
            "metric"
        )
        ==
        "journey_duration_minutes",
        (
            f"Metric="
            f"{investigation_json.get('metric')}"
        )
    )

    check(
        "Investigation record count is 8,000",
        investigation_result.get(
            "record_count"
        )
        ==
        8000,
        (
            f"Count="
            f"{investigation_result.get('record_count')}"
        )
    )

    check(
        "Investigation threshold is 90",
        float(
            investigation_result.get(
                "threshold",
                -1
            )
        )
        ==
        90.0,
        (
            f"Threshold="
            f"{investigation_result.get('threshold')}"
        )
    )

    expected_flagged = int(
        (
            pd.to_numeric(
                journey_df[
                    "journey_duration_minutes"
                ],
                errors="coerce"
            )
            >=
            90
        ).sum()
    )

    check(
        "Investigation flagged count reconciles",
        investigation_result.get(
            "flagged_count"
        )
        ==
        expected_flagged,
        (
            f"Expected={expected_flagged}, "
            f"API={investigation_result.get('flagged_count')}"
        )
    )

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    print()
    print("VALIDATING ERROR HANDLING")
    print("-" * 40)

    unknown_customer_response = client.get(
        "/profile",
        params={
            "customer_id": UNKNOWN_CUSTOMER
        }
    )

    check(
        "Unknown customer returns 404",
        unknown_customer_response.status_code == 404,
        f"HTTP={unknown_customer_response.status_code}"
    )

    unknown_customer_json = (
        unknown_customer_response.json()
    )

    check(
        "Unknown customer error is standardized",
        set(
            [
                "error",
                "message",
                "status_code",
                "path"
            ]
        ).issubset(
            unknown_customer_json.keys()
        ),
        (
            f"Fields="
            f"{list(unknown_customer_json.keys())}"
        )
    )

    unknown_journey_response = client.get(
        f"/journey/{UNKNOWN_BOOKING}"
    )

    check(
        "Unknown journey returns 404",
        unknown_journey_response.status_code == 404,
        f"HTTP={unknown_journey_response.status_code}"
    )

    invalid_metric_response = client.post(
        "/investigate",
        json={
            "metric": "customer_happiness",
            "threshold": 50
        }
    )

    check(
        "Invalid investigation metric returns 400",
        invalid_metric_response.status_code == 400,
        (
            f"HTTP="
            f"{invalid_metric_response.status_code}"
        )
    )

    missing_profile_response = client.get(
        "/profile"
    )

    check(
        "Missing profile parameter returns 422",
        missing_profile_response.status_code == 422,
        (
            f"HTTP="
            f"{missing_profile_response.status_code}"
        )
    )

    unknown_route_response = client.get(
        "/route-that-does-not-exist"
    )

    check(
        "Unknown route returns 404",
        unknown_route_response.status_code == 404,
        (
            f"HTTP="
            f"{unknown_route_response.status_code}"
        )
    )

    unknown_route_json = (
        unknown_route_response.json()
    )

    check(
        "Unknown route error is standardized",
        set(
            [
                "error",
                "message",
                "status_code",
                "path"
            ]
        ).issubset(
            unknown_route_json.keys()
        ),
        (
            f"Fields="
            f"{list(unknown_route_json.keys())}"
        )
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
        "OpenAPI returns 200",
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

        expected_routes = {
            "/",
            "/health",
            "/profile",
            "/customers",
            "/journey/{booking_id}",
            "/kpis",
            "/upload",
            "/investigate",
        }

        missing_routes = (
            expected_routes
            -
            set(paths.keys())
        )

        check(
            "All production routes are registered",
            len(missing_routes) == 0,
            (
                "All routes present"
                if not missing_routes
                else f"Missing={sorted(missing_routes)}"
            )
        )

    except Exception as exc:

        check(
            "OpenAPI JSON is valid",
            False,
            str(exc)
        )

    # ========================================================
    # CROSS-ENDPOINT CONSISTENCY
    # ========================================================

    print()
    print("VALIDATING CROSS-ENDPOINT CONSISTENCY")
    print("-" * 40)

    profile_customer_id = (
        profile_json.get(
            "customer_id"
        )
    )

    journey_customer_id = (
        journey_json.get(
            "customer_id"
        )
    )

    check(
        "Profile customer identity is preserved",
        profile_customer_id
        ==
        VALID_CUSTOMER,
        (
            f"Profile={profile_customer_id}"
        )
    )

    if not source_booking.empty:

        booking_customer_id = str(
            booking_row[
                "customer_id"
            ]
        )

        check(
            "Journey customer matches source",
            journey_customer_id
            ==
            booking_customer_id,
            (
                f"Journey={journey_customer_id}, "
                f"Source={booking_customer_id}"
            )
        )

    check(
        "API KPI count matches source KPI count",
        kpi_json.get(
            "total_kpis"
        )
        ==
        len(kpi_df),
        (
            f"API={kpi_json.get('total_kpis')}, "
            f"Source={len(kpi_df)}"
        )
    )

    # ========================================================
    # CLEAN UP TEST UPLOAD
    # ========================================================

    print()
    print("CLEANING INTEGRATION TEST FILE")
    print("-" * 40)

    if os.path.isfile(
        stored_path
    ):

        try:

            os.remove(
                stored_path
            )

            check(
                "Integration test upload cleaned",
                True,
                stored_filename
            )

        except OSError as exc:

            check(
                "Integration test upload cleaned",
                False,
                str(exc)
            )

    else:

        check(
            "Integration test upload cleaned",
            True,
            "No test file remained"
        )

    # ========================================================
    # SAVE VALIDATION REPORT
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

    total_checks = len(
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
        total_checks
        -
        passed
    )

    pass_rate = round(
        (
            passed
            /
            total_checks
            *
            100
        ),
        2
    )

    print()
    print("=" * 60)
    print("DAY 8 FULL API VALIDATION SUMMARY")
    print("=" * 60)

    print(
        f"Total checks: {total_checks}"
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
            "DAY 8 BRICK 8.10 — FULL API: PASSED"
        )
        print("=" * 60)

        print()
        print(
            "The complete Journey Forensics API "
            "has passed end-to-end integration validation."
        )

        print()
        print(
            "Validated:"
        )

        print(
            "Root, Health, Profile, Customers, "
            "Journey, KPIs, Upload, Investigation, "
            "Error Handling, OpenAPI, and Cross-endpoint consistency."
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
        "DAY 8 BRICK 8.10 — FULL API: FAILED"
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