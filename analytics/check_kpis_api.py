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

KPI_FILE = os.path.join(
    PROCESSED_DIR,
    "day5_kpi_report.csv"
)

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day8_kpis_validation_report.csv"
)

EXPECTED_TOTAL = 22
EXPECTED_AVAILABLE = 19
EXPECTED_PROXY = 1
EXPECTED_UNSUPPORTED = 2


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
    print("DAY 8 — /KPIS ENDPOINT VALIDATION")
    print("=" * 60)

    # ========================================================
    # SOURCE FILE
    # ========================================================

    check(
        "KPI source file exists",
        os.path.isfile(KPI_FILE),
        KPI_FILE
    )

    if not os.path.isfile(KPI_FILE):
        return 1

    try:

        source = pd.read_csv(
            KPI_FILE
        )

        check(
            "KPI source file loads",
            True,
            f"Rows={len(source):,}"
        )

    except Exception as exc:

        check(
            "KPI source file loads",
            False,
            str(exc)
        )

        return 1

    # ========================================================
    # SOURCE STRUCTURE
    # ========================================================

    required_source_columns = {
        "kpi_name",
        "value",
        "unit",
        "status"
    }

    missing_source_columns = (
        required_source_columns
        -
        set(source.columns)
    )

    check(
        "KPI source columns exist",
        len(missing_source_columns) == 0,
        (
            "All required columns present"
            if not missing_source_columns
            else f"Missing={sorted(missing_source_columns)}"
        )
    )

    # ========================================================
    # SOURCE COUNTS
    # ========================================================

    actual_source_total = len(
        source
    )

    actual_available = int(
        source[
            "status"
        ]
        .eq("AVAILABLE")
        .sum()
    )

    actual_proxy = int(
        source[
            "status"
        ]
        .eq("PROXY")
        .sum()
    )

    actual_unsupported = int(
        source[
            "status"
        ]
        .eq("NOT_SUPPORTED")
        .sum()
    )

    check(
        "Source contains 22 KPIs",
        actual_source_total == EXPECTED_TOTAL,
        (
            f"Expected={EXPECTED_TOTAL}, "
            f"Actual={actual_source_total}"
        )
    )

    check(
        "Source contains 19 AVAILABLE KPIs",
        actual_available == EXPECTED_AVAILABLE,
        (
            f"Expected={EXPECTED_AVAILABLE}, "
            f"Actual={actual_available}"
        )
    )

    check(
        "Source contains 1 PROXY KPI",
        actual_proxy == EXPECTED_PROXY,
        (
            f"Expected={EXPECTED_PROXY}, "
            f"Actual={actual_proxy}"
        )
    )

    check(
        "Source contains 2 unsupported KPIs",
        actual_unsupported == EXPECTED_UNSUPPORTED,
        (
            f"Expected={EXPECTED_UNSUPPORTED}, "
            f"Actual={actual_unsupported}"
        )
    )

    # ========================================================
    # KPI NAME UNIQUENESS
    # ========================================================

    check(
        "KPI names are unique",
        source[
            "kpi_name"
        ]
        .astype(str)
        .is_unique,
        (
            f"Duplicates="
            f"{source['kpi_name'].duplicated().sum()}"
        )
    )

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
    # GET /KPIS
    # ========================================================

    print()
    print("VALIDATING GET /KPIS")
    print("-" * 40)

    response = client.get(
        "/kpis"
    )

    check(
        "GET /kpis returns 200",
        response.status_code == 200,
        f"HTTP {response.status_code}"
    )

    # ========================================================
    # JSON RESPONSE
    # ========================================================

    try:

        response_json = response.json()

        check(
            "KPI response is valid JSON",
            isinstance(
                response_json,
                dict
            ),
            "JSON object received"
        )

    except Exception as exc:

        check(
            "KPI response is valid JSON",
            False,
            str(exc)
        )

        return 1

    # ========================================================
    # RESPONSE STRUCTURE
    # ========================================================

    required_response_fields = {
        "total_kpis",
        "available_kpis",
        "proxy_kpis",
        "unsupported_kpis",
        "kpis"
    }

    missing_response_fields = (
        required_response_fields
        -
        set(response_json.keys())
    )

    check(
        "KPI response contains required fields",
        len(missing_response_fields) == 0,
        (
            "All required fields present"
            if not missing_response_fields
            else f"Missing={sorted(missing_response_fields)}"
        )
    )

    # ========================================================
    # API COUNTS
    # ========================================================

    api_total = response_json.get(
        "total_kpis"
    )

    api_available = response_json.get(
        "available_kpis"
    )

    api_proxy = response_json.get(
        "proxy_kpis"
    )

    api_unsupported = response_json.get(
        "unsupported_kpis"
    )

    check(
        "API total KPI count is 22",
        api_total == EXPECTED_TOTAL,
        (
            f"Expected={EXPECTED_TOTAL}, "
            f"API={api_total}"
        )
    )

    check(
        "API AVAILABLE count is 19",
        api_available == EXPECTED_AVAILABLE,
        (
            f"Expected={EXPECTED_AVAILABLE}, "
            f"API={api_available}"
        )
    )

    check(
        "API PROXY count is 1",
        api_proxy == EXPECTED_PROXY,
        (
            f"Expected={EXPECTED_PROXY}, "
            f"API={api_proxy}"
        )
    )

    check(
        "API unsupported count is 2",
        api_unsupported == EXPECTED_UNSUPPORTED,
        (
            f"Expected={EXPECTED_UNSUPPORTED}, "
            f"API={api_unsupported}"
        )
    )

    # ========================================================
    # KPI RECORDS
    # ========================================================

    api_kpis = response_json.get(
        "kpis",
        []
    )

    check(
        "API returns 22 KPI records",
        len(api_kpis) == EXPECTED_TOTAL,
        (
            f"Expected={EXPECTED_TOTAL}, "
            f"Records={len(api_kpis)}"
        )
    )

    # ========================================================
    # KPI OBJECT STRUCTURE
    # ========================================================

    required_kpi_fields = {
        "kpi_name",
        "value",
        "unit",
        "status",
        "definition"
    }

    invalid_kpi_objects = 0

    for kpi in api_kpis:

        if not isinstance(
            kpi,
            dict
        ):

            invalid_kpi_objects += 1
            continue

        if not required_kpi_fields.issubset(
            set(kpi.keys())
        ):

            invalid_kpi_objects += 1

    check(
        "All KPI records have required fields",
        invalid_kpi_objects == 0,
        (
            f"Invalid records="
            f"{invalid_kpi_objects}"
        )
    )

    # ========================================================
    # KPI NAME SET
    # ========================================================

    source_names = set(
        source[
            "kpi_name"
        ]
        .astype(str)
    )

    api_names = set(
        str(
            kpi["kpi_name"]
        )
        for kpi in api_kpis
    )

    check(
        "API KPI names match source",
        api_names == source_names,
        (
            f"Difference="
            f"{len(api_names ^ source_names)}"
        )
    )

    # ========================================================
    # KPI RECONCILIATION
    # ========================================================

    source_lookup = (
        source
        .set_index(
            "kpi_name"
        )
    )

    api_lookup = {
        str(
            kpi["kpi_name"]
        ): kpi
        for kpi in api_kpis
    }

    reconciliation_failures = []

    for kpi_name, source_row in source_lookup.iterrows():

        kpi_name = str(
            kpi_name
        )

        api_kpi = api_lookup.get(
            kpi_name
        )

        if api_kpi is None:

            reconciliation_failures.append(
                f"{kpi_name}: missing from API"
            )

            continue

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        source_status = str(
            source_row[
                "status"
            ]
        )

        api_status = str(
            api_kpi[
                "status"
            ]
        )

        if source_status != api_status:

            reconciliation_failures.append(
                (
                    f"{kpi_name}: status "
                    f"API={api_status}, "
                    f"source={source_status}"
                )
            )

        # ----------------------------------------------------
        # Unit
        # ----------------------------------------------------

        source_unit = str(
            source_row[
                "unit"
            ]
        )

        api_unit = str(
            api_kpi[
                "unit"
            ]
        )

        if source_unit != api_unit:

            reconciliation_failures.append(
                (
                    f"{kpi_name}: unit "
                    f"API={api_unit}, "
                    f"source={source_unit}"
                )
            )

        # ----------------------------------------------------
        # Value
        # ----------------------------------------------------

        source_value = source_row[
            "value"
        ]

        api_value = api_kpi[
            "value"
        ]

        if pd.isna(
            source_value
        ):

            if api_value is not None:

                reconciliation_failures.append(
                    (
                        f"{kpi_name}: "
                        f"expected null value"
                    )
                )

        else:

            try:

                values_match = np.isclose(
                    float(api_value),
                    float(source_value),
                    rtol=1e-6,
                    atol=1e-6
                )

                if not values_match:

                    reconciliation_failures.append(
                        (
                            f"{kpi_name}: value "
                            f"API={api_value}, "
                            f"source={source_value}"
                        )
                    )

            except (
                TypeError,
                ValueError
            ):

                reconciliation_failures.append(
                    (
                        f"{kpi_name}: invalid "
                        f"numeric API value"
                    )
                )

        # ----------------------------------------------------
        # Definition
        # ----------------------------------------------------

        definition = str(
            api_kpi.get(
                "definition",
                ""
            )
        ).strip()

        if not definition:

            reconciliation_failures.append(
                (
                    f"{kpi_name}: "
                    f"missing definition"
                )
            )

    check(
        "All KPI values, units, statuses, and definitions reconcile",
        len(
            reconciliation_failures
        ) == 0,
        (
            "All source KPIs reconciled"
            if not reconciliation_failures
            else
            f"Failures={len(reconciliation_failures)}"
        )
    )

    # ========================================================
    # UNSUPPORTED KPIs
    # ========================================================

    expected_unsupported_names = {
        "COMPLAINT_RATE",
        "COMPLAINT_RESOLUTION_TIME"
    }

    api_unsupported_names = {
        kpi["kpi_name"]
        for kpi in api_kpis
        if kpi["status"] == "NOT_SUPPORTED"
    }

    check(
        "Unsupported complaint KPIs remain explicit",
        api_unsupported_names
        ==
        expected_unsupported_names,
        (
            f"Unsupported="
            f"{sorted(api_unsupported_names)}"
        )
    )

    unsupported_non_null = [

        kpi
        for kpi in api_kpis
        if (
            kpi["status"] == "NOT_SUPPORTED"
            and
            kpi["value"] is not None
        )
    ]

    check(
        "Unsupported KPI values remain null",
        len(
            unsupported_non_null
        ) == 0,
        (
            f"Invalid values="
            f"{len(unsupported_non_null)}"
        )
    )

    # ========================================================
    # PROXY KPI
    # ========================================================

    proxy_kpis = [
        kpi
        for kpi in api_kpis
        if kpi["status"] == "PROXY"
    ]

    check(
        "Retention proxy KPI is explicitly marked",
        (
            len(proxy_kpis) == 1
            and
            proxy_kpis[0]["kpi_name"]
            ==
            "RETENTION_PROXY_RATE"
        ),
        (
            "RETENTION_PROXY_RATE present"
            if len(proxy_kpis) == 1
            else (
                f"Proxy KPIs="
                f"{[
                    k['kpi_name']
                    for k in proxy_kpis
                ]}"
            )
        )
    )

    # ========================================================
    # AVAILABLE KPI VALUES
    # ========================================================

    available_null_values = [

        kpi
        for kpi in api_kpis
        if (
            kpi["status"] == "AVAILABLE"
            and
            kpi["value"] is None
        )
    ]

    check(
        "AVAILABLE KPIs have values",
        len(
            available_null_values
        ) == 0,
        (
            f"Missing values="
            f"{len(available_null_values)}"
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

        kpi_definition = (
            openapi
            .get(
                "paths",
                {}
            )
            .get(
                "/kpis",
                {}
            )
            .get(
                "get"
            )
        )

        check(
            "OpenAPI contains GET /kpis",
            kpi_definition is not None,
            "GET /kpis registered"
        )

    except Exception as exc:

        check(
            "OpenAPI contains GET /kpis",
            False,
            str(exc)
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
    print("DAY 8 /KPIS VALIDATION SUMMARY")
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
            "DAY 8 BRICK 8.6 — /KPIS: PASSED"
        )
        print("=" * 60)

        print()
        print(
            "KPI listing, counts, values, units, statuses, "
            "definitions, unsupported metrics, proxy "
            "handling, source reconciliation, and "
            "OpenAPI registration are independently validated."
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
        "DAY 8 BRICK 8.6 — /KPIS: FAILED"
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