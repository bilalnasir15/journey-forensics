import os
import sys

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

KPI_FILE = os.path.join(
    PROCESSED_DIR,
    "day5_kpi_report.csv"
)

STAT_FILE = os.path.join(
    PROCESSED_DIR,
    "day5_statistical_report.csv"
)

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day5_kpi_statistics_validation.csv"
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
# LOAD FILE
# ============================================================

def load_file(
    path,
    name
):

    if not os.path.isfile(path):

        check(
            f"{name} exists",
            False,
            path
        )

        return None

    try:

        df = pd.read_csv(
            path
        )

        check(
            f"{name} exists and loads",
            True,
            f"{len(df):,} records"
        )

        return df

    except Exception as exc:

        check(
            f"{name} exists and loads",
            False,
            str(exc)
        )

        return None


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 5 KPI + STATISTICS VALIDATION")
    print("=" * 60)

    print()

    # ========================================================
    # LOAD
    # ========================================================

    kpi = load_file(
        KPI_FILE,
        "KPI report"
    )

    statistics = load_file(
        STAT_FILE,
        "Statistical report"
    )

    if kpi is None or statistics is None:

        print()
        print("=" * 60)
        print(
            "DAY 5 VALIDATION: FAILED"
        )
        print("=" * 60)

        return 1

    # ========================================================
    # KPI STRUCTURE
    # ========================================================

    print()
    print("Validating KPI layer...")

    required_kpi_columns = {

        "kpi_name",
        "value",
        "unit",
        "status",
        "definition"
    }

    missing_kpi_columns = (
        required_kpi_columns
        -
        set(kpi.columns)
    )

    check(
        "Required KPI columns exist",
        len(missing_kpi_columns) == 0,
        (
            "All required columns present"
            if not missing_kpi_columns
            else f"Missing={sorted(missing_kpi_columns)}"
        )
    )

    # --------------------------------------------------------
    # Required KPI names
    # --------------------------------------------------------

    required_kpis = {

        "TOTAL_CUSTOMERS",

        "TOTAL_BOOKINGS",

        "TOTAL_PAYMENT_ATTEMPTS",

        "TOTAL_EVENTS",

        "BOOKING_CONVERSION_RATE",

        "BOOKING_CONFIRMATION_RATE",

        "CANCELLATION_RATE",

        "PAYMENT_SUCCESS_RATE",

        "PAYMENT_FAILURE_RATE",

        "RETRY_RATE",

        "BOOKING_RETRY_RATE",

        "REPEAT_CUSTOMER_RATE",

        "RETENTION_PROXY_RATE",

        "TOTAL_REVENUE",

        "REVENUE_PER_CUSTOMER",

        "AVERAGE_BOOKING_VALUE",

        "ANOMALY_RATE",

        "AVERAGE_JOURNEY_DURATION",

        "AVERAGE_PAYMENT_DURATION",

        "AVERAGE_FRICTION_SCORE",

        "COMPLAINT_RATE",

        "COMPLAINT_RESOLUTION_TIME"
    }

    actual_kpis = set(
        kpi[
            "kpi_name"
        ]
        .astype(str)
    )

    missing_kpis = (
        required_kpis
        -
        actual_kpis
    )

    check(
        "All roadmap KPI definitions represented",
        len(missing_kpis) == 0,
        (
            "All KPI definitions present"
            if not missing_kpis
            else f"Missing={sorted(missing_kpis)}"
        )
    )

    # --------------------------------------------------------
    # KPI value range
    # --------------------------------------------------------

    rates = kpi[
        kpi["unit"] == "rate"
    ].copy()

    if not rates.empty:

        rate_values = pd.to_numeric(
            rates["value"],
            errors="coerce"
        )

        # NOT_SUPPORTED KPIs legitimately have NaN
        available_rate_values = (
            rate_values[
                rates["status"]
                != "NOT_SUPPORTED"
            ]
        )

        check(
            "Available KPI rates are within 0-1",
            available_rate_values
            .between(0, 1)
            .all(),
            (
                f"Min={available_rate_values.min():.4f}, "
                f"Max={available_rate_values.max():.4f}"
            )
        )

    # --------------------------------------------------------
    # Unsupported complaint metrics
    # --------------------------------------------------------

    complaint_rows = kpi[
        kpi["kpi_name"].isin(
            [
                "COMPLAINT_RATE",
                "COMPLAINT_RESOLUTION_TIME"
            ]
        )
    ]

    complaint_status_valid = (
        complaint_rows[
            "status"
        ]
        .eq("NOT_SUPPORTED")
        .all()
    )

    check(
        "Unsupported complaint KPIs explicitly flagged",
        complaint_status_valid,
        "Complaint data is not available in current dataset"
    )

    # ========================================================
    # STATISTICAL STRUCTURE
    # ========================================================

    print()
    print("Validating statistical layer...")

    required_stat_columns = {

        "dataset",

        "metric",

        "count",

        "mean",

        "median",

        "variance",

        "standard_deviation",

        "probability",

        "confidence_level",

        "confidence_interval_lower",

        "confidence_interval_upper"
    }

    missing_stat_columns = (
        required_stat_columns
        -
        set(statistics.columns)
    )

    check(
        "Required statistical columns exist",
        len(missing_stat_columns) == 0,
        (
            "All required columns present"
            if not missing_stat_columns
            else f"Missing={sorted(missing_stat_columns)}"
        )
    )

    # ========================================================
    # DESCRIPTIVE STATISTICS
    # ========================================================

    check(
        "Mean statistics generated",
        statistics["mean"]
        .notna()
        .any(),
        "Mean values available"
    )

    check(
        "Median statistics generated",
        statistics["median"]
        .notna()
        .any(),
        "Median values available"
    )

    check(
        "Variance statistics are valid",
        statistics["variance"]
        .dropna()
        .ge(0)
        .all(),
        "Variance >= 0"
    )

    check(
        "Standard deviation statistics are valid",
        statistics["standard_deviation"]
        .dropna()
        .ge(0)
        .all(),
        "Standard deviation >= 0"
    )

    # ========================================================
    # CONFIDENCE INTERVALS
    # ========================================================

    ci_data = statistics[
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

    check(
        "Confidence intervals are valid",
        bool(ci_valid),
        f"Checked={len(ci_data):,}"
    )

    # --------------------------------------------------------
    # Confidence level
    # --------------------------------------------------------

    check(
        "Confidence level is 95%",
        (
            statistics[
                "confidence_level"
            ]
            == 0.95
        ).all(),
        "confidence_level = 0.95"
    )

    # ========================================================
    # PROBABILITIES
    # ========================================================

    probability_values = (
        statistics[
            "probability"
        ]
        .dropna()
    )

    check(
        "Probabilities are within 0-1",
        probability_values
        .between(0, 1)
        .all(),
        (
            f"Min={probability_values.min():.4f}, "
            f"Max={probability_values.max():.4f}"
        )
        if not probability_values.empty
        else "No probabilities found"
    )

    required_probability_metrics = {

        "probability_failed_payment",

        "probability_payment_retry",

        "probability_anomaly",

        "probability_high_or_critical_risk"
    }

    actual_probability_metrics = set(
        statistics[
            statistics[
                "metric"
            ]
            .astype(str)
            .str.startswith(
                "probability_"
            )
        ][
            "metric"
        ]
    )

    check(
        "All required probability metrics generated",
        required_probability_metrics
        .issubset(
            actual_probability_metrics
        ),
        (
            f"Found={sorted(actual_probability_metrics)}"
        )
    )

    # ========================================================
    # DATASET COUNTS
    # ========================================================

    print()
    print("Validating dataset counts...")

    # --------------------------------------------------------
    # KPI total customer
    # --------------------------------------------------------

    customer_kpi = kpi[
        kpi["kpi_name"]
        == "TOTAL_CUSTOMERS"
    ]

    if not customer_kpi.empty:

        customer_value = pd.to_numeric(
            customer_kpi.iloc[0]["value"],
            errors="coerce"
        )

        check(
            "Total customer KPI = 5,000",
            customer_value == 5000,
            f"Actual={customer_value}"
        )

    # --------------------------------------------------------
    # Total bookings
    # --------------------------------------------------------

    booking_kpi = kpi[
        kpi["kpi_name"]
        == "TOTAL_BOOKINGS"
    ]

    if not booking_kpi.empty:

        booking_value = pd.to_numeric(
            booking_kpi.iloc[0]["value"],
            errors="coerce"
        )

        check(
            "Total booking KPI = 8,000",
            booking_value == 8000,
            f"Actual={booking_value}"
        )

    # --------------------------------------------------------
    # Payment attempts
    # --------------------------------------------------------

    payment_kpi = kpi[
        kpi["kpi_name"]
        == "TOTAL_PAYMENT_ATTEMPTS"
    ]

    if not payment_kpi.empty:

        payment_value = pd.to_numeric(
            payment_kpi.iloc[0]["value"],
            errors="coerce"
        )

        check(
            "Payment attempts KPI = 10,557",
            payment_value == 10557,
            f"Actual={payment_value}"
        )

    # --------------------------------------------------------
    # Events
    # --------------------------------------------------------

    event_kpi = kpi[
        kpi["kpi_name"]
        == "TOTAL_EVENTS"
    ]

    if not event_kpi.empty:

        event_value = pd.to_numeric(
            event_kpi.iloc[0]["value"],
            errors="coerce"
        )

        check(
            "Event KPI = 61,673",
            event_value == 61673,
            f"Actual={event_value}"
        )

    # ========================================================
    # KEY KPI CONSISTENCY
    # ========================================================

    print()
    print("Validating KPI relationships...")

    # --------------------------------------------------------
    # Payment success + failure
    # --------------------------------------------------------

    success_row = kpi[
        kpi["kpi_name"]
        == "PAYMENT_SUCCESS_RATE"
    ]

    failure_row = kpi[
        kpi["kpi_name"]
        == "PAYMENT_FAILURE_RATE"
    ]

    if (
        not success_row.empty
        and not failure_row.empty
    ):

        success = float(
            success_row.iloc[0]["value"]
        )

        failure = float(
            failure_row.iloc[0]["value"]
        )

        check(
            "Payment success + failure = 100%",
            abs(
                (
                    success
                    +
                    failure
                )
                - 1.0
            ) < 0.0001,
            (
                f"Success={success:.4f}, "
                f"Failure={failure:.4f}"
            )
        )

    # --------------------------------------------------------
    # Booking confirmation + cancellation + pending
    # --------------------------------------------------------

    confirmation = kpi[
        kpi["kpi_name"]
        == "BOOKING_CONFIRMATION_RATE"
    ]

    cancellation = kpi[
        kpi["kpi_name"]
        == "CANCELLATION_RATE"
    ]

    if (
        not confirmation.empty
        and not cancellation.empty
    ):

        confirmation_value = float(
            confirmation.iloc[0]["value"]
        )

        cancellation_value = float(
            cancellation.iloc[0]["value"]
        )

        # Pending rate can be calculated from booking statuses.
        total_booking = 8000

        pending_rate = (
            1.0
            -
            confirmation_value
            -
            cancellation_value
        )

        check(
            "Booking status rates are mathematically consistent",
            pending_rate >= 0
            and pending_rate <= 1,
            (
                f"Confirmed={confirmation_value:.4f}, "
                f"Cancelled={cancellation_value:.4f}, "
                f"Derived pending={pending_rate:.4f}"
            )
        )

    # ========================================================
    # FINAL VALIDATION REPORT
    # ========================================================

    validation_df = pd.DataFrame(
        results
    )

    validation_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    total_checks = len(
        validation_df
    )

    passed = int(
        (
            validation_df["status"]
            == "PASS"
        ).sum()
    )

    failed = (
        total_checks
        -
        passed
    )

    pass_rate = round(
        (
            passed
            /
            total_checks
        )
        *
        100,
        2
    )

    print()
    print("=" * 60)
    print("DAY 5 FINAL VALIDATION SUMMARY")
    print("=" * 60)

    print(
        f"Total checks: {total_checks}"
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
            "DAY 5 KPI + STATISTICS: PASSED"
        )
        print("=" * 60)

        print()
        print(
            "All Day 5 KPI and statistical "
            "requirements are validated."
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
        "DAY 5 KPI + STATISTICS: FAILED"
    )
    print("=" * 60)

    print()

    print(
        validation_df[
            validation_df["status"] == "FAIL"
        ].to_string(
            index=False
        )
    )

    return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )