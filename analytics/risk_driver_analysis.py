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
    / "risk_driver_analysis.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("=" * 60)
    print("RISK DRIVER ANALYSIS")
    print("=" * 60)

    print("\nLoading customer risk model...")

    df = pd.read_csv(INPUT_FILE)

    print(
        f"Customers: {len(df):,}"
    )

    print(
        f"Risk dimensions: "
        f"{len(df.columns):,}"
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
        "average_friction_score",
        "maximum_friction_score",
        "high_risk_journeys",
        "critical_journeys",
        "problematic_journeys"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            ).fillna(0)

    return df


# ============================================================
# CORRELATION ANALYSIS
# ============================================================

def calculate_correlations(df):

    print("\nCalculating risk-driver correlations...")

    drivers = [
        "severity_score",
        "frequency_score",
        "persistence_score",
        "total_failed_payments",
        "total_retries",
        "total_anomalies",
        "maximum_friction_score",
        "average_friction_score",
        "high_risk_journeys",
        "critical_journeys",
        "problematic_journeys",
        "total_bookings"
    ]

    results = []

    for driver in drivers:

        if driver not in df.columns:
            continue

        correlation = (
            df[driver]
            .corr(
                df["customer_risk_score"]
            )
        )

        results.append(
            {
                "risk_driver": driver,
                "correlation_with_customer_risk": round(
                    correlation,
                    4
                )
            }
        )

    correlation_df = (
        pd.DataFrame(results)
        .sort_values(
            "correlation_with_customer_risk",
            ascending=False
        )
        .reset_index(drop=True)
    )

    return correlation_df


# ============================================================
# RISK GROUP COMPARISON
# ============================================================

def calculate_risk_groups(df):

    print(
        "Comparing LOW-risk and HIGH/CRITICAL customers..."
    )

    df["risk_group"] = np.where(
        df["customer_risk_level"].isin(
            [
                "HIGH",
                "CRITICAL"
            ]
        ),
        "HIGH_CRITICAL",
        "LOW_MEDIUM"
    )

    metrics = [
        "severity_score",
        "frequency_score",
        "persistence_score",
        "total_failed_payments",
        "total_retries",
        "total_anomalies",
        "average_friction_score",
        "problematic_journeys"
    ]

    rows = []

    for group, group_df in df.groupby(
        "risk_group"
    ):

        for metric in metrics:

            if metric not in group_df.columns:
                continue

            rows.append(
                {
                    "risk_group": group,
                    "metric": metric,
                    "customer_count": len(group_df),
                    "average_value": round(
                        group_df[metric].mean(),
                        2
                    ),
                    "median_value": round(
                        group_df[metric].median(),
                        2
                    )
                }
            )

    return pd.DataFrame(rows)


# ============================================================
# RISK DIMENSION ANALYSIS
# ============================================================

def calculate_dimension_summary(df):

    print(
        "Analyzing risk dimensions..."
    )

    dimensions = [
        "severity_score",
        "frequency_score",
        "persistence_score"
    ]

    rows = []

    for dimension in dimensions:

        if dimension not in df.columns:
            continue

        rows.append(
            {
                "dimension": dimension,
                "average": round(
                    df[dimension].mean(),
                    2
                ),
                "median": round(
                    df[dimension].median(),
                    2
                ),
                "minimum": round(
                    df[dimension].min(),
                    2
                ),
                "maximum": round(
                    df[dimension].max(),
                    2
                )
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# HIGH-RISK DRIVER ANALYSIS
# ============================================================

def calculate_high_risk_drivers(df):

    print(
        "Analyzing high-risk customer drivers..."
    )

    high_risk = df[
        df["customer_risk_level"].isin(
            [
                "HIGH",
                "CRITICAL"
            ]
        )
    ].copy()

    if len(high_risk) == 0:

        return pd.DataFrame(
            columns=[
                "driver",
                "average_value"
            ]
        )

    drivers = [
        "severity_score",
        "frequency_score",
        "persistence_score",
        "total_failed_payments",
        "total_retries",
        "total_anomalies",
        "problematic_journeys"
    ]

    rows = []

    for driver in drivers:

        if driver not in high_risk.columns:
            continue

        rows.append(
            {
                "driver": driver,
                "average_value": round(
                    high_risk[driver].mean(),
                    2
                )
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            "average_value",
            ascending=False
        )
        .reset_index(drop=True)
    )


# ============================================================
# RESEARCH STATISTICS
# ============================================================

def calculate_research_statistics(df):

    print(
        "Calculating research statistics..."
    )

    high_risk = df[
        df["customer_risk_level"].isin(
            [
                "HIGH",
                "CRITICAL"
            ]
        )
    ]

    low_risk = df[
        df["customer_risk_level"]
        == "LOW"
    ]

    metrics = [
        "severity_score",
        "frequency_score",
        "persistence_score",
        "total_failed_payments",
        "total_anomalies",
        "average_friction_score",
        "problematic_journeys"
    ]

    rows = []

    for metric in metrics:

        high_mean = (
            high_risk[metric].mean()
            if len(high_risk) > 0
            else 0
        )

        low_mean = (
            low_risk[metric].mean()
            if len(low_risk) > 0
            else 0
        )

        difference = (
            high_mean - low_mean
        )

        if low_mean != 0:

            percentage_difference = (
                difference
                /
                abs(low_mean)
                * 100
            )

        else:

            percentage_difference = np.nan

        rows.append(
            {
                "metric": metric,
                "high_critical_average": round(
                    high_mean,
                    2
                ),
                "low_average": round(
                    low_mean,
                    2
                ),
                "absolute_difference": round(
                    difference,
                    2
                ),
                "percentage_difference": round(
                    percentage_difference,
                    2
                )
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# PRINT REPORT
# ============================================================

def print_report(
    df,
    correlations,
    groups,
    dimensions,
    high_risk_drivers,
    research_stats
):

    print("\n")
    print("=" * 60)
    print("RISK DRIVER ANALYSIS REPORT")
    print("=" * 60)

    # --------------------------------------------------------
    # Overall population
    # --------------------------------------------------------

    print(
        "\nCUSTOMER POPULATION"
    )

    print("-" * 40)

    print(
        "Total customers:",
        f"{len(df):,}"
    )

    print(
        "HIGH/CRITICAL customers:",
        (
            df[
                "customer_risk_level"
            ]
            .isin(
                [
                    "HIGH",
                    "CRITICAL"
                ]
            )
            .sum()
        )
    )

    print(
        "LOW-risk customers:",
        (
            df[
                "customer_risk_level"
            ]
            == "LOW"
        ).sum()
    )

    # --------------------------------------------------------
    # Correlation
    # --------------------------------------------------------

    print(
        "\nRISK DRIVER CORRELATION"
    )

    print("-" * 40)

    print(
        correlations.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Risk dimensions
    # --------------------------------------------------------

    print(
        "\nRISK DIMENSION SUMMARY"
    )

    print("-" * 40)

    print(
        dimensions.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # High-risk drivers
    # --------------------------------------------------------

    print(
        "\nHIGH/CRITICAL CUSTOMER DRIVER PROFILE"
    )

    print("-" * 40)

    print(
        high_risk_drivers.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Group comparison
    # --------------------------------------------------------

    print(
        "\nHIGH/CRITICAL VS LOW-RISK COMPARISON"
    )

    print("-" * 40)

    print(
        research_stats.to_string(
            index=False
        )
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_analysis(
    df,
    correlations,
    groups,
    dimensions
):

    print("\n")
    print("=" * 60)
    print("RISK DRIVER ANALYSIS VALIDATION")
    print("=" * 60)

    checks = {}

    # --------------------------------------------------------
    # Customer IDs
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
    # Correlation generated
    # --------------------------------------------------------

    checks[
        "Correlation analysis generated"
    ] = (
        len(correlations) > 0
    )

    # --------------------------------------------------------
    # Dimension analysis
    # --------------------------------------------------------

    checks[
        "Risk dimensions analyzed"
    ] = (
        len(dimensions) == 3
    )

    # --------------------------------------------------------
    # Required dimensions
    # --------------------------------------------------------

    required_dimensions = {
        "severity_score",
        "frequency_score",
        "persistence_score"
    }

    actual_dimensions = set(
        dimensions[
            "dimension"
        ]
    )

    checks[
        "All risk dimensions present"
    ] = (
        required_dimensions
        .issubset(
            actual_dimensions
        )
    )

    # --------------------------------------------------------
    # No invalid correlations
    # --------------------------------------------------------

    checks[
        "Valid correlations"
    ] = (
        correlations[
            "correlation_with_customer_risk"
        ]
        .between(
            -1,
            1
        )
        .all()
    )

    # --------------------------------------------------------
    # Risk group created
    # --------------------------------------------------------

    checks[
        "Risk groups generated"
    ] = (
        df[
            "risk_group"
        ]
        .notna()
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
    # Correlations
    # --------------------------------------------------------

    correlations = (
        calculate_correlations(
            df
        )
    )

    # --------------------------------------------------------
    # Risk groups
    # --------------------------------------------------------

    groups = (
        calculate_risk_groups(
            df
        )
    )

    # --------------------------------------------------------
    # Dimensions
    # --------------------------------------------------------

    dimensions = (
        calculate_dimension_summary(
            df
        )
    )

    # --------------------------------------------------------
    # High-risk drivers
    # --------------------------------------------------------

    high_risk_drivers = (
        calculate_high_risk_drivers(
            df
        )
    )

    # --------------------------------------------------------
    # Research statistics
    # --------------------------------------------------------

    research_stats = (
        calculate_research_statistics(
            df
        )
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print_report(
        df,
        correlations,
        groups,
        dimensions,
        high_risk_drivers,
        research_stats
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    validation_passed = (
        validate_analysis(
            df,
            correlations,
            groups,
            dimensions
        )
    )

    # --------------------------------------------------------
    # Save combined driver table
    # --------------------------------------------------------

    output_df = correlations.copy()

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
            "RISK DRIVER ANALYSIS SUCCESS"
        )

    else:

        print(
            "RISK DRIVER ANALYSIS FAILED"
        )

    print("=" * 60)

    print(
        "\nOutput file:"
    )

    print(
        OUTPUT_FILE
    )