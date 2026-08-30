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
    sys.path.insert(
        0,
        BASE_DIR
    )


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

VALID_CUSTOMER_ID = "C004781"

INVALID_CUSTOMER_ID = "C999999"

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day8_profile_validation_report.csv"
)


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
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 8 — /PROFILE ENDPOINT VALIDATION")
    print("=" * 60)

    # ========================================================
    # FILE VALIDATION
    # ========================================================

    check(
        "Profile dataset exists",
        os.path.isfile(
            PROFILE_FILE
        ),
        PROFILE_FILE
    )

    if not os.path.isfile(
        PROFILE_FILE
    ):
        return 1

    # ========================================================
    # LOAD SOURCE
    # ========================================================

    try:

        source = pd.read_csv(
            PROFILE_FILE
        )

        check(
            "Profile dataset loads",
            True,
            f"Rows={len(source):,}"
        )

    except Exception as exc:

        check(
            "Profile dataset loads",
            False,
            str(exc)
        )

        return 1

    # ========================================================
    # SOURCE CUSTOMER
    # ========================================================

    source_customer = source[
        source[
            "customer_id"
        ].astype(str)
        ==
        VALID_CUSTOMER_ID
    ]

    check(
        "Validation customer exists in source",
        len(source_customer) == 1,
        f"Matches={len(source_customer)}"
    )

    if source_customer.empty:
        return 1

    source_row = source_customer.iloc[0]

    # ========================================================
    # FASTAPI TEST CLIENT
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
    # VALID CUSTOMER
    # ========================================================

    print()
    print("VALIDATING REAL CUSTOMER")
    print("-" * 40)

    response = client.get(
        "/profile",
        params={
            "customer_id": VALID_CUSTOMER_ID
        }
    )

    check(
        "GET /profile returns 200 for valid customer",
        response.status_code == 200,
        f"HTTP {response.status_code}"
    )

    # ========================================================
    # JSON RESPONSE
    # ========================================================

    try:

        response_json = response.json()

        check(
            "Profile response is valid JSON",
            isinstance(
                response_json,
                dict
            ),
            "JSON object received"
        )

    except Exception as exc:

        check(
            "Profile response is valid JSON",
            False,
            str(exc)
        )

        response_json = {}

    # ========================================================
    # REQUIRED FIELDS
    # ========================================================

    required_fields = [

        "customer_id",

        "total_bookings",

        "total_revenue",

        "average_booking_value",

        "recency_days",

        "booking_frequency",

        "repeat_booking_flag",

        "customer_segment",

        "segment_reason",

        "cohort_month",

        "cluster_id",

        "complaint_segment_status",

        "segmentation_status",

        "segmentation_method"
    ]

    missing_fields = [

        field
        for field in required_fields
        if field not in response_json
    ]

    check(
        "Profile response contains required fields",
        len(missing_fields) == 0,
        (
            "All required fields present"
            if not missing_fields
            else f"Missing={missing_fields}"
        )
    )

    # ========================================================
    # CUSTOMER ID
    # ========================================================

    check(
        "Returned customer ID is correct",
        response_json.get(
            "customer_id"
        )
        ==
        VALID_CUSTOMER_ID,
        (
            f"Returned="
            f"{response_json.get('customer_id')}"
        )
    )

    # ========================================================
    # NUMERIC RECONCILIATION
    # ========================================================

    def numeric_equal(
        response_value,
        source_value,
        tolerance=0.01
    ):

        try:

            return abs(
                float(response_value)
                -
                float(source_value)
            ) <= tolerance

        except (
            TypeError,
            ValueError
        ):

            return False

    check(
        "Total bookings matches source",
        numeric_equal(
            response_json.get(
                "total_bookings"
            ),
            source_row[
                "total_bookings"
            ]
        ),
        (
            f"API={response_json.get('total_bookings')}, "
            f"Source={source_row['total_bookings']}"
        )
    )

    check(
        "Total revenue matches source",
        numeric_equal(
            response_json.get(
                "total_revenue"
            ),
            source_row[
                "total_revenue"
            ]
        ),
        (
            f"API={response_json.get('total_revenue')}, "
            f"Source={source_row['total_revenue']}"
        )
    )

    check(
        "Average booking value matches source",
        numeric_equal(
            response_json.get(
                "average_booking_value"
            ),
            source_row[
                "average_booking_value"
            ]
        ),
        (
            f"API={response_json.get('average_booking_value')}, "
            f"Source={source_row['average_booking_value']}"
        )
    )

    check(
        "Recency matches source",
        numeric_equal(
            response_json.get(
                "recency_days"
            ),
            source_row[
                "recency_days"
            ]
        ),
        (
            f"API={response_json.get('recency_days')}, "
            f"Source={source_row['recency_days']}"
        )
    )

    check(
        "Booking frequency matches source",
        numeric_equal(
            response_json.get(
                "booking_frequency"
            ),
            source_row[
                "booking_frequency"
            ],
            tolerance=0.0001
        ),
        (
            f"API={response_json.get('booking_frequency')}, "
            f"Source={source_row['booking_frequency']}"
        )
    )

    check(
        "Repeat booking flag matches source",
        int(
            response_json.get(
                "repeat_booking_flag"
            )
        )
        ==
        int(
            source_row[
                "repeat_booking_flag"
            ]
        ),
        (
            f"API={response_json.get('repeat_booking_flag')}, "
            f"Source={source_row['repeat_booking_flag']}"
        )
    )

    check(
        "Customer segment matches source",
        response_json.get(
            "customer_segment"
        )
        ==
        str(
            source_row[
                "customer_segment"
            ]
        ),
        (
            f"API={response_json.get('customer_segment')}, "
            f"Source={source_row['customer_segment']}"
        )
    )

    check(
        "Cohort month matches source",
        response_json.get(
            "cohort_month"
        )
        ==
        str(
            source_row[
                "cohort_month"
            ]
        ),
        (
            f"API={response_json.get('cohort_month')}, "
            f"Source={source_row['cohort_month']}"
        )
    )

    check(
        "Segmentation status is READY",
        response_json.get(
            "segmentation_status"
        )
        ==
        "READY",
        (
            f"Status="
            f"{response_json.get('segmentation_status')}"
        )
    )

    check(
        "Complaint limitation is preserved",
        response_json.get(
            "complaint_segment_status"
        )
        ==
        "NOT_SUPPORTED",
        (
            f"Status="
            f"{response_json.get('complaint_segment_status')}"
        )
    )

    # ========================================================
    # UNKNOWN CUSTOMER
    # ========================================================

    print()
    print("VALIDATING UNKNOWN CUSTOMER")
    print("-" * 40)

    invalid_response = client.get(
        "/profile",
        params={
            "customer_id": INVALID_CUSTOMER_ID
        }
    )

    check(
        "GET /profile returns 404 for unknown customer",
        invalid_response.status_code == 404,
        f"HTTP {invalid_response.status_code}"
    )

    try:

        invalid_json = invalid_response.json()

        detail = str(
            invalid_json.get(
                "detail",
                ""
            )
        )

        check(
            "404 response contains useful error detail",
            INVALID_CUSTOMER_ID in detail,
            detail
        )

    except Exception as exc:

        check(
            "404 response contains useful error detail",
            False,
            str(exc)
        )

    # ========================================================
    # MISSING PARAMETER
    # ========================================================

    print()
    print("VALIDATING REQUEST PARAMETERS")
    print("-" * 40)

    missing_parameter_response = client.get(
        "/profile"
    )

    check(
        "Missing customer_id returns 422",
        missing_parameter_response.status_code == 422,
        (
            f"HTTP "
            f"{missing_parameter_response.status_code}"
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
        "OpenAPI specification is available",
        openapi_response.status_code == 200,
        f"HTTP {openapi_response.status_code}"
    )

    try:

        openapi = openapi_response.json()

        profile_definition = (
            openapi
            .get(
                "paths",
                {}
            )
            .get(
                "/profile",
                {}
            )
            .get(
                "get"
            )
        )

        check(
            "OpenAPI contains GET /profile",
            profile_definition is not None,
            "GET /profile registered"
        )

    except Exception as exc:

        check(
            "OpenAPI contains GET /profile",
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
        (
            passed
            /
            total
        )
        *
        100,
        2
    )

    print()
    print("=" * 60)
    print("DAY 8 /PROFILE VALIDATION SUMMARY")
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
            "DAY 8 BRICK 8.3 — /PROFILE: PASSED"
        )
        print("=" * 60)

        print()
        print(
            "The /profile endpoint is validated "
            "against the Day 7 final customer "
            "segmentation dataset."
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
        "DAY 8 BRICK 8.3 — /PROFILE: FAILED"
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