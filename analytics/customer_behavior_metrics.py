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

CUSTOMERS_FILE = os.path.join(
    RAW_DIR,
    "customers.csv"
)

BOOKINGS_FILE = os.path.join(
    RAW_DIR,
    "bookings.csv"
)

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_behavior_metrics.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not os.path.isfile(CUSTOMERS_FILE):
        raise FileNotFoundError(
            f"customers.csv not found:\n{CUSTOMERS_FILE}"
        )

    if not os.path.isfile(BOOKINGS_FILE):
        raise FileNotFoundError(
            f"bookings.csv not found:\n{BOOKINGS_FILE}"
        )

    customers = pd.read_csv(
        CUSTOMERS_FILE
    )

    bookings = pd.read_csv(
        BOOKINGS_FILE
    )

    required_customer_columns = [
        "customer_id"
    ]

    required_booking_columns = [
        "booking_id",
        "customer_id",
        "booking_date",
        "booking_amount"
    ]

    missing_customer = [
        col
        for col in required_customer_columns
        if col not in customers.columns
    ]

    missing_booking = [
        col
        for col in required_booking_columns
        if col not in bookings.columns
    ]

    if missing_customer:
        raise ValueError(
            f"Missing customer columns: {missing_customer}"
        )

    if missing_booking:
        raise ValueError(
            f"Missing booking columns: {missing_booking}"
        )

    bookings["booking_date"] = pd.to_datetime(
        bookings["booking_date"],
        errors="coerce"
    )

    bookings["booking_amount"] = pd.to_numeric(
        bookings["booking_amount"],
        errors="coerce"
    )

    if bookings["booking_date"].isna().any():
        raise ValueError(
            "Invalid booking dates found."
        )

    if bookings["booking_amount"].isna().any():
        raise ValueError(
            "Invalid booking amounts found."
        )

    return customers, bookings


# ============================================================
# BUILD BEHAVIOR METRICS
# ============================================================

def build_behavior_metrics(
    customers,
    bookings
):

    print(
        "Building customer behavioral metrics..."
    )

    # --------------------------------------------------------
    # Dataset reference date
    # --------------------------------------------------------

    reference_date = bookings[
        "booking_date"
    ].max()

    # --------------------------------------------------------
    # Aggregate booking behavior
    # --------------------------------------------------------

    customer_booking_metrics = (
        bookings
        .groupby(
            "customer_id",
            as_index=False
        )
        .agg(

            total_bookings=(
                "booking_id",
                "nunique"
            ),

            total_revenue=(
                "booking_amount",
                "sum"
            ),

            average_booking_value=(
                "booking_amount",
                "mean"
            ),

            first_booking_date=(
                "booking_date",
                "min"
            ),

            last_booking_date=(
                "booking_date",
                "max"
            )
        )
    )

    # --------------------------------------------------------
    # Recency
    # --------------------------------------------------------

    customer_booking_metrics[
        "recency_days"
    ] = (

        reference_date
        -
        customer_booking_metrics[
            "last_booking_date"
        ]

    ).dt.days

    # --------------------------------------------------------
    # Booking frequency
    #
    # Definition:
    # total bookings / active span in months
    #
    # A minimum one-month denominator prevents artificially
    # huge frequency for customers whose first and last booking
    # occurred on the same date.
    # --------------------------------------------------------

    active_span_days = (

        customer_booking_metrics[
            "last_booking_date"
        ]
        -
        customer_booking_metrics[
            "first_booking_date"
        ]
    ).dt.days

    active_span_months = (
        active_span_days
        /
        30.0
    ).clip(
        lower=1.0
    )

    customer_booking_metrics[
        "booking_frequency"
    ] = (

        customer_booking_metrics[
            "total_bookings"
        ]
        /
        active_span_months
    )

    # --------------------------------------------------------
    # Repeat booking
    # --------------------------------------------------------

    customer_booking_metrics[
        "repeat_booking_flag"
    ] = (

        customer_booking_metrics[
            "total_bookings"
        ]
        >=
        2
    ).astype(int)

    # --------------------------------------------------------
    # Round numeric values
    # --------------------------------------------------------

    customer_booking_metrics[
        "total_revenue"
    ] = (
        customer_booking_metrics[
            "total_revenue"
        ]
        .round(2)
    )

    customer_booking_metrics[
        "average_booking_value"
    ] = (
        customer_booking_metrics[
            "average_booking_value"
        ]
        .round(2)
    )

    customer_booking_metrics[
        "booking_frequency"
    ] = (
        customer_booking_metrics[
            "booking_frequency"
        ]
        .round(4)
    )

    # --------------------------------------------------------
    # Add customers with zero bookings
    # --------------------------------------------------------

    result = customers[
        [
            "customer_id"
        ]
    ].merge(

        customer_booking_metrics,

        on="customer_id",

        how="left",

        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Fill zero-activity customers
    # --------------------------------------------------------

    zero_booking_columns = [
        "total_bookings",
        "total_revenue",
        "average_booking_value",
        "recency_days",
        "booking_frequency",
        "repeat_booking_flag"
    ]

    for column in zero_booking_columns:

        result[column] = (
            pd.to_numeric(
                result[column],
                errors="coerce"
            )
            .fillna(0)
        )

    result[
        "repeat_booking_flag"
    ] = (
        result[
            "repeat_booking_flag"
        ]
        .astype(int)
    )

    return result, reference_date


# ============================================================
# VALIDATION
# ============================================================

def validate_metrics(
    customers,
    bookings,
    result,
    reference_date
):

    print()
    print("=" * 60)
    print("DAY 7 BEHAVIORAL METRICS VALIDATION")
    print("=" * 60)

    checks = []

    # --------------------------------------------------------
    # Customer coverage
    # --------------------------------------------------------

    checks.append(
        (
            "Customer coverage preserved",
            (
                result["customer_id"].nunique()
                ==
                customers["customer_id"].nunique()
            ),
            (
                f"Customers="
                f"{customers['customer_id'].nunique():,}, "
                f"Metrics="
                f"{result['customer_id'].nunique():,}"
            )
        )
    )

    # --------------------------------------------------------
    # One row per customer
    # --------------------------------------------------------

    checks.append(
        (
            "One row per customer",
            result["customer_id"].is_unique,
            (
                f"Duplicates="
                f"{result['customer_id'].duplicated().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # Booking reconciliation
    # --------------------------------------------------------

    checks.append(
        (
            "Booking counts reconcile",
            (
                result["total_bookings"].sum()
                ==
                bookings["booking_id"].nunique()
            ),
            (
                f"Expected="
                f"{bookings['booking_id'].nunique():,}, "
                f"Actual="
                f"{int(result['total_bookings'].sum()):,}"
            )
        )
    )

    # --------------------------------------------------------
    # Revenue reconciliation
    # --------------------------------------------------------

    expected_revenue = round(
        bookings["booking_amount"].sum(),
        2
    )

    actual_revenue = round(
        result["total_revenue"].sum(),
        2
    )

    checks.append(
        (
            "Revenue reconciles",
            abs(
                actual_revenue
                -
                expected_revenue
            ) < 0.01,
            (
                f"Expected={expected_revenue:.2f}, "
                f"Actual={actual_revenue:.2f}"
            )
        )
    )

    # --------------------------------------------------------
    # First booking <= last booking
    # --------------------------------------------------------

    active_customers = result[
        result["total_bookings"] > 0
    ]

    checks.append(
        (
            "First booking is not after last booking",
            (
                active_customers[
                    "first_booking_date"
                ]
                <=
                active_customers[
                    "last_booking_date"
                ]
            ).all(),
            "All active customers valid"
        )
    )

    # --------------------------------------------------------
    # Recency
    # --------------------------------------------------------

    checks.append(
        (
            "Recency is non-negative",
            result[
                "recency_days"
            ].ge(0).all(),
            (
                f"Min="
                f"{result['recency_days'].min():.0f}, "
                f"Max="
                f"{result['recency_days'].max():.0f}"
            )
        )
    )

    # --------------------------------------------------------
    # Recency correctness
    # --------------------------------------------------------

    active_recency = active_customers[
        "last_booking_date"
    ]

    expected_recency = (
        reference_date
        -
        active_recency
    ).dt.days

    actual_recency = active_customers[
        "recency_days"
    ].astype(int)

    checks.append(
        (
            "Recency calculation is correct",
            expected_recency
            .reset_index(drop=True)
            .equals(
                actual_recency
                .reset_index(drop=True)
            ),
            f"Reference date={reference_date.date()}"
        )
    )

    # --------------------------------------------------------
    # Booking frequency
    # --------------------------------------------------------

    checks.append(
        (
            "Booking frequency is non-negative",
            result[
                "booking_frequency"
            ].ge(0).all(),
            "All values >= 0"
        )
    )

    # --------------------------------------------------------
    # Repeat flag
    # --------------------------------------------------------

    expected_repeat = (
        result[
            "total_bookings"
        ]
        .ge(2)
        .astype(int)
    )

    checks.append(
        (
            "Repeat booking flag is correct",
            expected_repeat
            .equals(
                result[
                    "repeat_booking_flag"
                ]
            ),
            "Flag = 1 when bookings >= 2"
        )
    )

    # --------------------------------------------------------
    # First/last booking null handling
    # --------------------------------------------------------

    zero_booking = result[
        result["total_bookings"] == 0
    ]

    checks.append(
        (
            "Zero-booking customers are handled",
            (
                zero_booking[
                    "repeat_booking_flag"
                ]
                .eq(0)
                .all()
            ),
            (
                f"Zero-booking customers="
                f"{len(zero_booking):,}"
            )
        )
    )

    # --------------------------------------------------------
    # Print
    # --------------------------------------------------------

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

    pass_rate = round(
        passed
        /
        len(checks)
        *
        100,
        2
    )

    print(
        f"Pass rate: {pass_rate:.2f}%"
    )

    return (
        failed == 0
    ), checks


# ============================================================
# REPORT
# ============================================================

def print_report(
    result,
    reference_date
):

    print()
    print("=" * 60)
    print("DAY 7 CUSTOMER BEHAVIOR REPORT")
    print("=" * 60)

    print()
    print(
        f"Customers: "
        f"{len(result):,}"
    )

    print(
        f"Reference date: "
        f"{reference_date.date()}"
    )

    print()
    print("BEHAVIOR SUMMARY")
    print("-" * 40)

    print(
        f"Average bookings: "
        f"{result['total_bookings'].mean():.2f}"
    )

    print(
        f"Average revenue: "
        f"{result['total_revenue'].mean():.2f}"
    )

    print(
        f"Average booking value: "
        f"{result['average_booking_value'].mean():.2f}"
    )

    print(
        f"Average recency: "
        f"{result['recency_days'].mean():.2f} days"
    )

    print(
        f"Repeat customers: "
        f"{result['repeat_booking_flag'].sum():,}"
    )

    print()
    print(
        "TOP 10 CUSTOMERS BY REVENUE"
    )
    print("-" * 40)

    print(
        result[
            [
                "customer_id",
                "total_bookings",
                "total_revenue",
                "average_booking_value",
                "recency_days",
                "booking_frequency",
                "repeat_booking_flag"
            ]
        ]
        .sort_values(
            "total_revenue",
            ascending=False
        )
        .head(10)
        .to_string(
            index=False
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 7 — CUSTOMER BEHAVIOR METRICS")
    print("=" * 60)

    try:

        print()
        print(
            "Loading raw datasets..."
        )

        customers, bookings = (
            load_data()
        )

        print(
            f"Customers: "
            f"{len(customers):,}"
        )

        print(
            f"Bookings: "
            f"{len(bookings):,}"
        )

        result, reference_date = (
            build_behavior_metrics(
                customers,
                bookings
            )
        )

        print_report(
            result,
            reference_date
        )

        validation_passed, checks = (
            validate_metrics(
                customers,
                bookings,
                result,
                reference_date
            )
        )

        os.makedirs(
            PROCESSED_DIR,
            exist_ok=True
        )

        result.to_csv(
            OUTPUT_FILE,
            index=False
        )

        print()
        print("=" * 60)

        if validation_passed:

            print(
                "DAY 7 BEHAVIORAL METRICS: PASSED"
            )

        else:

            print(
                "DAY 7 BEHAVIORAL METRICS: FAILED"
            )

        print("=" * 60)

        print()
        print(
            "Output file:"
        )

        print(
            OUTPUT_FILE
        )

        print()
        print(
            f"Customer records: "
            f"{len(result):,}"
        )

        print(
            f"Features generated: "
            f"{len(result.columns):,}"
        )

        return (
            0
            if validation_passed
            else
            1
        )

    except Exception as exc:

        print()
        print("=" * 60)
        print(
            "DAY 7 BEHAVIORAL METRICS: FAILED"
        )
        print("=" * 60)

        print()
        print(
            f"ERROR: {exc}"
        )

        return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )