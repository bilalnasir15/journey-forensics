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

JOURNEY_FILE = os.path.join(
    PROCESSED_DIR,
    "customer_journey_features.csv"
)

CUSTOMER_FILE = os.path.join(
    RAW_DIR,
    "customers.csv"
)

BOOKING_FILE = os.path.join(
    RAW_DIR,
    "bookings.csv"
)

PAYMENT_FILE = os.path.join(
    RAW_DIR,
    "payments.csv"
)

EVENT_FILE = os.path.join(
    RAW_DIR,
    "events.csv"
)

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day5_kpi_report.csv"
)


# ============================================================
# HELPERS
# ============================================================

def load_csv(path, name):

    if not os.path.isfile(path):

        raise FileNotFoundError(
            f"{name} not found:\n{path}"
        )

    return pd.read_csv(path)


def safe_ratio(
    numerator,
    denominator
):

    if denominator == 0:
        return np.nan

    return numerator / denominator


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 5 — KPI ANALYSIS ENGINE")
    print("=" * 60)

    # ========================================================
    # LOAD
    # ========================================================

    print("\nLoading project datasets...")

    journey = load_csv(
        JOURNEY_FILE,
        "customer_journey_features.csv"
    )

    customers = load_csv(
        CUSTOMER_FILE,
        "customers.csv"
    )

    bookings = load_csv(
        BOOKING_FILE,
        "bookings.csv"
    )

    payments = load_csv(
        PAYMENT_FILE,
        "payments.csv"
    )

    events = load_csv(
        EVENT_FILE,
        "events.csv"
    )

    print(
        f"Customers: {len(customers):,}"
    )

    print(
        f"Bookings: {len(bookings):,}"
    )

    print(
        f"Payments: {len(payments):,}"
    )

    print(
        f"Events: {len(events):,}"
    )

    print(
        f"Journey features: {len(journey):,}"
    )

    # ========================================================
    # PREPARE TYPES
    # ========================================================

    bookings["booking_amount"] = pd.to_numeric(
        bookings["booking_amount"],
        errors="coerce"
    )

    payments["payment_amount"] = pd.to_numeric(
        payments["payment_amount"],
        errors="coerce"
    )

    bookings["booking_date"] = pd.to_datetime(
        bookings["booking_date"],
        errors="coerce"
    )

    payments["payment_timestamp"] = pd.to_datetime(
        payments["payment_timestamp"],
        errors="coerce"
    )

    events["event_timestamp"] = pd.to_datetime(
        events["event_timestamp"],
        errors="coerce"
    )

    # ========================================================
    # BASIC COUNTS
    # ========================================================

    total_customers = (
        customers["customer_id"]
        .nunique()
    )

    total_bookings = (
        bookings["booking_id"]
        .nunique()
    )

    total_payments = (
        payments["payment_id"]
        .nunique()
    )

    total_events = (
        events["event_id"]
        .nunique()
    )

    # ========================================================
    # BOOKING STATUS
    # ========================================================

    confirmed_bookings = int(
        (
            bookings["booking_status"]
            .astype(str)
            .str.upper()
            .eq("CONFIRMED")
        ).sum()
    )

    pending_bookings = int(
        (
            bookings["booking_status"]
            .astype(str)
            .str.upper()
            .eq("PENDING")
        ).sum()
    )

    cancelled_bookings = int(
        (
            bookings["booking_status"]
            .astype(str)
            .str.upper()
            .eq("CANCELLED")
        ).sum()
    )

    # ========================================================
    # PAYMENT STATUS
    # ========================================================

    successful_payments = int(
        (
            payments["payment_status"]
            .astype(str)
            .str.upper()
            .eq("SUCCESS")
        ).sum()
    )

    failed_payments = int(
        (
            payments["payment_status"]
            .astype(str)
            .str.upper()
            .eq("FAILED")
        ).sum()
    )

    payment_failure_rate = safe_ratio(
        failed_payments,
        total_payments
    )

    payment_success_rate = safe_ratio(
        successful_payments,
        total_payments
    )

    # ========================================================
    # RETRIES
    # ========================================================

    retry_attempts = int(
        payments[
            "attempt_number"
        ]
        .astype(int)
        .sub(1)
        .clip(lower=0)
        .sum()
    )

    retry_rate = safe_ratio(
        retry_attempts,
        total_payments
    )

    bookings_with_retries = int(
        (
            payments
            .groupby("booking_id")[
                "attempt_number"
            ]
            .max()
            .gt(1)
            .sum()
        )
    )

    retry_booking_rate = safe_ratio(
        bookings_with_retries,
        total_bookings
    )

    # ========================================================
    # BOOKING CONVERSION
    # ========================================================
    #
    # We define booking conversion at the event level:
    #
    # Unique customers with BOOKING_CREATED
    # --------------------------------------------------------
    # Unique customers with SEARCH
    #
    # This is a journey conversion measure, not a
    # marketing-session conversion measure.
    # ========================================================

    search_customers = (
        events.loc[
            events["event_type"] == "SEARCH",
            "customer_id"
        ]
        .nunique()
    )

    booking_created_customers = (
        events.loc[
            events["event_type"] == "BOOKING_CREATED",
            "customer_id"
        ]
        .nunique()
    )

    booking_conversion_rate = safe_ratio(
        booking_created_customers,
        search_customers
    )

    # ========================================================
    # CONFIRMATION RATE
    # ========================================================

    booking_confirmation_rate = safe_ratio(
        confirmed_bookings,
        total_bookings
    )

    cancellation_rate = safe_ratio(
        cancelled_bookings,
        total_bookings
    )

    # ========================================================
    # REPEAT BOOKING
    # ========================================================

    bookings_per_customer = (
        bookings
        .groupby("customer_id")[
            "booking_id"
        ]
        .nunique()
    )

    repeat_customers = int(
        bookings_per_customer
        .ge(2)
        .sum()
    )

    single_booking_customers = int(
        bookings_per_customer
        .eq(1)
        .sum()
    )

    repeat_booking_rate = safe_ratio(
        repeat_customers,
        total_customers
    )

    # ========================================================
    # RETENTION PROXY
    # ========================================================
    #
    # Dataset has no explicit retention/period definition.
    #
    # We therefore define a transparent behavioral proxy:
    # customer made 2 or more bookings.
    # ========================================================

    retention_proxy_rate = safe_ratio(
        repeat_customers,
        total_customers
    )

    # ========================================================
    # REVENUE METRICS
    # ========================================================

    total_revenue = (
        bookings[
            "booking_amount"
        ]
        .sum()
    )

    revenue_per_customer = safe_ratio(
        total_revenue,
        total_customers
    )

    average_booking_value = safe_ratio(
        total_revenue,
        total_bookings
    )

    # ========================================================
    # JOURNEY METRICS
    # ========================================================

    total_anomalies = 0

    if "anomaly_summary" in journey.columns:

        total_anomalies = int(
            journey[
                "anomaly_summary"
            ]
            .ne("NO_ANOMALY")
            .sum()
        )

    anomaly_rate = safe_ratio(
        total_anomalies,
        total_bookings
    )

    average_journey_duration = np.nan

    if "journey_duration_minutes" in journey.columns:

        average_journey_duration = (
            pd.to_numeric(
                journey[
                    "journey_duration_minutes"
                ],
                errors="coerce"
            )
            .mean()
        )

    average_payment_duration = np.nan

    if "payment_duration_minutes" in journey.columns:

        average_payment_duration = (
            pd.to_numeric(
                journey[
                    "payment_duration_minutes"
                ],
                errors="coerce"
            )
            .mean()
        )

    average_friction_score = np.nan

    if "friction_score" in journey.columns:

        average_friction_score = (
            pd.to_numeric(
                journey[
                    "friction_score"
                ],
                errors="coerce"
            )
            .mean()
        )

    # ========================================================
    # KPI RECORDS
    # ========================================================

    kpis = [

        {
            "kpi_name":
                "TOTAL_CUSTOMERS",
            "value":
                total_customers,
            "unit":
                "customers",
            "status":
                "AVAILABLE",
            "definition":
                "Unique customers in the dataset"
        },

        {
            "kpi_name":
                "TOTAL_BOOKINGS",
            "value":
                total_bookings,
            "unit":
                "bookings",
            "status":
                "AVAILABLE",
            "definition":
                "Unique bookings in the dataset"
        },

        {
            "kpi_name":
                "TOTAL_PAYMENT_ATTEMPTS",
            "value":
                total_payments,
            "unit":
                "attempts",
            "status":
                "AVAILABLE",
            "definition":
                "Total payment attempts"
        },

        {
            "kpi_name":
                "TOTAL_EVENTS",
            "value":
                total_events,
            "unit":
                "events",
            "status":
                "AVAILABLE",
            "definition":
                "Total journey events"
        },

        {
            "kpi_name":
                "BOOKING_CONVERSION_RATE",
            "value":
                booking_conversion_rate,
            "unit":
                "rate",
            "status":
                "AVAILABLE",
            "definition":
                "Unique customers creating bookings divided by unique customers searching"
        },

        {
            "kpi_name":
                "BOOKING_CONFIRMATION_RATE",
            "value":
                booking_confirmation_rate,
            "unit":
                "rate",
            "status":
                "AVAILABLE",
            "definition":
                "Confirmed bookings divided by total bookings"
        },

        {
            "kpi_name":
                "CANCELLATION_RATE",
            "value":
                cancellation_rate,
            "unit":
                "rate",
            "status":
                "AVAILABLE",
            "definition":
                "Cancelled bookings divided by total bookings"
        },

        {
            "kpi_name":
                "PAYMENT_SUCCESS_RATE",
            "value":
                payment_success_rate,
            "unit":
                "rate",
            "status":
                "AVAILABLE",
            "definition":
                "Successful payment attempts divided by all payment attempts"
        },

        {
            "kpi_name":
                "PAYMENT_FAILURE_RATE",
            "value":
                payment_failure_rate,
            "unit":
                "rate",
            "status":
                "AVAILABLE",
            "definition":
                "Failed payment attempts divided by all payment attempts"
        },

        {
            "kpi_name":
                "RETRY_RATE",
            "value":
                retry_rate,
            "unit":
                "rate",
            "status":
                "AVAILABLE",
            "definition":
                "Retry attempts divided by payment attempts"
        },

        {
            "kpi_name":
                "BOOKING_RETRY_RATE",
            "value":
                retry_booking_rate,
            "unit":
                "rate",
            "status":
                "AVAILABLE",
            "definition":
                "Bookings with more than one payment attempt divided by all bookings"
        },

        {
            "kpi_name":
                "REPEAT_CUSTOMER_RATE",
            "value":
                repeat_booking_rate,
            "unit":
                "rate",
            "status":
                "AVAILABLE",
            "definition":
                "Customers with two or more bookings divided by all customers"
        },

        {
            "kpi_name":
                "RETENTION_PROXY_RATE",
            "value":
                retention_proxy_rate,
            "unit":
                "rate",
            "status":
                "PROXY",
            "definition":
                "Repeat-booking rate used as a retention proxy because no explicit retention period exists"
        },

        {
            "kpi_name":
                "TOTAL_REVENUE",
            "value":
                total_revenue,
            "unit":
                "currency_units",
            "status":
                "AVAILABLE",
            "definition":
                "Sum of booking amounts"
        },

        {
            "kpi_name":
                "REVENUE_PER_CUSTOMER",
            "value":
                revenue_per_customer,
            "unit":
                "currency_units/customer",
            "status":
                "AVAILABLE",
            "definition":
                "Total booking revenue divided by total customers"
        },

        {
            "kpi_name":
                "AVERAGE_BOOKING_VALUE",
            "value":
                average_booking_value,
            "unit":
                "currency_units/booking",
            "status":
                "AVAILABLE",
            "definition":
                "Total booking revenue divided by total bookings"
        },

        {
            "kpi_name":
                "ANOMALY_RATE",
            "value":
                anomaly_rate,
            "unit":
                "rate",
            "status":
                "AVAILABLE",
            "definition":
                "Journeys with at least one anomaly divided by total bookings"
        },

        {
            "kpi_name":
                "AVERAGE_JOURNEY_DURATION",
            "value":
                average_journey_duration,
            "unit":
                "minutes",
            "status":
                "AVAILABLE",
            "definition":
                "Average journey duration"
        },

        {
            "kpi_name":
                "AVERAGE_PAYMENT_DURATION",
            "value":
                average_payment_duration,
            "unit":
                "minutes",
            "status":
                "AVAILABLE",
            "definition":
                "Average payment duration"
        },

        {
            "kpi_name":
                "AVERAGE_FRICTION_SCORE",
            "value":
                average_friction_score,
            "unit":
                "score",
            "status":
                "AVAILABLE",
            "definition":
                "Average journey friction score"
        },

        {
            "kpi_name":
                "COMPLAINT_RATE",
            "value":
                np.nan,
            "unit":
                "rate",
            "status":
                "NOT_SUPPORTED",
            "definition":
                "Complaint data is not present in the current dataset"
        },

        {
            "kpi_name":
                "COMPLAINT_RESOLUTION_TIME",
            "value":
                np.nan,
            "unit":
                "minutes",
            "status":
                "NOT_SUPPORTED",
            "definition":
                "Complaint timestamps are not present in the current dataset"
        }
    ]

    kpi_df = pd.DataFrame(
        kpis
    )

    # ========================================================
    # ROUND VALUES
    # ========================================================

    rate_mask = (
        kpi_df["unit"] == "rate"
    )

    kpi_df.loc[
        rate_mask,
        "value"
    ] = (
        pd.to_numeric(
            kpi_df.loc[
                rate_mask,
                "value"
            ],
            errors="coerce"
        )
        .round(4)
    )

    numeric_mask = (
        kpi_df["unit"]
        .isin(
            [
                "currency_units",
                "currency_units/customer",
                "currency_units/booking",
                "minutes",
                "score"
            ]
        )
    )

    kpi_df.loc[
        numeric_mask,
        "value"
    ] = (
        pd.to_numeric(
            kpi_df.loc[
                numeric_mask,
                "value"
            ],
            errors="coerce"
        )
        .round(2)
    )

    # ========================================================
    # SAVE
    # ========================================================

    os.makedirs(
        PROCESSED_DIR,
        exist_ok=True
    )

    kpi_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # REPORT
    # ========================================================

    print()
    print("=" * 60)
    print("DAY 5 KPI REPORT")
    print("=" * 60)

    print()
    print(
        kpi_df[
            [
                "kpi_name",
                "value",
                "unit",
                "status"
            ]
        ].to_string(
            index=False
        )
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    available = int(
        (
            kpi_df["status"]
            == "AVAILABLE"
        ).sum()
    )

    proxy = int(
        (
            kpi_df["status"]
            == "PROXY"
        ).sum()
    )

    not_supported = int(
        (
            kpi_df["status"]
            == "NOT_SUPPORTED"
        ).sum()
    )

    print()
    print(
        f"Available KPIs: {available}"
    )

    print(
        f"Proxy KPIs: {proxy}"
    )

    print(
        f"Not supported by current data: "
        f"{not_supported}"
    )

    print()
    print("=" * 60)
    print("DAY 5 KPI ENGINE COMPLETE")
    print("=" * 60)

    print()
    print(
        "Output file:"
    )

    print(
        OUTPUT_FILE
    )

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )