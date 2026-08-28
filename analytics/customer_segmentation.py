import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "customer_risk_model.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "customer_risk_segments.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("=" * 60)
    print("CUSTOMER RISK SEGMENTATION")
    print("=" * 60)

    print("\nLoading customer risk model...")

    df = pd.read_csv(INPUT_FILE)

    print(
        f"Customers: {len(df):,}"
    )

    return df


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(df):

    numeric_columns = [
        "severity_score",
        "frequency_score",
        "persistence_score",
        "customer_risk_score",
        "total_bookings",
        "total_failed_payments",
        "total_retries",
        "total_anomalies",
        "problematic_journeys",
        "high_risk_journeys",
        "critical_journeys"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            ).fillna(0)

    return df


# ============================================================
# SEGMENT CLASSIFICATION
# ============================================================

def classify_segment(row):

    severity = row[
        "severity_score"
    ]

    frequency = row[
        "frequency_score"
    ]

    persistence = row[
        "persistence_score"
    ]

    risk = row[
        "customer_risk_score"
    ]

    problematic = row[
        "problematic_journeys"
    ]

    bookings = row[
        "total_bookings"
    ]

    # ========================================================
    # SEGMENT 1
    # CRITICAL RECURRING RISK
    # ========================================================

    if (

        risk >= 75

        and

        severity >= 75

        and

        persistence >= 50

        and

        problematic >= 2

    ):

        return "CRITICAL_RECURRING_RISK"

    # ========================================================
    # SEGMENT 2
    # PERSISTENT RISK
    # ========================================================

    if (

        persistence >= 50

        and

        problematic >= 2

    ):

        return "PERSISTENT_RISK"

    # ========================================================
    # SEGMENT 3
    # RECENT HIGH SEVERITY
    # ========================================================
    #
    # High severity but limited evidence of repetition.
    # ========================================================

    if (

        severity >= 75

        and

        persistence < 50

    ):

        return "RECENT_HIGH_SEVERITY"

    # ========================================================
    # SEGMENT 4
    # FREQUENT FRICTION
    # ========================================================

    if (

        frequency >= 15

        and

        severity < 75

    ):

        return "FREQUENT_FRICTION"

    # ========================================================
    # SEGMENT 5
    # DEVELOPING FRICTION
    # ========================================================

    if (

        (
            frequency >= 5
            or
            persistence >= 25
        )

        and

        risk >= 25

    ):

        return "DEVELOPING_FRICTION"

    # ========================================================
    # SEGMENT 6
    # STABLE CUSTOMER
    # ========================================================

    if (

        risk < 25

        and

        severity < 50

        and

        frequency < 15

        and

        persistence < 25

    ):

        if (

            bookings >= 3

            and

            problematic <= 1

        ):

            return "LOYAL_STABLE_CUSTOMER"

        return "STABLE_CUSTOMER"

    # ========================================================
    # FALLBACK
    # ========================================================

    return "DEVELOPING_FRICTION"


# ============================================================
# SEGMENT REASON
# ============================================================

def build_segment_reason(row):

    segment = row[
        "risk_segment"
    ]

    severity = row[
        "severity_score"
    ]

    frequency = row[
        "frequency_score"
    ]

    persistence = row[
        "persistence_score"
    ]

    problematic = int(
        row[
            "problematic_journeys"
        ]
    )

    reasons = []

    # --------------------------------------------------------
    # Critical recurring
    # --------------------------------------------------------

    if segment == "CRITICAL_RECURRING_RISK":

        reasons.append(
            "Very high severity"
        )

        reasons.append(
            "Persistent problematic behavior"
        )

        reasons.append(
            f"{problematic} problematic journeys"
        )

    # --------------------------------------------------------
    # Persistent
    # --------------------------------------------------------

    elif segment == "PERSISTENT_RISK":

        reasons.append(
            "Repeated problematic journeys"
        )

        reasons.append(
            f"Persistence score {persistence:.2f}"
        )

    # --------------------------------------------------------
    # Recent high severity
    # --------------------------------------------------------

    elif segment == "RECENT_HIGH_SEVERITY":

        reasons.append(
            f"High severity score {severity:.2f}"
        )

        reasons.append(
            "Limited evidence of repeated behavior"
        )

    # --------------------------------------------------------
    # Frequent friction
    # --------------------------------------------------------

    elif segment == "FREQUENT_FRICTION":

        reasons.append(
            f"Frequency score {frequency:.2f}"
        )

        reasons.append(
            "Repeated problematic activity"
        )

    # --------------------------------------------------------
    # Developing friction
    # --------------------------------------------------------

    elif segment == "DEVELOPING_FRICTION":

        reasons.append(
            "Emerging risk indicators"
        )

        if frequency >= 5:

            reasons.append(
                "Increasing problem frequency"
            )

        if persistence >= 25:

            reasons.append(
                "Early persistence signal"
            )

    # --------------------------------------------------------
    # Loyal stable
    # --------------------------------------------------------

    elif segment == "LOYAL_STABLE_CUSTOMER":

        reasons.append(
            "Multiple bookings"
        )

        reasons.append(
            "Low journey friction"
        )

        reasons.append(
            "Minimal problematic journeys"
        )

    # --------------------------------------------------------
    # Stable
    # --------------------------------------------------------

    elif segment == "STABLE_CUSTOMER":

        reasons.append(
            "Low overall risk"
        )

        reasons.append(
            "Low severity"
        )

        reasons.append(
            "Low frequency"
        )

    return " | ".join(
        reasons
    )


# ============================================================
# BUILD SEGMENTS
# ============================================================

def build_segments(df):

    print(
        "\nClassifying customer segments..."
    )

    df["risk_segment"] = (
        df.apply(
            classify_segment,
            axis=1
        )
    )

    df["segment_reason"] = (
        df.apply(
            build_segment_reason,
            axis=1
        )
    )

    return df


# ============================================================
# SEGMENT METRICS
# ============================================================

def calculate_segment_metrics(df):

    print(
        "Calculating segment statistics..."
    )

    metrics = (

        df
        .groupby(
            "risk_segment"
        )
        .agg(

            customer_count=(
                "customer_id",
                "count"
            ),

            average_risk_score=(
                "customer_risk_score",
                "mean"
            ),

            average_severity=(
                "severity_score",
                "mean"
            ),

            average_frequency=(
                "frequency_score",
                "mean"
            ),

            average_persistence=(
                "persistence_score",
                "mean"
            ),

            average_failed_payments=(
                "total_failed_payments",
                "mean"
            ),

            average_anomalies=(
                "total_anomalies",
                "mean"
            ),

            average_problematic_journeys=(
                "problematic_journeys",
                "mean"
            )
        )

        .reset_index()
    )

    # --------------------------------------------------------
    # Percentage of customers
    # --------------------------------------------------------

    total_customers = (
        metrics[
            "customer_count"
        ]
        .sum()
    )

    metrics["customer_percentage"] = (

        metrics[
            "customer_count"
        ]

        /

        total_customers

        * 100
    )

    numeric_columns = [
        "average_risk_score",
        "average_severity",
        "average_frequency",
        "average_persistence",
        "average_failed_payments",
        "average_anomalies",
        "average_problematic_journeys",
        "customer_percentage"
    ]

    for column in numeric_columns:

        metrics[column] = (
            metrics[column]
            .round(2)
        )

    return metrics


# ============================================================
# SEGMENT DRIVER ANALYSIS
# ============================================================

def calculate_segment_drivers(df):

    print(
        "Analyzing dominant segment dimensions..."
    )

    dimensions = [
        "severity_score",
        "frequency_score",
        "persistence_score"
    ]

    rows = []

    for segment, segment_df in df.groupby(
        "risk_segment"
    ):

        averages = {
            dimension:
            segment_df[
                dimension
            ].mean()
            for dimension in dimensions
        }

        dominant_dimension = max(
            averages,
            key=averages.get
        )

        rows.append(
            {
                "risk_segment": segment,
                "dominant_dimension":
                    dominant_dimension,
                "dominant_dimension_score":
                    round(
                        averages[
                            dominant_dimension
                        ],
                        2
                    )
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            "dominant_dimension_score",
            ascending=False
        )
    )


# ============================================================
# PRINT REPORT
# ============================================================

def print_report(
    df,
    segment_metrics,
    segment_drivers
):

    print("\n")
    print("=" * 60)
    print("CUSTOMER RISK SEGMENTATION REPORT")
    print("=" * 60)

    # --------------------------------------------------------
    # Population
    # --------------------------------------------------------

    print(
        "\nCUSTOMER POPULATION"
    )

    print("-" * 40)

    print(
        "Total customers:",
        f"{len(df):,}"
    )

    # --------------------------------------------------------
    # Distribution
    # --------------------------------------------------------

    print(
        "\nRISK SEGMENT DISTRIBUTION"
    )

    print("-" * 40)

    distribution = (
        df[
            "risk_segment"
        ]
        .value_counts()
    )

    print(
        distribution
    )

    # --------------------------------------------------------
    # Detailed metrics
    # --------------------------------------------------------

    print(
        "\nSEGMENT METRICS"
    )

    print("-" * 40)

    print(
        segment_metrics
        .sort_values(
            "average_risk_score",
            ascending=False
        )
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Dominant dimensions
    # --------------------------------------------------------

    print(
        "\nSEGMENT DOMINANT DIMENSIONS"
    )

    print("-" * 40)

    print(
        segment_drivers
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Top critical customers
    # --------------------------------------------------------

    print(
        "\nTOP CUSTOMERS BY SEGMENT RISK"
    )

    print("-" * 40)

    columns = [

        "customer_id",

        "first_name",

        "last_name",

        "risk_segment",

        "customer_risk_score",

        "severity_score",

        "frequency_score",

        "persistence_score",

        "problematic_journeys",

        "segment_reason"
    ]

    print(

        df
        .sort_values(
            "customer_risk_score",
            ascending=False
        )
        [
            columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_segments(
    df,
    segment_metrics,
    segment_drivers
):

    print("\n")
    print("=" * 60)
    print("CUSTOMER SEGMENTATION VALIDATION")
    print("=" * 60)

    checks = {}

    # --------------------------------------------------------
    # Segment column
    # --------------------------------------------------------

    checks[
        "Segments generated"
    ] = (
        df[
            "risk_segment"
        ]
        .notna()
        .all()
    )

    # --------------------------------------------------------
    # Segment reasons
    # --------------------------------------------------------

    checks[
        "Segment reasons generated"
    ] = (
        df[
            "segment_reason"
        ]
        .notna()
        .all()
    )

    # --------------------------------------------------------
    # Customer uniqueness
    # --------------------------------------------------------

    checks[
        "Unique customer IDs"
    ] = (
        df[
            "customer_id"
        ]
        .is_unique
    )

    # --------------------------------------------------------
    # Customer conservation
    # --------------------------------------------------------

    checks[
        "Customers conserved"
    ] = (

        segment_metrics[
            "customer_count"
        ]
        .sum()

        ==

        len(df)
    )

    # --------------------------------------------------------
    # Percentages
    # --------------------------------------------------------

    percentage_total = (
        segment_metrics[
            "customer_percentage"
        ]
        .sum()
    )

    checks[
        "Segment percentages valid"
    ] = np.isclose(
        percentage_total,
        100,
        atol=0.1
    )

    # --------------------------------------------------------
    # Valid dominant dimensions
    # --------------------------------------------------------

    checks[
        "Valid dominant dimensions"
    ] = (
        segment_drivers[
            "dominant_dimension"
        ]
        .isin(
            [
                "severity_score",
                "frequency_score",
                "persistence_score"
            ]
        )
        .all()
    )

    # --------------------------------------------------------
    # No invalid risk scores
    # --------------------------------------------------------

    checks[
        "Risk scores valid"
    ] = (
        df[
            "customer_risk_score"
        ]
        .between(
            0,
            100
        )
        .all()
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    for name, result in checks.items():

        print(
            f"{name}:",
            "PASS"
            if result
            else "FAIL"
        )

    overall = all(
        checks.values()
    )

    print(
        "\nOverall validation:",
        "PASSED"
        if overall
        else "FAILED"
    )

    return overall


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = load_data()

    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    df = prepare_data(
        df
    )

    # --------------------------------------------------------
    # Build segments
    # --------------------------------------------------------

    df = build_segments(
        df
    )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    segment_metrics = (
        calculate_segment_metrics(
            df
        )
    )

    # --------------------------------------------------------
    # Drivers
    # --------------------------------------------------------

    segment_drivers = (
        calculate_segment_drivers(
            df
        )
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print_report(
        df,
        segment_metrics,
        segment_drivers
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    validation_passed = (
        validate_segments(
            df,
            segment_metrics,
            segment_drivers
        )
    )

    # --------------------------------------------------------
    # Output columns
    # --------------------------------------------------------

    output_columns = [

        "customer_id",

        "first_name",

        "last_name",

        "country",

        "customer_segment",

        "total_bookings",

        "total_failed_payments",

        "total_retries",

        "total_anomalies",

        "problematic_journeys",

        "severity_score",

        "frequency_score",

        "persistence_score",

        "customer_risk_score",

        "customer_risk_level",

        "behavior_profile",

        "risk_segment",

        "segment_reason"
    ]

    output_columns = [
        column
        for column in output_columns
        if column in df.columns
    ]

    output_df = df[
        output_columns
    ].copy()

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)

    if validation_passed:

        print(
            "CUSTOMER SEGMENTATION SUCCESS"
        )

    else:

        print(
            "CUSTOMER SEGMENTATION FAILED"
        )

    print("=" * 60)

    print(
        "\nOutput file:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nCustomers:",
        f"{len(output_df):,}"
    )

    print(
        "Features:",
        f"{len(output_df.columns):,}"
    )