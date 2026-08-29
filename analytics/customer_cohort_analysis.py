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

OUTPUT_CUSTOMER_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_cohorts.csv"
)

OUTPUT_COHORT_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_cohort_summary.csv"
)

REFERENCE_DATE = None


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
        column
        for column in required_customer_columns
        if column not in customers.columns
    ]

    missing_booking = [
        column
        for column in required_booking_columns
        if column not in bookings.columns
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
# BUILD CUSTOMER COHORT DATA
# ============================================================

def build_customer_cohorts(
    customers,
    bookings
):

    print(
        "Building customer cohort assignments..."
    )

    # --------------------------------------------------------
    # Reference date
    # --------------------------------------------------------

    reference_date = bookings[
        "booking_date"
    ].max()

    # --------------------------------------------------------
    # Customer booking history
    # --------------------------------------------------------

    customer_history = (
        bookings
        .groupby(
            "customer_id",
            as_index=False
        )
        .agg(

            first_booking_date=(
                "booking_date",
                "min"
            ),

            last_booking_date=(
                "booking_date",
                "max"
            ),

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
            )
        )
    )

    # --------------------------------------------------------
    # Cohort month
    # --------------------------------------------------------

    customer_history[
        "cohort_month"
    ] = (
        customer_history[
            "first_booking_date"
        ]
        .dt.to_period("M")
        .astype(str)
    )

    # --------------------------------------------------------
    # Recency
    # --------------------------------------------------------

    customer_history[
        "recency_days"
    ] = (

        reference_date
        -
        customer_history[
            "last_booking_date"
        ]

    ).dt.days

    # --------------------------------------------------------
    # Repeat customer
    # --------------------------------------------------------

    customer_history[
        "repeat_booking_flag"
    ] = (

        customer_history[
            "total_bookings"
        ]
        >= 2
    ).astype(int)

    # --------------------------------------------------------
    # Active booking span
    # --------------------------------------------------------

    active_span_days = (

        customer_history[
            "last_booking_date"
        ]
        -
        customer_history[
            "first_booking_date"
        ]
    ).dt.days

    customer_history[
        "active_span_days"
    ] = active_span_days

    # --------------------------------------------------------
    # Customer frequency
    #
    # Uses the same definition as Brick 7.1.
    # --------------------------------------------------------

    active_span_months = (
        active_span_days
        /
        30.0
    ).clip(
        lower=1.0
    )

    customer_history[
        "booking_frequency"
    ] = (

        customer_history[
            "total_bookings"
        ]
        /
        active_span_months
    )

    # --------------------------------------------------------
    # Add customers without bookings
    # --------------------------------------------------------

    result = customers[
        [
            "customer_id"
        ]
    ].merge(

        customer_history,

        on="customer_id",

        how="left",

        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Explicitly represent customers without bookings
    # --------------------------------------------------------

    result[
        "cohort_status"
    ] = (
        result[
            "first_booking_date"
        ]
        .notna()
        .map(
            {
                True: "ACTIVE_COHORT_MEMBER",
                False: "NO_BOOKING"
            }
        )
    )

    return result, reference_date


# ============================================================
# BUILD COHORT SUMMARY
# ============================================================

def build_cohort_summary(
    customer_cohorts
):

    print(
        "Calculating cohort-level statistics..."
    )

    active = customer_cohorts[
        customer_cohorts[
            "cohort_status"
        ]
        ==
        "ACTIVE_COHORT_MEMBER"
    ].copy()

    if active.empty:

        return pd.DataFrame(
            columns=[
                "cohort_month",
                "cohort_size",
                "repeat_customers",
                "repeat_customer_rate",
                "average_bookings",
                "average_revenue",
                "average_booking_value",
                "average_recency_days",
                "average_booking_frequency",
                "total_cohort_revenue"
            ]
        )

    summary = (
        active
        .groupby(
            "cohort_month",
            as_index=False
        )
        .agg(

            cohort_size=(
                "customer_id",
                "nunique"
            ),

            repeat_customers=(
                "repeat_booking_flag",
                "sum"
            ),

            average_bookings=(
                "total_bookings",
                "mean"
            ),

            average_revenue=(
                "total_revenue",
                "mean"
            ),

            average_booking_value=(
                "average_booking_value",
                "mean"
            ),

            average_recency_days=(
                "recency_days",
                "mean"
            ),

            average_booking_frequency=(
                "booking_frequency",
                "mean"
            ),

            total_cohort_revenue=(
                "total_revenue",
                "sum"
            )
        )
    )

    # --------------------------------------------------------
    # Repeat customer rate
    # --------------------------------------------------------

    summary[
        "repeat_customer_rate"
    ] = (

        summary[
            "repeat_customers"
        ]
        /
        summary[
            "cohort_size"
        ]
    )

    # --------------------------------------------------------
    # Round values
    # --------------------------------------------------------

    numeric_columns = [
        "average_bookings",
        "average_revenue",
        "average_booking_value",
        "average_recency_days",
        "average_booking_frequency",
        "total_cohort_revenue",
        "repeat_customer_rate"
    ]

    for column in numeric_columns:

        summary[column] = pd.to_numeric(
            summary[column],
            errors="coerce"
        ).round(4)

    summary[
        "cohort_size"
    ] = (
        summary[
            "cohort_size"
        ]
        .astype(int)
    )

    summary[
        "repeat_customers"
    ] = (
        summary[
            "repeat_customers"
        ]
        .astype(int)
    )

    return summary


# ============================================================
# VALIDATION
# ============================================================

def validate_cohorts(
    customers,
    bookings,
    customer_cohorts,
    cohort_summary,
    reference_date
):

    print()
    print("=" * 60)
    print(
        "DAY 7 COHORT ANALYSIS VALIDATION"
    )
    print("=" * 60)

    checks = []

    # --------------------------------------------------------
    # Customer conservation
    # --------------------------------------------------------

    checks.append(
        (
            "Customer count preserved",
            len(customer_cohorts)
            ==
            len(customers),
            (
                f"Customers={len(customers):,}, "
                f"Cohort records={len(customer_cohorts):,}"
            )
        )
    )

    # --------------------------------------------------------
    # Unique customers
    # --------------------------------------------------------

    checks.append(
        (
            "One row per customer",
            customer_cohorts[
                "customer_id"
            ].is_unique,
            (
                f"Duplicates="
                f"{customer_cohorts['customer_id'].duplicated().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # Booking count
    # --------------------------------------------------------

    active = customer_cohorts[
        customer_cohorts[
            "cohort_status"
        ]
        ==
        "ACTIVE_COHORT_MEMBER"
    ]

    checks.append(
        (
            "Active customers match booking customers",
            active[
                "customer_id"
            ].nunique()
            ==
            bookings[
                "customer_id"
            ].nunique(),
            (
                f"Bookings customers="
                f"{bookings['customer_id'].nunique():,}, "
                f"Active cohort customers="
                f"{active['customer_id'].nunique():,}"
            )
        )
    )

    # --------------------------------------------------------
    # Booking reconciliation
    # --------------------------------------------------------

    checks.append(
        (
            "Customer booking counts reconcile",
            active[
                "total_bookings"
            ].sum()
            ==
            bookings[
                "booking_id"
            ].nunique(),
            (
                f"Expected="
                f"{bookings['booking_id'].nunique():,}, "
                f"Actual="
                f"{int(active['total_bookings'].sum()):,}"
            )
        )
    )

    # --------------------------------------------------------
    # Revenue reconciliation
    # --------------------------------------------------------

    expected_revenue = round(
        bookings[
            "booking_amount"
        ].sum(),
        2
    )

    actual_revenue = round(
        active[
            "total_revenue"
        ].sum(),
        2
    )

    checks.append(
        (
            "Cohort revenue reconciles",
            abs(
                expected_revenue
                -
                actual_revenue
            )
            <
            0.01,
            (
                f"Expected={expected_revenue:.2f}, "
                f"Actual={actual_revenue:.2f}"
            )
        )
    )

    # --------------------------------------------------------
    # Cohort dates
    # --------------------------------------------------------

    cohort_dates = pd.to_datetime(
        active[
            "first_booking_date"
        ],
        errors="coerce"
    )

    checks.append(
        (
            "First booking dates are valid",
            cohort_dates.notna().all(),
            (
                f"Missing="
                f"{cohort_dates.isna().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # Cohort month correctness
    # --------------------------------------------------------

    expected_cohort_month = (
        active[
            "first_booking_date"
        ]
        .dt.to_period("M")
        .astype(str)
    )

    actual_cohort_month = (
        active[
            "cohort_month"
        ]
        .astype(str)
    )

    checks.append(
        (
            "Cohort month matches first booking month",
            expected_cohort_month
            .reset_index(drop=True)
            .equals(
                actual_cohort_month
                .reset_index(drop=True)
            ),
            "Cohort = month of first booking"
        )
    )

    # --------------------------------------------------------
    # Recency
    # --------------------------------------------------------

    checks.append(
        (
            "Cohort recency is non-negative",
            active[
                "recency_days"
            ]
            .ge(0)
            .all(),
            (
                f"Min="
                f"{active['recency_days'].min():.0f}, "
                f"Max="
                f"{active['recency_days'].max():.0f}"
            )
        )
    )

    # --------------------------------------------------------
    # Repeat flag
    # --------------------------------------------------------

    expected_repeat = (
        active[
            "total_bookings"
        ]
        .ge(2)
        .astype(int)
    )

    checks.append(
        (
            "Repeat booking flags are correct",
            expected_repeat
            .reset_index(drop=True)
            .equals(
                active[
                    "repeat_booking_flag"
                ]
                .astype(int)
                .reset_index(drop=True)
            ),
            "Repeat = 1 when bookings >= 2"
        )
    )

    # --------------------------------------------------------
    # Cohort size conservation
    # --------------------------------------------------------

    checks.append(
        (
            "Cohort sizes reconcile",
            cohort_summary[
                "cohort_size"
            ].sum()
            ==
            len(active),
            (
                f"Active customers="
                f"{len(active):,}, "
                f"Cohort total="
                f"{int(cohort_summary['cohort_size'].sum()):,}"
            )
        )
    )

    # --------------------------------------------------------
    # Repeat customers
    # --------------------------------------------------------

    checks.append(
        (
            "Cohort repeat counts reconcile",
            cohort_summary[
                "repeat_customers"
            ].sum()
            ==
            int(
                active[
                    "repeat_booking_flag"
                ].sum()
            ),
            (
                f"Customer repeats="
                f"{int(active['repeat_booking_flag'].sum()):,}, "
                f"Cohort repeats="
                f"{int(cohort_summary['repeat_customers'].sum()):,}"
            )
        )
    )

    # --------------------------------------------------------
    # Repeat rates
    # --------------------------------------------------------

    expected_repeat_rates = (
        cohort_summary[
            "repeat_customers"
        ]
        /
        cohort_summary[
            "cohort_size"
        ]
    )

    checks.append(
        (
            "Cohort repeat rates are correct",
            (
                expected_repeat_rates
                -
                cohort_summary[
                    "repeat_customer_rate"
                ]
            )
            .abs()
            .le(0.0001)
            .all(),
            "Repeat rate = repeat customers / cohort size"
        )
    )

    # --------------------------------------------------------
    # Cohort month uniqueness
    # --------------------------------------------------------

    checks.append(
        (
            "Cohort summary has one row per cohort month",
            cohort_summary[
                "cohort_month"
            ].is_unique,
            (
                f"Duplicates="
                f"{cohort_summary['cohort_month'].duplicated().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # Reference date
    # --------------------------------------------------------

    checks.append(
        (
            "Reference date is valid",
            pd.notna(reference_date),
            (
                f"Reference={reference_date.date()}"
            )
        )
    )

    # --------------------------------------------------------
    # Print checks
    # --------------------------------------------------------

    passed = 0

    for name, condition, detail in checks:

        status = (
            "PASS"
            if condition
            else
            "FAIL"
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

    pass_rate = round(
        passed
        /
        len(checks)
        *
        100,
        2
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

    print(
        f"Pass rate: {pass_rate:.2f}%"
    )

    return failed == 0


# ============================================================
# REPORT
# ============================================================

def print_report(
    customer_cohorts,
    cohort_summary,
    reference_date
):

    active = customer_cohorts[
        customer_cohorts[
            "cohort_status"
        ]
        ==
        "ACTIVE_COHORT_MEMBER"
    ]

    no_booking = customer_cohorts[
        customer_cohorts[
            "cohort_status"
        ]
        ==
        "NO_BOOKING"
    ]

    print()
    print("=" * 60)
    print(
        "DAY 7 COHORT ANALYSIS REPORT"
    )
    print("=" * 60)

    print()
    print(
        f"Total customers: "
        f"{len(customer_cohorts):,}"
    )

    print(
        f"Active cohort customers: "
        f"{len(active):,}"
    )

    print(
        f"No-booking customers: "
        f"{len(no_booking):,}"
    )

    print(
        f"Reference date: "
        f"{reference_date.date()}"
    )

    print()
    print("COHORT SUMMARY")
    print("-" * 40)

    print(
        cohort_summary.to_string(
            index=False
        )
    )

    print()
    print("LARGEST COHORTS")
    print("-" * 40)

    print(
        cohort_summary[
            [
                "cohort_month",
                "cohort_size",
                "repeat_customer_rate",
                "average_revenue",
                "total_cohort_revenue"
            ]
        ]
        .sort_values(
            "cohort_size",
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
    print(
        "DAY 7 — CUSTOMER COHORT ANALYSIS"
    )
    print("=" * 60)

    try:

        print()
        print(
            "Loading raw customer and booking data..."
        )

        customers, bookings = (
            load_data()
        )

        print(
            f"Customers: {len(customers):,}"
        )

        print(
            f"Bookings: {len(bookings):,}"
        )

        customer_cohorts, reference_date = (
            build_customer_cohorts(
                customers,
                bookings
            )
        )

        cohort_summary = (
            build_cohort_summary(
                customer_cohorts
            )
        )

        print_report(
            customer_cohorts,
            cohort_summary,
            reference_date
        )

        validation_passed = (
            validate_cohorts(
                customers,
                bookings,
                customer_cohorts,
                cohort_summary,
                reference_date
            )
        )

        os.makedirs(
            PROCESSED_DIR,
            exist_ok=True
        )

        customer_cohorts.to_csv(
            OUTPUT_CUSTOMER_FILE,
            index=False
        )

        cohort_summary.to_csv(
            OUTPUT_COHORT_FILE,
            index=False
        )

        print()
        print("=" * 60)

        if validation_passed:

            print(
                "DAY 7 COHORT ANALYSIS: PASSED"
            )

        else:

            print(
                "DAY 7 COHORT ANALYSIS: FAILED"
            )

        print("=" * 60)

        print()
        print(
            "Customer cohort file:"
        )

        print(
            OUTPUT_CUSTOMER_FILE
        )

        print()
        print(
            "Cohort summary file:"
        )

        print(
            OUTPUT_COHORT_FILE
        )

        print()
        print(
            f"Customer records: "
            f"{len(customer_cohorts):,}"
        )

        print(
            f"Cohort months: "
            f"{len(cohort_summary):,}"
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
            "DAY 7 COHORT ANALYSIS: FAILED"
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