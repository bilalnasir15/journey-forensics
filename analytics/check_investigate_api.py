import os
import sys

import numpy as np
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

PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

JOURNEY_FILE = os.path.join(
    PROCESSED_DIR,
    "customer_journey_features.csv"
)

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day8_investigate_validation_report.csv"
)

TEST_METRIC = "journey_duration_minutes"
TEST_THRESHOLD = 90.0

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
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 8 — /INVESTIGATE ENDPOINT VALIDATION")
    print("=" * 60)

    # ========================================================
    # SOURCE DATA
    # ========================================================

    check(
        "Journey dataset exists",
        os.path.isfile(JOURNEY_FILE),
        JOURNEY_FILE
    )

    if not os.path.isfile(JOURNEY_FILE):
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
    # SOURCE METRIC
    # ========================================================

    check(
        "Investigation metric exists in source",
        TEST_METRIC in source.columns,
        TEST_METRIC
    )

    if TEST_METRIC not in source.columns:
        return 1

    source_values = pd.to_numeric(
        source[TEST_METRIC],
        errors="coerce"
    ).dropna()

    check(
        "Investigation metric contains numeric values",
        len(source_values) > 0,
        (
            f"Valid values="
            f"{len(source_values):,}"
        )
    )

    # ========================================================
    # INDEPENDENT CALCULATIONS
    # ========================================================

    source_count = int(
        source_values.count()
    )

    source_mean = float(
        source_values.mean()
    )

    source_median = float(
        source_values.median()
    )

    source_std = float(
        source_values.std(
            ddof=1
        )
    ) if source_count > 1 else 0.0

    source_min = float(
        source_values.min()
    )

    source_max = float(
        source_values.max()
    )

    source_flagged_count = int(
        (
            source_values
            >=
            TEST_THRESHOLD
        ).sum()
    )

    source_flagged_percentage = (
        source_flagged_count
        /
        source_count
        *
        100
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
    # VALID INVESTIGATION REQUEST
    # ========================================================

    print()
    print("VALIDATING REAL INVESTIGATION")
    print("-" * 40)

    response = client.post(
        "/investigate",
        json={
            "metric": TEST_METRIC,
            "threshold": TEST_THRESHOLD
        }
    )

    check(
        "Valid investigation returns 200",
        response.status_code == 200,
        f"HTTP {response.status_code}"
    )

    try:

        response_json = response.json()

        check(
            "Investigation response is valid JSON",
            isinstance(
                response_json,
                dict
            ),
            "JSON object received"
        )

    except Exception as exc:

        check(
            "Investigation response is valid JSON",
            False,
            str(exc)
        )

        return 1

    # ========================================================
    # REQUIRED TOP-LEVEL FIELDS
    # ========================================================

    required_fields = {
        "metric",
        "status",
        "message",
        "result"
    }

    missing_fields = (
        required_fields
        -
        set(response_json.keys())
    )

    check(
        "Investigation response has required fields",
        len(missing_fields) == 0,
        (
            "All required fields present"
            if not missing_fields
            else f"Missing={sorted(missing_fields)}"
        )
    )

    # ========================================================
    # BASIC RESPONSE
    # ========================================================

    check(
        "Returned metric is correct",
        response_json.get(
            "metric"
        )
        ==
        TEST_METRIC,
        (
            f"Metric="
            f"{response_json.get('metric')}"
        )
    )

    check(
        "Investigation status is valid",
        response_json.get(
            "status"
        )
        ==
        "THRESHOLD_MATCHES_FOUND",
        (
            f"Status="
            f"{response_json.get('status')}"
        )
    )

    result = response_json.get(
        "result"
    )

    check(
        "Investigation result is an object",
        isinstance(
            result,
            dict
        ),
        "Result object received"
    )

    if not isinstance(
        result,
        dict
    ):

        result = {}

    # ========================================================
    # REQUIRED RESULT FIELDS
    # ========================================================

    required_result_fields = {
        "metric",
        "source_column",
        "record_count",
        "mean",
        "median",
        "standard_deviation",
        "minimum",
        "maximum",
        "threshold",
        "threshold_operator",
        "flagged_count",
        "flagged_percentage",
        "top_flagged_journeys"
    }

    missing_result_fields = (
        required_result_fields
        -
        set(result.keys())
    )

    check(
        "Investigation result has required fields",
        len(missing_result_fields) == 0,
        (
            "All required result fields present"
            if not missing_result_fields
            else f"Missing={sorted(missing_result_fields)}"
        )
    )

    # ========================================================
    # SOURCE COLUMN
    # ========================================================

    check(
        "Source column is correct",
        result.get(
            "source_column"
        )
        ==
        TEST_METRIC,
        (
            f"Source column="
            f"{result.get('source_column')}"
        )
    )

    # ========================================================
    # COUNT RECONCILIATION
    # ========================================================

    check(
        "Record count matches source",
        result.get(
            "record_count"
        )
        ==
        source_count,
        (
            f"Expected={source_count}, "
            f"API={result.get('record_count')}"
        )
    )

    # ========================================================
    # NUMERIC COMPARISON
    # ========================================================

    def close(
        api_value,
        expected_value,
        tolerance=0.0001
    ):

        try:

            return np.isclose(
                float(api_value),
                float(expected_value),
                rtol=1e-6,
                atol=tolerance
            )

        except (
            TypeError,
            ValueError
        ):

            return False

    check(
        "Mean matches source",
        close(
            result.get("mean"),
            source_mean
        ),
        (
            f"Expected={source_mean:.4f}, "
            f"API={result.get('mean')}"
        )
    )

    check(
        "Median matches source",
        close(
            result.get("median"),
            source_median
        ),
        (
            f"Expected={source_median:.4f}, "
            f"API={result.get('median')}"
        )
    )

    check(
        "Standard deviation matches source",
        close(
            result.get(
                "standard_deviation"
            ),
            source_std
        ),
        (
            f"Expected={source_std:.4f}, "
            f"API={result.get('standard_deviation')}"
        )
    )

    check(
        "Minimum matches source",
        close(
            result.get("minimum"),
            source_min
        ),
        (
            f"Expected={source_min:.4f}, "
            f"API={result.get('minimum')}"
        )
    )

    check(
        "Maximum matches source",
        close(
            result.get("maximum"),
            source_max
        ),
        (
            f"Expected={source_max:.4f}, "
            f"API={result.get('maximum')}"
        )
    )

    # ========================================================
    # THRESHOLD
    # ========================================================

    check(
        "Threshold matches request",
        close(
            result.get("threshold"),
            TEST_THRESHOLD
        ),
        (
            f"Expected={TEST_THRESHOLD}, "
            f"API={result.get('threshold')}"
        )
    )

    check(
        "Threshold operator is >= ",
        result.get(
            "threshold_operator"
        )
        ==
        ">=",
        (
            f"Operator="
            f"{result.get('threshold_operator')}"
        )
    )

    check(
        "Flagged count matches source",
        result.get(
            "flagged_count"
        )
        ==
        source_flagged_count,
        (
            f"Expected={source_flagged_count}, "
            f"API={result.get('flagged_count')}"
        )
    )

    check(
        "Flagged percentage matches source",
        close(
            result.get(
                "flagged_percentage"
            ),
            source_flagged_percentage,
            tolerance=0.01
        ),
        (
            f"Expected={source_flagged_percentage:.2f}, "
            f"API={result.get('flagged_percentage')}"
        )
    )

    # ========================================================
    # TOP FLAGGED JOURNEYS
    # ========================================================

    top_flagged = result.get(
        "top_flagged_journeys"
    )

    check(
        "Top flagged journeys is a list",
        isinstance(
            top_flagged,
            list
        ),
        (
            f"Type="
            f"{type(top_flagged).__name__}"
        )
    )

    check(
        "Top flagged journeys contains at most 10 records",
        isinstance(
            top_flagged,
            list
        )
        and
        len(top_flagged) <= 10,
        (
            f"Records="
            f"{len(top_flagged) if isinstance(top_flagged, list) else 0}"
        )
    )

    # --------------------------------------------------------
    # Verify every returned flagged record
    # --------------------------------------------------------

    invalid_top_records = 0

    if isinstance(
        top_flagged,
        list
    ):

        for item in top_flagged:

            if not isinstance(
                item,
                dict
            ):

                invalid_top_records += 1
                continue

            if not {
                "booking_id",
                "customer_id",
                "value"
            }.issubset(
                set(item.keys())
            ):

                invalid_top_records += 1
                continue

            try:

                if float(
                    item["value"]
                ) < TEST_THRESHOLD:

                    invalid_top_records += 1

            except (
                TypeError,
                ValueError
            ):

                invalid_top_records += 1

    check(
        "Top flagged journey records are valid",
        invalid_top_records == 0,
        (
            f"Invalid records="
            f"{invalid_top_records}"
        )
    )

    # ========================================================
    # TOP RECORD ORDER
    # ========================================================

    values = []

    if isinstance(
        top_flagged,
        list
    ):

        for item in top_flagged:

            try:

                values.append(
                    float(
                        item["value"]
                    )
                )

            except (
                KeyError,
                TypeError,
                ValueError
            ):

                pass

    check(
        "Top flagged journeys are sorted descending",
        values
        ==
        sorted(
            values,
            reverse=True
        ),
        (
            f"Values={values}"
        )
    )

    # ========================================================
    # NO-THRESHOLD REQUEST
    # ========================================================

    print()
    print("VALIDATING NO-THRESHOLD INVESTIGATION")
    print("-" * 40)

    no_threshold_response = client.post(
        "/investigate",
        json={
            "metric": TEST_METRIC
        }
    )

    check(
        "Investigation without threshold returns 200",
        no_threshold_response.status_code == 200,
        (
            f"HTTP="
            f"{no_threshold_response.status_code}"
        )
    )

    try:

        no_threshold_json = (
            no_threshold_response.json()
        )

        check(
            "No-threshold status is ANALYZED",
            no_threshold_json.get(
                "status"
            )
            ==
            "ANALYZED",
            (
                f"Status="
                f"{no_threshold_json.get('status')}"
            )
        )

    except Exception as exc:

        check(
            "No-threshold response is valid JSON",
            False,
            str(exc)
        )

    # ========================================================
    # INVALID METRIC
    # ========================================================

    print()
    print("VALIDATING INVALID METRIC")
    print("-" * 40)

    invalid_response = client.post(
        "/investigate",
        json={
            "metric": INVALID_METRIC,
            "threshold": 50
        }
    )

    check(
        "Invalid metric returns 400",
        invalid_response.status_code == 400,
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
            "Invalid metric error contains metric name",
            INVALID_METRIC in detail,
            detail
        )

        check(
            "Invalid metric error lists supported metrics",
            "Supported metrics" in detail,
            detail
        )

    except Exception as exc:

        check(
            "Invalid metric response is valid JSON",
            False,
            str(exc)
        )

    # ========================================================
    # EMPTY METRIC
    # ========================================================

    print()
    print("VALIDATING EMPTY METRIC")
    print("-" * 40)

    empty_metric_response = client.post(
        "/investigate",
        json={
            "metric": "",
            "threshold": 50
        }
    )

    check(
        "Empty metric returns 422",
        empty_metric_response.status_code == 422,
        (
            f"HTTP="
            f"{empty_metric_response.status_code}"
        )
    )

    # ========================================================
    # MISSING REQUEST BODY
    # ========================================================

    missing_body_response = client.post(
        "/investigate"
    )

    check(
        "Missing request body returns 422",
        missing_body_response.status_code == 422,
        (
            f"HTTP="
            f"{missing_body_response.status_code}"
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
        (
            f"HTTP="
            f"{openapi_response.status_code}"
        )
    )

    try:

        openapi = (
            openapi_response.json()
        )

        investigate_definition = (
            openapi
            .get(
                "paths",
                {}
            )
            .get(
                "/investigate",
                {}
            )
            .get(
                "post"
            )
        )

        check(
            "OpenAPI contains POST /investigate",
            investigate_definition is not None,
            "POST /investigate registered"
        )

    except Exception as exc:

        check(
            "OpenAPI contains POST /investigate",
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
    print("DAY 8 /INVESTIGATE VALIDATION SUMMARY")
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
            "DAY 8 BRICK 8.8 — /INVESTIGATE: PASSED"
        )
        print("=" * 60)

        print()
        print(
            "Investigation calculations, threshold analysis, "
            "flagged journeys, validation, error handling, "
            "Pydantic request/response behavior, and OpenAPI "
            "registration are independently validated."
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
        "DAY 8 BRICK 8.8 — /INVESTIGATE: FAILED"
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