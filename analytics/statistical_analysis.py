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

PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

JOURNEY_FILE = os.path.join(
    PROCESSED_DIR,
    "customer_journey_features.csv"
)

CUSTOMER_RISK_FILE = os.path.join(
    PROCESSED_DIR,
    "customer_risk_model.csv"
)

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day5_statistical_report.csv"
)


# ============================================================
# CONSTANTS
# ============================================================

CONFIDENCE_LEVEL = 0.95
Z_VALUE = 1.96


# ============================================================
# LOAD DATA
# ============================================================

def load_csv(path, name):

    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"{name} not found:\n{path}"
        )

    try:
        return pd.read_csv(path)

    except Exception as exc:
        raise RuntimeError(
            f"Could not load {name}: {exc}"
        )


# ============================================================
# CONFIDENCE INTERVAL
# ============================================================

def calculate_confidence_interval(series):

    values = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()

    n = len(values)

    if n == 0:
        return np.nan, np.nan

    mean = values.mean()

    if n == 1:
        return mean, mean

    std = values.std(
        ddof=1
    )

    standard_error = (
        std /
        np.sqrt(n)
    )

    margin = (
        Z_VALUE *
        standard_error
    )

    lower = mean - margin
    upper = mean + margin

    return lower, upper


# ============================================================
# PROFILE ONE NUMERIC METRIC
# ============================================================

def profile_metric(
    dataset_name,
    metric_name,
    series,
    probability=None
):

    values = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()

    if values.empty:

        return {
            "dataset": dataset_name,
            "metric": metric_name,
            "count": 0,
            "mean": np.nan,
            "median": np.nan,
            "variance": np.nan,
            "standard_deviation": np.nan,
            "minimum": np.nan,
            "maximum": np.nan,
            "probability": probability,
            "confidence_level": CONFIDENCE_LEVEL,
            "confidence_interval_lower": np.nan,
            "confidence_interval_upper": np.nan
        }

    ci_lower, ci_upper = (
        calculate_confidence_interval(
            values
        )
    )

    return {
        "dataset": dataset_name,
        "metric": metric_name,
        "count": int(len(values)),
        "mean": round(
            values.mean(),
            4
        ),
        "median": round(
            values.median(),
            4
        ),
        "variance": round(
            values.var(
                ddof=1
            ),
            4
        ) if len(values) > 1 else 0.0,
        "standard_deviation": round(
            values.std(
                ddof=1
            ),
            4
        ) if len(values) > 1 else 0.0,
        "minimum": round(
            values.min(),
            4
        ),
        "maximum": round(
            values.max(),
            4
        ),
        "probability": (
            round(
                probability,
                4
            )
            if probability is not None
            else np.nan
        ),
        "confidence_level": CONFIDENCE_LEVEL,
        "confidence_interval_lower": round(
            ci_lower,
            4
        ),
        "confidence_interval_upper": round(
            ci_upper,
            4
        )
    }


# ============================================================
# PROBABILITY HELPER
# ============================================================

def calculate_probability(condition_series):

    condition = pd.Series(
        condition_series
    ).fillna(False)

    if len(condition) == 0:
        return np.nan

    true_count = int(
        condition.astype(bool).sum()
    )

    total_count = int(
        len(condition)
    )

    return true_count / total_count


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 5 — STATISTICAL ANALYSIS ENGINE")
    print("=" * 60)

    # ========================================================
    # LOAD
    # ========================================================

    print("\nLoading analytical datasets...")

    journey = load_csv(
        JOURNEY_FILE,
        "customer_journey_features.csv"
    )

    customer_risk = load_csv(
        CUSTOMER_RISK_FILE,
        "customer_risk_model.csv"
    )

    print(
        f"Journey records: {len(journey):,}"
    )

    print(
        f"Customer records: {len(customer_risk):,}"
    )

    # ========================================================
    # PREPARE JOURNEY NUMERIC COLUMNS
    # ========================================================

    journey_numeric_columns = [

        "booking_amount",
        "payment_attempts",
        "failed_payments",
        "successful_payments",
        "retry_count",
        "payment_success_rate",
        "payment_duration_minutes",
        "total_events",
        "journey_duration_minutes",
        "friction_score"
    ]

    for column in journey_numeric_columns:

        if column in journey.columns:

            journey[column] = pd.to_numeric(
                journey[column],
                errors="coerce"
            )

    # ========================================================
    # PREPARE CUSTOMER RISK NUMERIC COLUMNS
    # ========================================================

    risk_numeric_columns = [

        "total_bookings",
        "total_failed_payments",
        "total_retries",
        "total_anomalies",
        "problematic_journeys",
        "severity_score",
        "frequency_score",
        "persistence_score",
        "customer_risk_score",
        "average_friction_score",
        "maximum_friction_score"
    ]

    for column in risk_numeric_columns:

        if column in customer_risk.columns:

            customer_risk[column] = pd.to_numeric(
                customer_risk[column],
                errors="coerce"
            )

    # ========================================================
    # DESCRIPTIVE STATISTICS
    # ========================================================

    print(
        "\nCalculating descriptive statistics..."
    )

    results = []

    # ========================================================
    # JOURNEY METRICS
    # ========================================================

    journey_metrics = [

        "booking_amount",
        "payment_attempts",
        "failed_payments",
        "retry_count",
        "payment_success_rate",
        "payment_duration_minutes",
        "total_events",
        "journey_duration_minutes",
        "friction_score"
    ]

    for metric in journey_metrics:

        if metric not in journey.columns:
            continue

        results.append(
            profile_metric(
                "journey",
                metric,
                journey[metric]
            )
        )

    # ========================================================
    # CUSTOMER RISK METRICS
    # ========================================================

    customer_metrics = [

        "total_bookings",
        "total_failed_payments",
        "total_retries",
        "total_anomalies",
        "problematic_journeys",
        "severity_score",
        "frequency_score",
        "persistence_score",
        "customer_risk_score",
        "average_friction_score",
        "maximum_friction_score"
    ]

    for metric in customer_metrics:

        if metric not in customer_risk.columns:
            continue

        results.append(
            profile_metric(
                "customer_risk",
                metric,
                customer_risk[metric]
            )
        )

    # ========================================================
    # PROBABILITY ANALYSIS
    # ========================================================

    print(
        "Calculating probabilities..."
    )

    # --------------------------------------------------------
    # Probability of at least one failed payment
    # --------------------------------------------------------

    if "failed_payments" in journey.columns:

        failed_condition = (
            journey["failed_payments"]
            .fillna(0)
            .gt(0)
        )

        failed_probability = (
            calculate_probability(
                failed_condition
            )
        )

        results.append(
            profile_metric(
                "journey",
                "probability_failed_payment",
                failed_condition.astype(int),
                failed_probability
            )
        )

    # --------------------------------------------------------
    # Probability of at least one retry
    # --------------------------------------------------------

    if "retry_count" in journey.columns:

        retry_condition = (
            journey["retry_count"]
            .fillna(0)
            .gt(0)
        )

        retry_probability = (
            calculate_probability(
                retry_condition
            )
        )

        results.append(
            profile_metric(
                "journey",
                "probability_payment_retry",
                retry_condition.astype(int),
                retry_probability
            )
        )

    # --------------------------------------------------------
    # Probability of an anomalous journey
    # --------------------------------------------------------

    if "anomaly_summary" in journey.columns:

        anomaly_condition = (
            journey["anomaly_summary"]
            .fillna("NO_ANOMALY")
            .astype(str)
            .ne("NO_ANOMALY")
        )

        anomaly_probability = (
            calculate_probability(
                anomaly_condition
            )
        )

        results.append(
            profile_metric(
                "journey",
                "probability_anomaly",
                anomaly_condition.astype(int),
                anomaly_probability
            )
        )

    # --------------------------------------------------------
    # Probability of HIGH / CRITICAL customer
    # --------------------------------------------------------

    if "customer_risk_level" in customer_risk.columns:

        high_critical_condition = (
            customer_risk[
                "customer_risk_level"
            ]
            .fillna("")
            .astype(str)
            .str.upper()
            .isin(
                [
                    "HIGH",
                    "CRITICAL"
                ]
            )
        )

        high_critical_probability = (
            calculate_probability(
                high_critical_condition
            )
        )

        results.append(
            profile_metric(
                "customer_risk",
                "probability_high_or_critical_risk",
                high_critical_condition.astype(int),
                high_critical_probability
            )
        )

    # ========================================================
    # BUILD REPORT
    # ========================================================

    report = pd.DataFrame(
        results
    )

    # ========================================================
    # ROUND REPORT VALUES
    # ========================================================

    numeric_report_columns = [

        "mean",
        "median",
        "variance",
        "standard_deviation",
        "minimum",
        "maximum",
        "confidence_interval_lower",
        "confidence_interval_upper"
    ]

    for column in numeric_report_columns:

        if column in report.columns:

            report[column] = pd.to_numeric(
                report[column],
                errors="coerce"
            ).round(4)

    report["probability"] = pd.to_numeric(
        report["probability"],
        errors="coerce"
    ).round(4)

    # ========================================================
    # SAVE
    # ========================================================

    os.makedirs(
        PROCESSED_DIR,
        exist_ok=True
    )

    report.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # STATISTICAL SUMMARY
    # ========================================================

    print()
    print("=" * 60)
    print("STATISTICAL SUMMARY")
    print("=" * 60)

    display_columns = [

        "dataset",
        "metric",
        "count",
        "mean",
        "median",
        "variance",
        "standard_deviation",
        "probability",
        "confidence_interval_lower",
        "confidence_interval_upper"
    ]

    print(
        report[
            display_columns
        ].to_string(
            index=False
        )
    )

    # ========================================================
    # KEY FINDINGS
    # ========================================================

    print()
    print("=" * 60)
    print("KEY STATISTICAL FINDINGS")
    print("=" * 60)

    # --------------------------------------------------------
    # Friction
    # --------------------------------------------------------

    friction = report[
        (
            report["dataset"]
            == "journey"
        )
        &
        (
            report["metric"]
            == "friction_score"
        )
    ]

    if not friction.empty:

        row = friction.iloc[0]

        print()
        print("Friction Score")

        print(
            f"  Mean: {row['mean']:.2f}"
        )

        print(
            f"  Median: {row['median']:.2f}"
        )

        print(
            f"  Std Dev: "
            f"{row['standard_deviation']:.2f}"
        )

        print(
            f"  95% CI: "
            f"["
            f"{row['confidence_interval_lower']:.2f}, "
            f"{row['confidence_interval_upper']:.2f}"
            f"]"
        )

    # --------------------------------------------------------
    # Customer risk
    # --------------------------------------------------------

    risk_score = report[
        (
            report["dataset"]
            == "customer_risk"
        )
        &
        (
            report["metric"]
            == "customer_risk_score"
        )
    ]

    if not risk_score.empty:

        row = risk_score.iloc[0]

        print()
        print("Customer Risk Score")

        print(
            f"  Mean: {row['mean']:.2f}"
        )

        print(
            f"  Median: {row['median']:.2f}"
        )

        print(
            f"  Std Dev: "
            f"{row['standard_deviation']:.2f}"
        )

        print(
            f"  95% CI: "
            f"["
            f"{row['confidence_interval_lower']:.2f}, "
            f"{row['confidence_interval_upper']:.2f}"
            f"]"
        )

    # --------------------------------------------------------
    # Probabilities
    # --------------------------------------------------------

    probabilities = report[
        report["metric"]
        .astype(str)
        .str.startswith(
            "probability_"
        )
    ]

    print()
    print("Probabilities")

    for _, row in probabilities.iterrows():

        if pd.notna(
            row["probability"]
        ):

            print(
                f"  {row['metric']}: "
                f"{row['probability']:.2%}"
            )

    # ========================================================
    # VALIDITY CHECKS
    # ========================================================

    print()
    print("=" * 60)
    print("STATISTICAL ENGINE VALIDATION")
    print("=" * 60)

    required_stat_columns = [

        "mean",
        "median",
        "variance",
        "standard_deviation",
        "probability",
        "confidence_level",
        "confidence_interval_lower",
        "confidence_interval_upper"
    ]

    checks = []

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    missing_columns = [
        column
        for column in required_stat_columns
        if column not in report.columns
    ]

    checks.append(
        (
            "Required statistical columns exist",
            len(missing_columns) == 0,
            (
                "All required columns present"
                if not missing_columns
                else f"Missing={missing_columns}"
            )
        )
    )

    # --------------------------------------------------------
    # Mean/median values
    # --------------------------------------------------------

    checks.append(
        (
            "Mean values generated",
            report["mean"].notna().any(),
            "At least one mean calculated"
        )
    )

    checks.append(
        (
            "Median values generated",
            report["median"].notna().any(),
            "At least one median calculated"
        )
    )

    # --------------------------------------------------------
    # Variance
    # --------------------------------------------------------

    checks.append(
        (
            "Variance values are non-negative",
            report[
                "variance"
            ]
            .dropna()
            .ge(0)
            .all(),
            "Variance >= 0"
        )
    )

    # --------------------------------------------------------
    # Standard deviation
    # --------------------------------------------------------

    checks.append(
        (
            "Standard deviations are non-negative",
            report[
                "standard_deviation"
            ]
            .dropna()
            .ge(0)
            .all(),
            "Standard deviation >= 0"
        )
    )

    # --------------------------------------------------------
    # Confidence level
    # --------------------------------------------------------

    checks.append(
        (
            "Confidence level is 95%",
            (
                report[
                    "confidence_level"
                ]
                == 0.95
            ).all(),
            "Confidence level = 0.95"
        )
    )

    # --------------------------------------------------------
    # Probability range
    # --------------------------------------------------------

    probability_values = (
        report["probability"]
        .dropna()
    )

    checks.append(
        (
            "Probabilities are within 0-1",
            probability_values
            .between(
                0,
                1
            )
            .all(),
            (
                f"Min={probability_values.min():.4f}, "
                f"Max={probability_values.max():.4f}"
            )
            if not probability_values.empty
            else "No probabilities"
        )
    )

    # --------------------------------------------------------
    # Confidence interval ordering
    # --------------------------------------------------------

    ci_data = report[
        [
            "confidence_interval_lower",
            "confidence_interval_upper"
        ]
    ].dropna()

    ci_valid = (
        ci_data[
            "confidence_interval_lower"
        ]
        <=
        ci_data[
            "confidence_interval_upper"
        ]
    ).all()

    checks.append(
        (
            "Confidence intervals are ordered correctly",
            bool(ci_valid),
            (
                f"Checked={len(ci_data):,} metrics"
            )
        )
    )

    # --------------------------------------------------------
    # Probability consistency
    # --------------------------------------------------------

    expected_probability_metrics = {
        "probability_failed_payment",
        "probability_payment_retry",
        "probability_anomaly",
        "probability_high_or_critical_risk"
    }

    actual_probability_metrics = set(
        report[
            report["metric"]
            .astype(str)
            .str.startswith("probability_")
        ]["metric"]
    )

    checks.append(
        (
            "Required probability metrics generated",
            expected_probability_metrics
            .issubset(
                actual_probability_metrics
            ),
            (
                f"Found="
                f"{sorted(actual_probability_metrics)}"
            )
        )
    )

    # ========================================================
    # PRINT VALIDATION
    # ========================================================

    passed = 0

    for name, condition, detail in checks:

        status = (
            "PASS"
            if condition
            else "FAIL"
        )

        print(
            f"{name}: {status}"
        )

        if detail:
            print(
                f"    {detail}"
            )

        if condition:
            passed += 1

    failed = (
        len(checks)
        -
        passed
    )

    print()
    print(
        f"Total checks: {len(checks)}"
    )

    print(
        f"Passed: {passed}"
    )

    print(
        f"Failed: {failed}"
    )

    print()

    if failed == 0:

        print("=" * 60)
        print(
            "DAY 5 STATISTICAL ENGINE: PASSED"
        )
        print("=" * 60)

        print()
        print(
            "Statistical analysis successfully "
            "generated validated descriptive "
            "statistics, probabilities, and "
            "confidence intervals."
        )

        print()
        print(
            "Output file:"
        )

        print(
            OUTPUT_FILE
        )

        print()
        print(
            f"Statistical records: "
            f"{len(report):,}"
        )

        return 0

    print("=" * 60)
    print(
        "DAY 5 STATISTICAL ENGINE: FAILED"
    )
    print("=" * 60)

    print()
    print(
        "Fix the failed checks before "
        "continuing Day 5."
    )

    return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )