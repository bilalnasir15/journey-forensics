import math
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

PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

PROFILE_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_segmentation_final.csv"
)

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day8_customers_validation_report.csv"
)

EXPECTED_TOTAL_CUSTOMERS = 5000

TEST_PAGE_SIZE = 10


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
    print("DAY 8 — /CUSTOMERS ENDPOINT VALIDATION")
    print("=" * 60)

    # ========================================================
    # SOURCE FILE
    # ========================================================

    check(
        "Customer profile dataset exists",
        os.path.isfile(PROFILE_FILE),
        PROFILE_FILE
    )

    if not os.path.isfile(PROFILE_FILE):
        return 1

    try:

        source = pd.read_csv(
            PROFILE_FILE
        )

        check(
            "Customer profile dataset loads",
            True,
            f"Rows={len(source):,}"
        )

    except Exception as exc:

        check(
            "Customer profile dataset loads",
            False,
            str(exc)
        )

        return 1

    # ========================================================
    # SOURCE CUSTOMER COUNT
    # ========================================================

    check(
        "Source customer count is 5,000",
        len(source) == EXPECTED_TOTAL_CUSTOMERS,
        f"Actual={len(source):,}"
    )

    check(
        "Source customer IDs are unique",
        source[
            "customer_id"
        ].astype(str).is_unique,
        (
            f"Duplicates="
            f"{source['customer_id'].duplicated().sum()}"
        )
    )

    source_ids = (
        source[
            "customer_id"
        ]
        .astype(str)
        .tolist()
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
    # PAGE 1
    # ========================================================

    print()
    print("VALIDATING PAGE 1")
    print("-" * 40)

    page_1_response = client.get(
        "/customers",
        params={
            "page": 1,
            "page_size": TEST_PAGE_SIZE
        }
    )

    check(
        "Page 1 returns 200",
        page_1_response.status_code == 200,
        f"HTTP {page_1_response.status_code}"
    )

    try:

        page_1 = page_1_response.json()

        check(
            "Page 1 response is JSON object",
            isinstance(page_1, dict),
            "JSON object received"
        )

    except Exception as exc:

        check(
            "Page 1 response is JSON object",
            False,
            str(exc)
        )

        return 1

    # ========================================================
    # REQUIRED RESPONSE FIELDS
    # ========================================================

    required_fields = {
        "total",
        "page",
        "page_size",
        "total_pages",
        "customers"
    }

    missing_fields = (
        required_fields
        -
        set(page_1.keys())
    )

    check(
        "Customers response contains required fields",
        len(missing_fields) == 0,
        (
            "All required fields present"
            if not missing_fields
            else f"Missing={sorted(missing_fields)}"
        )
    )

    # ========================================================
    # TOTAL
    # ========================================================

    check(
        "Total customers returned is 5,000",
        page_1.get("total")
        ==
        EXPECTED_TOTAL_CUSTOMERS,
        (
            f"API total="
            f"{page_1.get('total')}"
        )
    )

    check(
        "Page number is correct",
        page_1.get("page") == 1,
        f"Page={page_1.get('page')}"
    )

    check(
        "Page size is correct",
        page_1.get("page_size")
        ==
        TEST_PAGE_SIZE,
        (
            f"Page size="
            f"{page_1.get('page_size')}"
        )
    )

    expected_total_pages = math.ceil(
        EXPECTED_TOTAL_CUSTOMERS
        /
        TEST_PAGE_SIZE
    )

    check(
        "Total pages is mathematically correct",
        page_1.get("total_pages")
        ==
        expected_total_pages,
        (
            f"Expected={expected_total_pages}, "
            f"Actual={page_1.get('total_pages')}"
        )
    )

    # ========================================================
    # PAGE 1 RECORD COUNT
    # ========================================================

    page_1_customers = page_1.get(
        "customers",
        []
    )

    check(
        "Page 1 contains 10 customers",
        len(page_1_customers)
        ==
        TEST_PAGE_SIZE,
        (
            f"Records="
            f"{len(page_1_customers)}"
        )
    )

    # ========================================================
    # CUSTOMER ITEM STRUCTURE
    # ========================================================

    customer_required_fields = {
        "customer_id",
        "first_name",
        "last_name",
        "country",
        "customer_segment"
    }

    invalid_customer_objects = 0

    for customer in page_1_customers:

        if not isinstance(
            customer,
            dict
        ):

            invalid_customer_objects += 1
            continue

        if not customer_required_fields.issubset(
            set(customer.keys())
        ):

            invalid_customer_objects += 1

    check(
        "Customer records have required fields",
        invalid_customer_objects == 0,
        (
            f"Invalid records="
            f"{invalid_customer_objects}"
        )
    )

    # ========================================================
    # PAGE 1 ORDERING
    # ========================================================

    page_1_ids = [
        str(
            customer["customer_id"]
        )
        for customer in page_1_customers
    ]

    check(
        "Page 1 customer IDs are unique",
        len(page_1_ids)
        ==
        len(set(page_1_ids)),
        (
            f"Records={len(page_1_ids)}, "
            f"Unique={len(set(page_1_ids))}"
        )
    )

    check(
        "Page 1 is sorted by customer_id",
        page_1_ids == sorted(page_1_ids),
        "Stable customer ordering"
    )

    # ========================================================
    # PAGE 1 SOURCE RECONCILIATION
    # ========================================================

    expected_page_1_ids = sorted(
        source_ids
    )[
        0:TEST_PAGE_SIZE
    ]

    check(
        "Page 1 IDs match source ordering",
        page_1_ids
        ==
        expected_page_1_ids,
        (
            f"First ID="
            f"{page_1_ids[0] if page_1_ids else None}"
        )
    )

    # ========================================================
    # PAGE 2
    # ========================================================

    print()
    print("VALIDATING PAGE 2")
    print("-" * 40)

    page_2_response = client.get(
        "/customers",
        params={
            "page": 2,
            "page_size": TEST_PAGE_SIZE
        }
    )

    check(
        "Page 2 returns 200",
        page_2_response.status_code == 200,
        f"HTTP {page_2_response.status_code}"
    )

    try:

        page_2 = page_2_response.json()

        page_2_customers = page_2.get(
            "customers",
            []
        )

    except Exception as exc:

        check(
            "Page 2 response is valid JSON",
            False,
            str(exc)
        )

        page_2 = {}
        page_2_customers = []

    check(
        "Page 2 number is correct",
        page_2.get("page") == 2,
        f"Page={page_2.get('page')}"
    )

    check(
        "Page 2 contains 10 customers",
        len(page_2_customers)
        ==
        TEST_PAGE_SIZE,
        (
            f"Records="
            f"{len(page_2_customers)}"
        )
    )

    page_2_ids = [
        str(
            customer["customer_id"]
        )
        for customer in page_2_customers
    ]

    # ========================================================
    # NO OVERLAP
    # ========================================================

    overlap = (
        set(page_1_ids)
        &
        set(page_2_ids)
    )

    check(
        "Page 1 and Page 2 have no overlapping customers",
        len(overlap) == 0,
        (
            f"Overlap={len(overlap)}"
        )
    )

    # ========================================================
    # PAGE 2 SOURCE RECONCILIATION
    # ========================================================

    expected_page_2_ids = sorted(
        source_ids
    )[
        TEST_PAGE_SIZE:
        TEST_PAGE_SIZE * 2
    ]

    check(
        "Page 2 IDs match source ordering",
        page_2_ids
        ==
        expected_page_2_ids,
        (
            f"First ID="
            f"{page_2_ids[0] if page_2_ids else None}"
        )
    )

    # ========================================================
    # LARGE PAGE SIZE
    # ========================================================

    print()
    print("VALIDATING LARGE PAGE")
    print("-" * 40)

    large_page_response = client.get(
        "/customers",
        params={
            "page": 1,
            "page_size": 500
        }
    )

    check(
        "Maximum allowed page size 500 returns 200",
        large_page_response.status_code == 200,
        f"HTTP {large_page_response.status_code}"
    )

    try:

        large_page = (
            large_page_response.json()
        )

        large_records = large_page.get(
            "customers",
            []
        )

        check(
            "Page size 500 returns 500 records",
            len(large_records) == 500,
            (
                f"Records={len(large_records)}"
            )
        )

    except Exception as exc:

        check(
            "Page size 500 response is valid JSON",
            False,
            str(exc)
        )

    # ========================================================
    # INVALID PAGE
    # ========================================================

    print()
    print("VALIDATING INVALID PAGE")
    print("-" * 40)

    invalid_page_response = client.get(
        "/customers",
        params={
            "page": 9999,
            "page_size": TEST_PAGE_SIZE
        }
    )

    check(
        "Out-of-range page returns 404",
        invalid_page_response.status_code == 404,
        (
            f"HTTP="
            f"{invalid_page_response.status_code}"
        )
    )

    try:

        invalid_page_json = (
            invalid_page_response.json()
        )

        detail = str(
            invalid_page_json.get(
                "detail",
                ""
            )
        )

        check(
            "Invalid page contains useful error detail",
            "Page 9999" in detail,
            detail
        )

    except Exception as exc:

        check(
            "Invalid page contains useful error detail",
            False,
            str(exc)
        )

    # ========================================================
    # INVALID PAGE SIZE — TOO LARGE
    # ========================================================

    print()
    print("VALIDATING INVALID PAGE SIZE")
    print("-" * 40)

    too_large_response = client.get(
        "/customers",
        params={
            "page": 1,
            "page_size": 501
        }
    )

    check(
        "page_size > 500 returns 422",
        too_large_response.status_code == 422,
        (
            f"HTTP="
            f"{too_large_response.status_code}"
        )
    )

    # ========================================================
    # INVALID PAGE — ZERO
    # ========================================================

    zero_page_response = client.get(
        "/customers",
        params={
            "page": 0,
            "page_size": TEST_PAGE_SIZE
        }
    )

    check(
        "page=0 returns 422",
        zero_page_response.status_code == 422,
        (
            f"HTTP="
            f"{zero_page_response.status_code}"
        )
    )

    # ========================================================
    # INVALID PAGE SIZE — ZERO
    # ========================================================

    zero_page_size_response = client.get(
        "/customers",
        params={
            "page": 1,
            "page_size": 0
        }
    )

    check(
        "page_size=0 returns 422",
        zero_page_size_response.status_code == 422,
        (
            f"HTTP="
            f"{zero_page_size_response.status_code}"
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

        openapi = (
            openapi_response.json()
        )

        customers_definition = (
            openapi
            .get(
                "paths",
                {}
            )
            .get(
                "/customers",
                {}
            )
            .get(
                "get"
            )
        )

        check(
            "OpenAPI contains GET /customers",
            customers_definition is not None,
            "GET /customers registered"
        )

    except Exception as exc:

        check(
            "OpenAPI contains GET /customers",
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
    print("DAY 8 /CUSTOMERS VALIDATION SUMMARY")
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
            "DAY 8 BRICK 8.4 — /CUSTOMERS: PASSED"
        )
        print("=" * 60)

        print()
        print(
            "Customer listing, pagination, ordering, "
            "Pydantic response structure, source "
            "reconciliation, and error handling "
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
        "DAY 8 BRICK 8.4 — /CUSTOMERS: FAILED"
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