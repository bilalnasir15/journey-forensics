import os
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

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
# HELPERS
# ============================================================

def safe_percentage(numerator, denominator):
    if denominator == 0:
        return 0.0

    return round((numerator / denominator) * 100, 2)


def calculate_quality_score(
    missing_pct,
    duplicate_pct,
    invalid_pct=0.0
):
    """
    Overall quality score.

    Missing values, duplicate rows and invalid values
    reduce the score.
    """

    score = 100.0

    score -= missing_pct * 0.5
    score -= duplicate_pct * 0.3
    score -= invalid_pct * 0.2

    return round(max(0.0, min(100.0, score)), 2)


# ============================================================
# PROFILE ONE DATASET
# ============================================================

def profile_dataset(file_name):

    file_path = os.path.join(RAW_DIR, file_name)

    print()
    print("=" * 60)
    print(f"DATASET: {file_name}")
    print("=" * 60)

    if not os.path.exists(file_path):
        print("STATUS: FILE NOT FOUND")
        return None

    try:
        df = pd.read_csv(file_path)
    except Exception as exc:
        print(f"STATUS: FAILED TO READ")
        print(f"ERROR: {exc}")
        return None

    rows, columns = df.shape

    # --------------------------------------------------------
    # DUPLICATES
    # --------------------------------------------------------

    duplicate_rows = int(df.duplicated().sum())

    duplicate_pct = safe_percentage(
        duplicate_rows,
        rows
    )

    # --------------------------------------------------------
    # MISSING VALUES
    # --------------------------------------------------------

    missing_cells = int(df.isna().sum().sum())

    total_cells = rows * columns

    missing_pct = safe_percentage(
        missing_cells,
        total_cells
    )

    columns_with_missing = int(
        (df.isna().sum() > 0).sum()
    )

    # --------------------------------------------------------
    # UNIQUE / CARDINALITY
    # --------------------------------------------------------

    unique_columns = int(
        sum(df[column].nunique(dropna=True) for column in df.columns)
    )

    total_possible_values = rows * columns

    cardinality_pct = safe_percentage(
        unique_columns,
        total_possible_values
    )

    # --------------------------------------------------------
    # DATA TYPES
    # --------------------------------------------------------

    numeric_columns = int(
        df.select_dtypes(include=np.number).shape[1]
    )

    datetime_columns = int(
        sum(
            "date" in column.lower()
            or "time" in column.lower()
            for column in df.columns
        )
    )

    object_columns = int(
        df.select_dtypes(include=["object"]).shape[1]
    )

    # --------------------------------------------------------
    # INVALID VALUE CHECK
    # --------------------------------------------------------

    invalid_values = 0

    # Numeric columns: count infinite values
    numeric_df = df.select_dtypes(include=np.number)

    if not numeric_df.empty:
        invalid_values += int(
            np.isinf(numeric_df.to_numpy()).sum()
        )

    invalid_pct = safe_percentage(
        invalid_values,
        total_cells
    )

    # --------------------------------------------------------
    # QUALITY SCORE
    # --------------------------------------------------------

    quality_score = calculate_quality_score(
        missing_pct,
        duplicate_pct,
        invalid_pct
    )

    # --------------------------------------------------------
    # DATASET STATUS
    # --------------------------------------------------------

    if quality_score >= 95:
        quality_status = "EXCELLENT"

    elif quality_score >= 85:
        quality_status = "GOOD"

    elif quality_score >= 70:
        quality_status = "ACCEPTABLE"

    else:
        quality_status = "POOR"

    # --------------------------------------------------------
    # CONSOLE REPORT
    # --------------------------------------------------------

    print(f"Rows:                 {rows:,}")
    print(f"Columns:              {columns:,}")
    print(f"Missing cells:        {missing_cells:,}")
    print(f"Missing percentage:   {missing_pct:.2f}%")
    print(f"Columns with missing: {columns_with_missing:,}")
    print(f"Duplicate rows:       {duplicate_rows:,}")
    print(f"Duplicate percentage: {duplicate_pct:.2f}%")
    print(f"Unique values:        {unique_columns:,}")
    print(f"Cardinality:          {cardinality_pct:.2f}%")
    print(f"Numeric columns:      {numeric_columns:,}")
    print(f"Object columns:       {object_columns:,}")
    print(f"Date/time-like cols:  {datetime_columns:,}")
    print(f"Invalid values:       {invalid_values:,}")
    print(f"Quality score:        {quality_score:.2f}")
    print(f"Quality status:       {quality_status}")

    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return {
        "dataset": file_name,
        "rows": rows,
        "columns": columns,
        "missing_cells": missing_cells,
        "missing_percentage": missing_pct,
        "columns_with_missing": columns_with_missing,
        "duplicate_rows": duplicate_rows,
        "duplicate_percentage": duplicate_pct,
        "unique_values": unique_columns,
        "cardinality_percentage": cardinality_pct,
        "numeric_columns": numeric_columns,
        "object_columns": object_columns,
        "datetime_like_columns": datetime_columns,
        "invalid_values": invalid_values,
        "quality_score": quality_score,
        "quality_status": quality_status,
    }


# ============================================================
# MAIN PROFILER
# ============================================================

def main():

    print()
    print("=" * 60)
    print("JOURNEY FORENSICS DATA PROFILING ENGINE")
    print("=" * 60)

    print()
    print("Loading raw datasets...")
    print(f"Source: {RAW_DIR}")

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    results = []

    for file_name in DATASETS:

        result = profile_dataset(file_name)

        if result is not None:
            results.append(result)

    # --------------------------------------------------------
    # BUILD REPORT
    # --------------------------------------------------------

    report = pd.DataFrame(results)

    if report.empty:

        print()
        print("No datasets were successfully profiled.")
        return

    # --------------------------------------------------------
    # OVERALL QUALITY
    # --------------------------------------------------------

    overall_quality_score = round(
        report["quality_score"].mean(),
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
    # FINAL REPORT
    # --------------------------------------------------------

    print()
    print()
    print("=" * 60)
    print("DATA PROFILING SUMMARY")
    print("=" * 60)

    print(
        f"Datasets profiled: {len(report)}"
    )

    print(
        f"Overall quality score: "
        f"{overall_quality_score:.2f}"
    )

    print()
    print(
        report[
            [
                "dataset",
                "rows",
                "columns",
                "missing_percentage",
                "duplicate_percentage",
                "quality_score",
                "quality_status",
            ]
        ].to_string(index=False)
    )

    print()
    print("=" * 60)
    print("DATA PROFILING COMPLETE")
    print("=" * 60)

    print()
    print("Output file:")
    print(OUTPUT_FILE)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()