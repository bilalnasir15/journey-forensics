import os
import sys

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RAW_DIR = os.path.join(
    BASE_DIR,
    "data",
    "raw"
)

PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "data_quality_report.csv"
)


# ============================================================
# DATASETS
# ============================================================

DATASETS = [
    "customers.csv",
    "trips.csv",
    "bookings.csv",
    "payments.csv",
    "events.csv",
]


# ============================================================
# EXPECTED ROW COUNTS
# ============================================================

EXPECTED_ROWS = {
    "customers.csv": 5000,
    "trips.csv": 50,
    "bookings.csv": 8000,
    "payments.csv": 10557,
    "events.csv": 61673,
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_percentage(numerator, denominator):
    """
    Safely calculate percentage.
    """

    if denominator == 0:
        return 0.0

    return round(
        (numerator / denominator) * 100,
        2
    )


def calculate_quality_score(
    missing_pct,
    duplicate_pct,
    invalid_pct
):
    """
    Calculate overall data quality score.

    Missing values:
        50% weight

    Duplicate rows:
        30% weight

    Invalid values:
        20% weight
    """

    score = 100.0

    score -= missing_pct * 0.50
    score -= duplicate_pct * 0.30
    score -= invalid_pct * 0.20

    return round(
        max(
            0.0,
            min(
                100.0,
                score
            )
        ),
        2
    )


def get_quality_status(score):
    """
    Convert quality score into a readable status.
    """

    if score >= 95:
        return "EXCELLENT"

    if score >= 85:
        return "GOOD"

    if score >= 70:
        return "ACCEPTABLE"

    return "POOR"


# ============================================================
# PROFILE ONE DATASET
# ============================================================

def profile_dataset(file_name):

    file_path = os.path.join(
        RAW_DIR,
        file_name
    )

    print()
    print("=" * 60)
    print(f"DATASET: {file_name}")
    print("=" * 60)

    # --------------------------------------------------------
    # FILE CHECK
    # --------------------------------------------------------

    if not os.path.exists(file_path):

        print("STATUS: FILE NOT FOUND")

        return None

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    try:

        df = pd.read_csv(
            file_path
        )

    except Exception as exc:

        print("STATUS: FAILED TO READ")
        print(f"ERROR: {exc}")

        return None

    # --------------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------------

    rows = int(
        df.shape[0]
    )

    columns = int(
        df.shape[1]
    )

    total_cells = rows * columns

    # --------------------------------------------------------
    # DUPLICATES
    # --------------------------------------------------------

    duplicate_rows = int(
        df.duplicated().sum()
    )

    duplicate_percentage = safe_percentage(
        duplicate_rows,
        rows
    )

    # --------------------------------------------------------
    # MISSING VALUES
    # --------------------------------------------------------

    missing_cells = int(
        df.isna().sum().sum()
    )

    missing_percentage = safe_percentage(
        missing_cells,
        total_cells
    )

    columns_with_missing = int(
        (df.isna().sum() > 0).sum()
    )

    # --------------------------------------------------------
    # UNIQUE VALUES / CARDINALITY
    # --------------------------------------------------------

    unique_values = int(
        sum(
            df[column].nunique(
                dropna=True
            )
            for column in df.columns
        )
    )

    cardinality_percentage = safe_percentage(
        unique_values,
        total_cells
    )

    # --------------------------------------------------------
    # DATA TYPES
    # --------------------------------------------------------

    numeric_columns = int(
        df.select_dtypes(
            include=np.number
        ).shape[1]
    )

    # IMPORTANT:
    # We intentionally do NOT use:
    #
    # df.select_dtypes(include=["object"])
    #
    # because newer pandas versions can emit a warning
    # around string dtype compatibility.
    #
    # Instead, inspect the actual dtype names.

    object_columns = int(
        sum(
            str(dtype) == "object"
            for dtype in df.dtypes
        )
    )

    string_columns = int(
        sum(
            str(dtype) == "string"
            for dtype in df.dtypes
        )
    )

    datetime_like_columns = int(
        sum(
            (
                "date" in column.lower()
                or "time" in column.lower()
            )
            for column in df.columns
        )
    )

    # --------------------------------------------------------
    # INVALID NUMERIC VALUES
    # --------------------------------------------------------

    invalid_values = 0

    numeric_df = df.select_dtypes(
        include=np.number
    )

    if not numeric_df.empty:

        numeric_array = numeric_df.to_numpy(
            dtype=float,
            na_value=np.nan
        )

        invalid_values = int(
            np.isinf(
                numeric_array
            ).sum()
        )

    invalid_percentage = safe_percentage(
        invalid_values,
        total_cells
    )

    # --------------------------------------------------------
    # QUALITY SCORE
    # --------------------------------------------------------

    quality_score = calculate_quality_score(
        missing_percentage,
        duplicate_percentage,
        invalid_percentage
    )

    quality_status = get_quality_status(
        quality_score
    )

    # --------------------------------------------------------
    # EXPECTED ROW COUNT CHECK
    # --------------------------------------------------------

    expected_rows = EXPECTED_ROWS.get(
        file_name
    )

    row_count_status = (
        "MATCH"
        if expected_rows is not None
        and rows == expected_rows
        else "MISMATCH"
    )

    # --------------------------------------------------------
    # CONSOLE REPORT
    # --------------------------------------------------------

    print(
        f"Rows:                 {rows:,}"
    )

    print(
        f"Columns:              {columns:,}"
    )

    print(
        f"Expected rows:        "
        f"{expected_rows:,}"
        if expected_rows is not None
        else "Expected rows:        N/A"
    )

    print(
        f"Row count status:     {row_count_status}"
    )

    print(
        f"Missing cells:        {missing_cells:,}"
    )

    print(
        f"Missing percentage:   "
        f"{missing_percentage:.2f}%"
    )

    print(
        f"Columns with missing: "
        f"{columns_with_missing:,}"
    )

    print(
        f"Duplicate rows:       "
        f"{duplicate_rows:,}"
    )

    print(
        f"Duplicate percentage: "
        f"{duplicate_percentage:.2f}%"
    )

    print(
        f"Unique values:        "
        f"{unique_values:,}"
    )

    print(
        f"Cardinality:          "
        f"{cardinality_percentage:.2f}%"
    )

    print(
        f"Numeric columns:      "
        f"{numeric_columns:,}"
    )

    print(
        f"Object columns:       "
        f"{object_columns:,}"
    )

    print(
        f"String columns:       "
        f"{string_columns:,}"
    )

    print(
        f"Date/time-like cols:  "
        f"{datetime_like_columns:,}"
    )

    print(
        f"Invalid values:       "
        f"{invalid_values:,}"
    )

    print(
        f"Quality score:        "
        f"{quality_score:.2f}"
    )

    print(
        f"Quality status:       "
        f"{quality_status}"
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "dataset": file_name,
        "rows": rows,
        "expected_rows": expected_rows,
        "row_count_status": row_count_status,
        "columns": columns,
        "missing_cells": missing_cells,
        "missing_percentage": missing_percentage,
        "columns_with_missing": columns_with_missing,
        "duplicate_rows": duplicate_rows,
        "duplicate_percentage": duplicate_percentage,
        "unique_values": unique_values,
        "cardinality_percentage": cardinality_percentage,
        "numeric_columns": numeric_columns,
        "object_columns": object_columns,
        "string_columns": string_columns,
        "datetime_like_columns": datetime_like_columns,
        "invalid_values": invalid_values,
        "invalid_percentage": invalid_percentage,
        "quality_score": quality_score,
        "quality_status": quality_status,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("JOURNEY FORENSICS DATA PROFILING ENGINE")
    print("=" * 60)

    print()
    print(
        "Loading raw datasets..."
    )

    print(
        f"Source: {RAW_DIR}"
    )

    # --------------------------------------------------------
    # CREATE OUTPUT DIRECTORY
    # --------------------------------------------------------

    os.makedirs(
        PROCESSED_DIR,
        exist_ok=True
    )

    # --------------------------------------------------------
    # PROFILE DATASETS
    # --------------------------------------------------------

    results = []

    for file_name in DATASETS:

        result = profile_dataset(
            file_name
        )

        if result is not None:

            results.append(
                result
            )

    # --------------------------------------------------------
    # NO RESULTS
    # --------------------------------------------------------

    if not results:

        print()
        print(
            "No datasets were successfully profiled."
        )

        return 1

    # --------------------------------------------------------
    # CREATE REPORT
    # --------------------------------------------------------

    report = pd.DataFrame(
        results
    )

    # --------------------------------------------------------
    # OVERALL QUALITY
    # --------------------------------------------------------

    overall_quality_score = round(
        report[
            "quality_score"
        ].mean(),
        2
    )

    # --------------------------------------------------------
    # SAVE REPORT
    # --------------------------------------------------------

    report.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print()
    print("=" * 60)
    print("DATA PROFILING SUMMARY")
    print("=" * 60)

    print(
        f"Datasets profiled: "
        f"{len(report)}"
    )

    print(
        f"Overall quality score: "
        f"{overall_quality_score:.2f}"
    )

    print()

    summary_columns = [
        "dataset",
        "rows",
        "columns",
        "missing_percentage",
        "duplicate_percentage",
        "quality_score",
        "quality_status",
    ]

    print(
        report[
            summary_columns
        ].to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # FINAL STATUS
    # --------------------------------------------------------

    all_rows_match = bool(
        (
            report[
                "row_count_status"
            ] == "MATCH"
        ).all()
    )

    all_scores_valid = bool(
        report[
            "quality_score"
        ].between(
            0,
            100
        ).all()
    )

    if (
        all_rows_match
        and all_scores_valid
    ):

        profiling_status = "PASSED"

    else:

        profiling_status = "WARNING"

    print()
    print("=" * 60)
    print(
        f"DATA PROFILING COMPLETE: "
        f"{profiling_status}"
    )
    print("=" * 60)

    print()
    print("Output file:")
    print(OUTPUT_FILE)

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )