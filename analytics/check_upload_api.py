import os
import sys
from io import BytesIO

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

UPLOAD_DIR = os.path.join(
    BASE_DIR,
    "data",
    "uploads"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "day8_upload_validation_report.csv"
)

TEST_FILENAME = "validation_test.csv"

VALID_CSV = (
    "customer_id,name\n"
    "TEST001,Usama\n"
    "TEST002,Ali\n"
    "TEST003,Ahmed\n"
)

EMPTY_CSV = (
    "customer_id,name\n"
)

INVALID_CSV = (
    "this,is,not,a,valid\n"
    "csv,\"broken"
)

NON_CSV_FILENAME = "validation_test.txt"

EXPECTED_ROWS = 3
EXPECTED_COLUMNS = 2


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
# HELPERS
# ============================================================

def cleanup_file(
    path
):

    try:

        if os.path.isfile(
            path
        ):

            os.remove(
                path
            )

    except OSError:
        pass


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 8 — /UPLOAD ENDPOINT VALIDATION")
    print("=" * 60)

    # ========================================================
    # UPLOAD DIRECTORY
    # ========================================================

    check(
        "Upload directory exists",
        os.path.isdir(
            UPLOAD_DIR
        ),
        UPLOAD_DIR
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
    # VALID CSV
    # ========================================================

    print()
    print("VALIDATING VALID CSV UPLOAD")
    print("-" * 40)

    response = client.post(
        "/upload",
        files={
            "file": (
                TEST_FILENAME,
                BytesIO(
                    VALID_CSV.encode(
                        "utf-8"
                    )
                ),
                "text/csv"
            )
        }
    )

    check(
        "Valid CSV returns 200",
        response.status_code == 200,
        f"HTTP {response.status_code}"
    )

    try:

        response_json = response.json()

    except Exception as exc:

        check(
            "Upload response is valid JSON",
            False,
            str(exc)
        )

        response_json = {}

    check(
        "Upload response is a JSON object",
        isinstance(
            response_json,
            dict
        ),
        "JSON object received"
    )

    # ========================================================
    # REQUIRED RESPONSE FIELDS
    # ========================================================

    required_fields = {
        "filename",
        "stored_filename",
        "rows",
        "columns",
        "status"
    }

    missing_fields = (
        required_fields
        -
        set(
            response_json.keys()
        )
    )

    check(
        "Upload response contains required fields",
        len(
            missing_fields
        ) == 0,
        (
            "All required fields present"
            if not missing_fields
            else f"Missing={sorted(missing_fields)}"
        )
    )

    # ========================================================
    # METADATA
    # ========================================================

    check(
        "Original filename is preserved",
        response_json.get(
            "filename"
        )
        ==
        TEST_FILENAME,
        (
            f"Filename="
            f"{response_json.get('filename')}"
        )
    )

    check(
        "Uploaded row count is correct",
        response_json.get(
            "rows"
        )
        ==
        EXPECTED_ROWS,
        (
            f"Expected={EXPECTED_ROWS}, "
            f"Actual={response_json.get('rows')}"
        )
    )

    check(
        "Uploaded column count is correct",
        response_json.get(
            "columns"
        )
        ==
        EXPECTED_COLUMNS,
        (
            f"Expected={EXPECTED_COLUMNS}, "
            f"Actual={response_json.get('columns')}"
        )
    )

    check(
        "Upload status is UPLOADED",
        response_json.get(
            "status"
        )
        ==
        "UPLOADED",
        (
            f"Status="
            f"{response_json.get('status')}"
        )
    )

    # ========================================================
    # UNIQUE STORED NAME
    # ========================================================

    stored_filename = response_json.get(
        "stored_filename"
    )

    check(
        "Stored filename is different from original filename",
        stored_filename
        !=
        TEST_FILENAME,
        (
            f"Stored={stored_filename}"
        )
    )

    check(
        "Stored filename ends with original filename",
        (
            isinstance(
                stored_filename,
                str
            )
            and
            stored_filename.endswith(
                TEST_FILENAME
            )
        ),
        (
            f"Stored={stored_filename}"
        )
    )

    # ========================================================
    # FILE ACTUALLY EXISTS
    # ========================================================

    stored_path = os.path.join(
        UPLOAD_DIR,
        str(
            stored_filename
        )
    )

    check(
        "Uploaded file exists on disk",
        os.path.isfile(
            stored_path
        ),
        stored_path
    )

    # ========================================================
    # STORED FILE CONTENT
    # ========================================================

    try:

        stored_df = pd.read_csv(
            stored_path
        )

        check(
            "Stored file can be read as CSV",
            True,
            (
                f"Rows={len(stored_df):,}, "
                f"Columns={len(stored_df.columns):,}"
            )
        )

        check(
            "Stored file row count matches upload metadata",
            len(stored_df)
            ==
            EXPECTED_ROWS,
            (
                f"Expected={EXPECTED_ROWS}, "
                f"Actual={len(stored_df)}"
            )
        )

        check(
            "Stored file column count matches metadata",
            len(stored_df.columns)
            ==
            EXPECTED_COLUMNS,
            (
                f"Expected={EXPECTED_COLUMNS}, "
                f"Actual={len(stored_df.columns)}"
            )
        )

    except Exception as exc:

        check(
            "Stored file can be read as CSV",
            False,
            str(exc)
        )

    # ========================================================
    # EMPTY CSV
    # ========================================================

    print()
    print("VALIDATING EMPTY CSV")
    print("-" * 40)

    empty_response = client.post(
        "/upload",
        files={
            "file": (
                "empty_test.csv",
                BytesIO(
                    EMPTY_CSV.encode(
                        "utf-8"
                    )
                ),
                "text/csv"
            )
        }
    )

    check(
        "Empty CSV is rejected",
        empty_response.status_code == 400,
        (
            f"HTTP="
            f"{empty_response.status_code}"
        )
    )

    try:

        empty_detail = str(
            empty_response.json().get(
                "detail",
                ""
            )
        )

        check(
            "Empty CSV provides useful error detail",
            "no data rows" in empty_detail.lower(),
            empty_detail
        )

    except Exception as exc:

        check(
            "Empty CSV provides useful error detail",
            False,
            str(exc)
        )

    # ========================================================
    # NON-CSV FILE
    # ========================================================

    print()
    print("VALIDATING NON-CSV FILE")
    print("-" * 40)

    non_csv_response = client.post(
        "/upload",
        files={
            "file": (
                NON_CSV_FILENAME,
                BytesIO(
                    b"some text"
                ),
                "text/plain"
            )
        }
    )

    check(
        "Non-CSV file is rejected",
        non_csv_response.status_code == 415,
        (
            f"HTTP="
            f"{non_csv_response.status_code}"
        )
    )

    try:

        non_csv_detail = str(
            non_csv_response.json().get(
                "detail",
                ""
            )
        )

        check(
            "Non-CSV response explains file requirement",
            "csv" in non_csv_detail.lower(),
            non_csv_detail
        )

    except Exception as exc:

        check(
            "Non-CSV response explains file requirement",
            False,
            str(exc)
        )

    # ========================================================
    # NO FILE
    # ========================================================

    print()
    print("VALIDATING MISSING FILE")
    print("-" * 40)

    no_file_response = client.post(
        "/upload"
    )

    check(
        "Missing file returns 422",
        no_file_response.status_code == 422,
        (
            f"HTTP="
            f"{no_file_response.status_code}"
        )
    )

    # ========================================================
    # PATH TRAVERSAL PROTECTION
    # ========================================================

    print()
    print("VALIDATING FILENAME SANITIZATION")
    print("-" * 40)

    traversal_name = (
        "../../unsafe_upload.csv"
    )

    traversal_response = client.post(
        "/upload",
        files={
            "file": (
                traversal_name,
                BytesIO(
                    VALID_CSV.encode(
                        "utf-8"
                    )
                ),
                "text/csv"
            )
        }
    )

    check(
        "Path traversal filename is accepted safely",
        traversal_response.status_code == 200,
        (
            f"HTTP="
            f"{traversal_response.status_code}"
        )
    )

    try:

        traversal_json = (
            traversal_response.json()
        )

        safe_name = str(
            traversal_json.get(
                "stored_filename",
                ""
            )
        )

        check(
            "Stored upload name does not contain path separators",
            (
                "/" not in safe_name
                and
                "\\" not in safe_name
                and
                ".." not in safe_name
            ),
            (
                f"Stored={safe_name}"
            )
        )

    except Exception as exc:

        check(
            "Stored upload name does not contain path separators",
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
        (
            f"HTTP="
            f"{openapi_response.status_code}"
        )
    )

    try:

        openapi = (
            openapi_response.json()
        )

        upload_definition = (
            openapi
            .get(
                "paths",
                {}
            )
            .get(
                "/upload",
                {}
            )
            .get(
                "post"
            )
        )

        check(
            "OpenAPI contains POST /upload",
            upload_definition is not None,
            "POST /upload registered"
        )

        request_body = (
            upload_definition
            .get(
                "requestBody",
                {}
            )
            if upload_definition
            else {}
        )

        content = request_body.get(
            "content",
            {}
        )

        check(
            "Upload endpoint uses multipart/form-data",
            "multipart/form-data" in content,
            (
                f"Content types="
                f"{list(content.keys())}"
            )
        )

    except Exception as exc:

        check(
            "OpenAPI upload definition is valid",
            False,
            str(exc)
        )

    # ========================================================
    # CLEANUP TEST FILES
    # ========================================================

    print()
    print("CLEANING TEST UPLOADS")
    print("-" * 40)

    cleanup_file(
        stored_path
    )

    if os.path.isdir(
        UPLOAD_DIR
    ):

        remaining_test_files = [

            filename

            for filename in os.listdir(
                UPLOAD_DIR
            )

            if (
                filename.endswith(
                    "test_upload.csv"
                )
                or
                filename.endswith(
                    "validation_test.csv"
                )
                or
                filename.endswith(
                    "empty_test.csv"
                )
                or
                filename.endswith(
                    "validation_test.txt"
                )
                or
                "unsafe_upload.csv" in filename
            )
        ]

        for filename in remaining_test_files:

            cleanup_file(
                os.path.join(
                    UPLOAD_DIR,
                    filename
                )
            )

        check(
            "Test upload artifacts cleaned",
            True,
            (
                f"Removed={len(remaining_test_files) + 1}"
            )
        )

    else:

        check(
            "Test upload artifacts cleaned",
            False,
            "Upload directory disappeared unexpectedly"
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
    print("DAY 8 /UPLOAD VALIDATION SUMMARY")
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
            "DAY 8 BRICK 8.7 — /UPLOAD: PASSED"
        )
        print("=" * 60)

        print()
        print(
            "CSV upload, parsing, metadata, storage, "
            "validation, filename sanitization, error "
            "handling, cleanup, and OpenAPI registration "
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
        "DAY 8 BRICK 8.7 — /UPLOAD: FAILED"
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