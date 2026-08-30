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

JOURNEY_FILE = os.path.join(
    PROCESSED_DIR,
    "customer_journey_features.csv"
)

VALID_BOOKING_ID = "B007998"

INVALID_BOOKING_ID = "B999999"

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day8_journey_validation_report.csv"
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
    print("DAY 8 — /JOURNEY ENDPOINT VALIDATION")
    print("=" * 60)

    # ========================================================
    # SOURCE DATA
    # ========================================================

    check(
        "Journey dataset exists",
        os.path.isfile(
            JOURNEY_FILE
        ),
        JOURNEY_FILE
    )

    if not os.path.isfile(
        JOURNEY_FILE
    ):
        return 1

    try:

        source = pd.read_csv(
            JOURNEY_FILE
        )

        check(
            "Journey dataset loads",
            True,
            f"Rows={len(source):,}"
        )

    except Exception as exc:

        check(
            "Journey dataset loads",
            False,
            str(exc)
        )

        return 1

    # ========================================================
    # SOURCE BOOKING
    # ========================================================

    source_booking = source[
        source[
            "booking_id"
        ].astype(str)
        ==
        VALID_BOOKING_ID
    ]

    check(
        "Validation booking exists in source",
        len(source_booking) == 1,
        f"Matches={len(source_booking)}"
    )

    if source_booking.empty:
        return 1

    source_row = source_booking.iloc[0]

    # ========================================================
    # SOURCE UNIQUENESS
    # ========================================================

    check(
        "Booking IDs are unique in journey dataset",
        source[
            "booking_id"
        ]
        .astype(str)
        .is_unique,
        (
            f"Duplicates="
            f"{source['booking_id'].duplicated().sum()}"
        )
    )

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
    # VALID JOURNEY
    # ========================================================

    print()
    print("VALIDATING REAL JOURNEY")
    print("-" * 40)

    response = client.get(
        f"/journey/{VALID_BOOKING_ID}"
    )

    check(
        "GET /journey returns 200 for valid booking",
        response.status_code == 200,
        f"HTTP {response.status_code}"
    )

    # ========================================================
    # JSON
    # ========================================================

    try:

        response_json = response.json()

        check(
            "Journey response is valid JSON",
            isinstance(
                response_json,
                dict
            ),
            "JSON object received"
        )

    except Exception as exc:

        check(
            "Journey response is valid JSON",
            False,
            str(exc)
        )

        response_json = {}

    # ========================================================
    # REQUIRED FIELDS
    # ========================================================

    required_fields = [

        "customer_id",
        "booking_id",
        "trip_id",
        "booking_status",
        "booking_amount",

        "payment_attempts",
        "failed_payments",
        "successful_payments",
        "retry_count",
        "payment_success_rate",

        "total_events",
        "search_events",
        "view_trip_events",
        "booking_started_events",
        "booking_created_events",
        "payment_started_events",
        "payment_failed_events",
        "payment_retry_events",
        "payment_completed_events",
        "booking_confirmed_events",

        "journey_duration_minutes",
        "payment_duration_minutes",

        "friction_score",
        "risk_level",
        "anomaly_summary"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in response_json
    ]

    check(
        "Journey response contains required fields",
        len(missing_fields) == 0,
        (
            "All required fields present"
            if not missing_fields
            else f"Missing={missing_fields}"
        )
    )

    # ========================================================
    # BASIC IDENTITY
    # ========================================================

    check(
        "Returned booking ID is correct",
        response_json.get(
            "booking_id"
        )
        ==
        VALID_BOOKING_ID,
        (
            f"Returned="
            f"{response_json.get('booking_id')}"
        )
    )

    # ========================================================
    # RECONCILIATION HELPER
    # ========================================================

    def numeric_equal(
        api_value,
        source_value,
        tolerance=0.01
    ):

        try:

            return abs(
                float(api_value)
                -
                float(source_value)
            ) <= tolerance

        except (
            TypeError,
            ValueError
        ):

            return False

    # ========================================================
    # SOURCE RECONCILIATION
    # ========================================================

    numeric_columns = [

        "booking_amount",
        "payment_attempts",
        "failed_payments",
        "successful_payments",
        "retry_count",
        "payment_success_rate",
        "total_events",
        "search_events",
        "view_trip_events",
        "booking_started_events",
        "booking_created_events",
        "payment_started_events",
        "payment_failed_events",
        "payment_retry_events",
        "payment_completed_events",
        "booking_confirmed_events",
        "journey_duration_minutes",
        "payment_duration_minutes",
        "friction_score"
    ]

    for column in numeric_columns:

        tolerance = (
            0.0001
            if column
            ==
            "payment_success_rate"
            else 0.01
        )

        check(
            f"{column} matches source",
            numeric_equal(
                response_json.get(column),
                source_row[column],
                tolerance
            ),
            (
                f"API={response_json.get(column)}, "
                f"Source={source_row[column]}"
            )
        )

    # ========================================================
    # STRING RECONCILIATION
    # ========================================================

    string_columns = [

        "customer_id",
        "trip_id",
        "booking_status",
        "risk_level",
        "anomaly_summary"
    ]

    for column in string_columns:

        source_value = source_row[column]

        if pd.isna(
            source_value
        ):
            expected = None
        else:
            expected = str(
                source_value
            )

        actual = response_json.get(
            column
        )

        check(
            f"{column} matches source",
            actual == expected,
            (
                f"API={actual}, "
                f"Source={expected}"
            )
        )

    # ========================================================
    # RISK / FRICTION
    # ========================================================

    check(
        "Friction score is between 0 and 100",
        (
            response_json.get(
                "friction_score"
            ) is not None
            and
            0
            <=
            float(
                response_json[
                    "friction_score"
                ]
            )
            <=
            100
        ),
        (
            f"Score="
            f"{response_json.get('friction_score')}"
        )
    )

    valid_risk_levels = {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    }

    check(
        "Risk level is valid",
        response_json.get(
            "risk_level"
        )
        in valid_risk_levels,
        (
            f"Risk="
            f"{response_json.get('risk_level')}"
        )
    )

    # ========================================================
    # UNKNOWN JOURNEY
    # ========================================================

    print()
    print("VALIDATING UNKNOWN JOURNEY")
    print("-" * 40)

    invalid_response = client.get(
        f"/journey/{INVALID_BOOKING_ID}"
    )

    check(
        "Unknown journey returns 404",
        invalid_response.status_code == 404,
        (
            f"HTTP="
            f"{invalid_response.status_code}"
        )
    )

    try:

        invalid_json = (
            invalid_response.json()
        )

        detail = str(
            invalid_json.get(
                "detail",
                ""
            )
        )

        check(
            "404 response contains useful error detail",
            INVALID_BOOKING_ID in detail,
            detail
        )

    except Exception as exc:

        check(
            "404 response contains useful error detail",
            False,
            str(exc)
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

        openapi = (
            openapi_response.json()
        )

        journey_definition = (
            openapi
            .get(
                "paths",
                {}
            )
            .get(
                "/journey/{booking_id}",
                {}
            )
            .get(
                "get"
            )
        )

        check(
            "OpenAPI contains GET /journey/{booking_id}",
            journey_definition is not None,
            "Journey endpoint registered"
        )

    except Exception as exc:

        check(
            "OpenAPI contains GET /journey/{booking_id}",
            False,
            str(exc)
        )

    # ========================================================
    # SAVE
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
    print("DAY 8 /JOURNEY VALIDATION SUMMARY")
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
            "DAY 8 BRICK 8.5 — /JOURNEY: PASSED"
        )
        print("=" * 60)

        print()
        print(
            "Journey lookup, forensic metrics, "
            "risk/friction values, source reconciliation, "
            "404 handling, and OpenAPI registration "
            "are independently validated."
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
        "DAY 8 BRICK 8.5 — /JOURNEY: FAILED"
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