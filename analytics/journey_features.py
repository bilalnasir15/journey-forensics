import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("=" * 60)
    print("LOADING RAW DATA")
    print("=" * 60)

    customers = pd.read_csv(
        RAW_DIR / "customers.csv",
        parse_dates=[
            "signup_date",
            "date_of_birth"
        ]
    )

    bookings = pd.read_csv(
        RAW_DIR / "bookings.csv",
        parse_dates=[
            "booking_date"
        ]
    )

    payments = pd.read_csv(
        RAW_DIR / "payments.csv",
        parse_dates=[
            "payment_timestamp"
        ]
    )

    events = pd.read_csv(
        RAW_DIR / "events.csv",
        parse_dates=[
            "event_timestamp"
        ]
    )

    trips = pd.read_csv(
        RAW_DIR / "trips.csv",
        parse_dates=[
            "departure_date",
            "return_date"
        ]
    )

    print(f"Customers: {len(customers):,}")
    print(f"Bookings: {len(bookings):,}")
    print(f"Payments: {len(payments):,}")
    print(f"Events: {len(events):,}")
    print(f"Trips: {len(trips):,}")

    return (
        customers,
        bookings,
        payments,
        events,
        trips
    )


# ============================================================
# PAYMENT FEATURES
# ============================================================

def build_payment_features(payments):

    print("\nBuilding payment features...")

    payment_features = (
        payments
        .groupby("booking_id")
        .agg(
            payment_attempts=(
                "payment_id",
                "count"
            ),

            failed_payments=(
                "payment_status",
                lambda x: (
                    x == "Failed"
                ).sum()
            ),

            successful_payments=(
                "payment_status",
                lambda x: (
                    x == "Success"
                ).sum()
            ),

            first_payment_timestamp=(
                "payment_timestamp",
                "min"
            ),

            last_payment_timestamp=(
                "payment_timestamp",
                "max"
            ),

            payment_methods_used=(
                "payment_method",
                lambda x: x.astype(str).nunique()
            ),

            payment_failures_reasons=(
                "failure_reason",
                lambda x: x.dropna().astype(str).nunique()
            )
        )
        .reset_index()
    )

    payment_features["retry_count"] = (
        payment_features["payment_attempts"] - 1
    )

    payment_features["payment_success_rate"] = np.where(
        payment_features["payment_attempts"] > 0,
        (
            payment_features["successful_payments"]
            /
            payment_features["payment_attempts"]
        ),
        0
    )

    payment_features["payment_duration_minutes"] = (
        (
            payment_features["last_payment_timestamp"]
            -
            payment_features["first_payment_timestamp"]
        )
        .dt.total_seconds()
        / 60
    )

    return payment_features


# ============================================================
# EVENT FEATURES
# ============================================================

def build_event_features(events):

    print("Building event features...")

    event_features = (
        events
        .groupby("booking_id")
        .agg(
            total_events=(
                "event_id",
                "count"
            ),

            first_event_timestamp=(
                "event_timestamp",
                "min"
            ),

            last_event_timestamp=(
                "event_timestamp",
                "max"
            )
        )
        .reset_index()
    )

    event_counts = (
        events
        .pivot_table(
            index="booking_id",
            columns="event_type",
            values="event_id",
            aggfunc="count",
            fill_value=0
        )
        .reset_index()
    )

    event_counts.columns = [
        str(column).lower()
        for column in event_counts.columns
    ]

    rename_map = {
        "search": "search_events",
        "view_trip": "view_trip_events",
        "booking_started": "booking_started_events",
        "booking_created": "booking_created_events",
        "payment_started": "payment_started_events",
        "payment_failed": "payment_failed_events",
        "payment_retry": "payment_retry_events",
        "payment_completed": "payment_completed_events",
        "booking_confirmed": "booking_confirmed_events"
    }

    event_counts = event_counts.rename(
        columns=rename_map
    )

    event_features = event_features.merge(
        event_counts,
        on="booking_id",
        how="left"
    )

    event_columns = [
        column
        for column in event_features.columns
        if column.endswith("_events")
    ]

    event_features[event_columns] = (
        event_features[event_columns]
        .fillna(0)
        .astype(int)
    )

    event_features["journey_duration_minutes"] = (
        (
            event_features["last_event_timestamp"]
            -
            event_features["first_event_timestamp"]
        )
        .dt.total_seconds()
        / 60
    )

    return event_features


# ============================================================
# BOOKING FEATURES
# ============================================================

def build_booking_features(
    bookings,
    trips
):

    print("Building booking features...")

    booking_features = bookings.merge(
        trips[
            [
                "trip_id",
                "destination",
                "trip_type",
                "departure_date",
                "return_date",
                "capacity",
                "base_price"
            ]
        ],
        on="trip_id",
        how="left"
    )

    booking_features["days_before_departure"] = (
        (
            booking_features["departure_date"]
            -
            booking_features["booking_date"]
        )
        .dt.total_seconds()
        / 86400
    )

    booking_features["price_difference"] = (
        booking_features["booking_amount"]
        -
        booking_features["base_price"]
    )

    booking_features["price_ratio"] = np.where(
        booking_features["base_price"] > 0,
        (
            booking_features["booking_amount"]
            /
            booking_features["base_price"]
        ),
        np.nan
    )

    return booking_features


# ============================================================
# FRICTION SCORE
# ============================================================

def calculate_friction_score(df):

    print("Calculating journey friction score...")

    score = pd.Series(
        0,
        index=df.index,
        dtype=float
    )

    score += (
        df["failed_payments"] * 15
    )

    score += (
        df["retry_count"] * 10
    )

    score += np.where(
        df["payment_duration_minutes"] > 30,
        15,
        np.where(
            df["payment_duration_minutes"] > 10,
            5,
            0
        )
    )

    score += np.where(
        df["total_events"] > 12,
        10,
        np.where(
            df["total_events"] > 8,
            5,
            0
        )
    )

    score += np.where(
        df["booking_status"] == "Pending",
        20,
        0
    )

    score += np.where(
        df["booking_status"] == "Cancelled",
        15,
        0
    )

    score += np.where(
        (
            df["successful_payments"] > 0
        )
        &
        (
            df["booking_status"] != "Confirmed"
        ),
        25,
        0
    )

    df["friction_score"] = np.minimum(
        score,
        100
    )

    df["risk_level"] = pd.cut(
        df["friction_score"],
        bins=[
            -1,
            29,
            59,
            79,
            100
        ],
        labels=[
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL"
        ]
    )

    return df


# ============================================================
# ANOMALY DETECTION
# ============================================================

def detect_anomalies(df):

    print("Detecting journey anomalies...")

    df["anomaly_multiple_payment_failures"] = (
        df["failed_payments"] >= 2
    )

    df["anomaly_retry_storm"] = (
        df["retry_count"] >= 2
    )

    df["anomaly_payment_booking_mismatch"] = (
        (
            df["successful_payments"] > 0
        )
        &
        (
            df["booking_status"] != "Confirmed"
        )
    )

    df["anomaly_long_journey"] = (
        df["journey_duration_minutes"] > 120
    )

    df["anomaly_long_payment"] = (
        df["payment_duration_minutes"] > 60
    )

    anomaly_columns = [
        column
        for column in df.columns
        if column.startswith("anomaly_")
    ]

    df["anomaly_count"] = (
        df[anomaly_columns]
        .sum(axis=1)
    )

    def create_anomaly_list(row):

        anomalies = []

        if row["anomaly_multiple_payment_failures"]:
            anomalies.append(
                "MULTIPLE_PAYMENT_FAILURES"
            )

        if row["anomaly_retry_storm"]:
            anomalies.append(
                "PAYMENT_RETRY_STORM"
            )

        if row["anomaly_payment_booking_mismatch"]:
            anomalies.append(
                "PAYMENT_SUCCESS_BOOKING_UNRESOLVED"
            )

        if row["anomaly_long_journey"]:
            anomalies.append(
                "LONG_JOURNEY"
            )

        if row["anomaly_long_payment"]:
            anomalies.append(
                "LONG_PAYMENT_PROCESS"
            )

        return (
            anomalies
            if anomalies
            else ["NO_ANOMALY"]
        )

    df["anomalies"] = df.apply(
        create_anomaly_list,
        axis=1
    )

    df["anomaly_summary"] = (
        df["anomalies"]
        .apply(
            lambda values:
            " | ".join(values)
        )
    )

    return df


# ============================================================
# BUILD COMPLETE FEATURE DATASET
# ============================================================

def build_customer_journey_features():

    (
        customers,
        bookings,
        payments,
        events,
        trips
    ) = load_data()

    payment_features = (
        build_payment_features(
            payments
        )
    )

    event_features = (
        build_event_features(
            events
        )
    )

    booking_features = (
        build_booking_features(
            bookings,
            trips
        )
    )

    journey = booking_features.merge(
        customers[
            [
                "customer_id",
                "first_name",
                "last_name",
                "country",
                "signup_date",
                "customer_segment"
            ]
        ],
        on="customer_id",
        how="left"
    )

    journey = journey.merge(
        payment_features,
        on="booking_id",
        how="left"
    )

    journey = journey.merge(
        event_features,
        on="booking_id",
        how="left"
    )

    numeric_columns = [
        "payment_attempts",
        "failed_payments",
        "successful_payments",
        "retry_count",
        "payment_methods_used",
        "payment_failures_reasons",
        "payment_success_rate",
        "payment_duration_minutes",
        "total_events",
        "journey_duration_minutes"
    ]

    for column in numeric_columns:

        if column in journey.columns:
            journey[column] = (
                journey[column]
                .fillna(0)
            )

    journey = calculate_friction_score(
        journey
    )

    journey = detect_anomalies(
        journey
    )

    customer_metrics = (
        journey
        .groupby("customer_id")
        .agg(
            total_bookings=(
                "booking_id",
                "count"
            ),

            total_booking_value=(
                "booking_amount",
                "sum"
            ),

            average_booking_value=(
                "booking_amount",
                "mean"
            ),

            total_payment_failures=(
                "failed_payments",
                "sum"
            ),

            total_payment_attempts=(
                "payment_attempts",
                "sum"
            ),

            average_friction_score=(
                "friction_score",
                "mean"
            ),

            maximum_friction_score=(
                "friction_score",
                "max"
            ),

            total_anomalies=(
                "anomaly_count",
                "sum"
            )
        )
        .reset_index()
    )

    journey = journey.merge(
        customer_metrics,
        on="customer_id",
        how="left"
    )

    journey["payment_success_rate"] = (
        journey["payment_success_rate"]
        .round(3)
    )

    journey["payment_duration_minutes"] = (
        journey["payment_duration_minutes"]
        .round(2)
    )

    journey["journey_duration_minutes"] = (
        journey["journey_duration_minutes"]
        .round(2)
    )

    journey["friction_score"] = (
        journey["friction_score"]
        .round(2)
    )

    journey["average_friction_score"] = (
        journey["average_friction_score"]
        .round(2)
    )

    preferred_columns = [

        "customer_id",
        "first_name",
        "last_name",
        "country",
        "customer_segment",

        "booking_id",
        "trip_id",
        "booking_date",
        "booking_status",
        "booking_amount",

        "destination",
        "trip_type",
        "departure_date",
        "return_date",
        "days_before_departure",
        "base_price",
        "price_difference",
        "price_ratio",

        "payment_attempts",
        "failed_payments",
        "successful_payments",
        "retry_count",
        "payment_success_rate",
        "payment_duration_minutes",
        "payment_methods_used",
        "payment_failures_reasons",

        "total_events",
        "search_events",
        "view_trip_events",
        "booking_started_events",
        "booking_created_events",
        "payment_started_events",
        "payment_failed_events",
        "payment_retry_events",
        "payment_completed_events",
        "booking_confirmed_events",
        "journey_duration_minutes",

        "friction_score",
        "risk_level",
        "anomaly_count",
        "anomaly_summary",

        "total_bookings",
        "total_booking_value",
        "average_booking_value",
        "total_payment_failures",
        "total_payment_attempts",
        "average_friction_score",
        "maximum_friction_score",
        "total_anomalies"
    ]

    final_columns = [
        column
        for column in preferred_columns
        if column in journey.columns
    ]

    journey = journey[
        final_columns
    ]

    journey = journey.sort_values(
        [
            "customer_id",
            "booking_date"
        ]
    ).reset_index(
        drop=True
    )

    return journey


# ============================================================
# OVERALL REPORT
# ============================================================

def print_report(journey):

    print("\n")
    print("=" * 60)
    print("JOURNEY FORENSICS FEATURE REPORT")
    print("=" * 60)

    print(
        "\nTotal journey records:",
        f"{len(journey):,}"
    )

    print(
        "Unique customers:",
        f"{journey['customer_id'].nunique():,}"
    )

    print(
        "Unique bookings:",
        f"{journey['booking_id'].nunique():,}"
    )

    print("\nRISK DISTRIBUTION")
    print("-" * 40)

    print(
        journey["risk_level"]
        .value_counts()
        .sort_index()
    )

    print("\nANOMALY DISTRIBUTION")
    print("-" * 40)

    print(
        journey["anomaly_summary"]
        .value_counts()
        .head(10)
    )

    print("\nTOP 10 HIGHEST FRICTION JOURNEYS")
    print("-" * 40)

    top_columns = [
        "customer_id",
        "booking_id",
        "friction_score",
        "risk_level",
        "failed_payments",
        "retry_count",
        "booking_status",
        "anomaly_summary"
    ]

    print(
        journey
        .sort_values(
            "friction_score",
            ascending=False
        )
        [top_columns]
        .head(10)
        .to_string(index=False)
    )


# ============================================================
# INDIVIDUAL FORENSICS REPORT
# ============================================================

def print_forensics_report(
    journey,
    booking_id
):

    matches = journey[
        journey["booking_id"].astype(str)
        == str(booking_id)
    ]

    if matches.empty:

        print(
            f"\nBooking {booking_id} was not found."
        )

        return

    row = matches.iloc[0]

    print("\n")
    print("=" * 60)
    print("JOURNEY FORENSICS REPORT")
    print("=" * 60)

    # --------------------------------------------------------
    # Customer
    # --------------------------------------------------------

    print("\nCUSTOMER")
    print("-" * 60)

    print(
        "Customer ID:",
        row["customer_id"]
    )

    print(
        "Name:",
        f"{row['first_name']} {row['last_name']}"
    )

    print(
        "Country:",
        row["country"]
    )

    print(
        "Segment:",
        row["customer_segment"]
    )

    # --------------------------------------------------------
    # Booking
    # --------------------------------------------------------

    print("\nBOOKING")
    print("-" * 60)

    print(
        "Booking ID:",
        row["booking_id"]
    )

    print(
        "Trip ID:",
        row["trip_id"]
    )

    print(
        "Destination:",
        row["destination"]
    )

    print(
        "Trip Type:",
        row["trip_type"]
    )

    print(
        "Booking Date:",
        row["booking_date"]
    )

    print(
        "Booking Status:",
        row["booking_status"]
    )

    print(
        "Booking Amount:",
        f"{row['booking_amount']:,.2f}"
    )

    # --------------------------------------------------------
    # Payment
    # --------------------------------------------------------

    print("\nPAYMENT ANALYSIS")
    print("-" * 60)

    print(
        "Payment Attempts:",
        int(row["payment_attempts"])
    )

    print(
        "Failed Payments:",
        int(row["failed_payments"])
    )

    print(
        "Successful Payments:",
        int(row["successful_payments"])
    )

    print(
        "Retry Count:",
        int(row["retry_count"])
    )

    print(
        "Payment Success Rate:",
        f"{row['payment_success_rate'] * 100:.1f}%"
    )

    print(
        "Payment Duration:",
        f"{row['payment_duration_minutes']:.2f} minutes"
    )

    # --------------------------------------------------------
    # Journey
    # --------------------------------------------------------

    print("\nJOURNEY ANALYSIS")
    print("-" * 60)

    print(
        "Total Events:",
        int(row["total_events"])
    )

    print(
        "Search Events:",
        int(row["search_events"])
    )

    print(
        "Trip Views:",
        int(row["view_trip_events"])
    )

    print(
        "Booking Started:",
        int(row["booking_started_events"])
    )

    print(
        "Payment Started:",
        int(row["payment_started_events"])
    )

    print(
        "Payment Failed:",
        int(row["payment_failed_events"])
    )

    print(
        "Payment Retries:",
        int(row["payment_retry_events"])
    )

    print(
        "Payment Completed:",
        int(row["payment_completed_events"])
    )

    print(
        "Booking Confirmed:",
        int(row["booking_confirmed_events"])
    )

    print(
        "Journey Duration:",
        f"{row['journey_duration_minutes']:.2f} minutes"
    )

    # --------------------------------------------------------
    # Forensics
    # --------------------------------------------------------

    print("\nFORENSIC FINDINGS")
    print("-" * 60)

    print(
        "Friction Score:",
        f"{row['friction_score']:.0f}/100"
    )

    print(
        "Risk Level:",
        row["risk_level"]
    )

    print(
        "Anomaly Count:",
        int(row["anomaly_count"])
    )

    print("\nDetected Anomalies:")

    anomalies = str(
        row["anomaly_summary"]
    ).split(" | ")

    for anomaly in anomalies:

        print(
            f"  • {anomaly}"
        )

    # --------------------------------------------------------
    # Conclusion
    # --------------------------------------------------------

    print("\nFORENSIC CONCLUSION")
    print("-" * 60)

    if (
        row["successful_payments"] > 0
        and row["booking_status"] != "Confirmed"
    ):

        print(
            "Payment succeeded but the booking remained "
            "unresolved. This indicates a potential "
            "payment/booking state inconsistency."
        )

    elif row["failed_payments"] >= 2:

        print(
            "The customer experienced significant "
            "payment friction with multiple failed "
            "payment attempts."
        )

    elif row["retry_count"] >= 2:

        print(
            "The customer experienced repeated payment "
            "retries before completing the journey."
        )

    elif row["booking_status"] == "Cancelled":

        print(
            "The journey ended with a cancelled booking."
        )

    elif row["friction_score"] >= 60:

        print(
            "The journey contains significant friction "
            "that requires further investigation."
        )

    else:

        print(
            "No major journey friction was detected."
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "Building Journey Forensics feature dataset..."
    )

    journey_features = (
        build_customer_journey_features()
    )

    output_path = (
        PROCESSED_DIR
        / "customer_journey_features.csv"
    )

    journey_features.to_csv(
        output_path,
        index=False
    )

    print_report(
        journey_features
    )

    # --------------------------------------------------------
    # Example individual investigation
    # --------------------------------------------------------

    print_forensics_report(
        journey_features,
        "B007998"
    )

    print("\n")
    print("=" * 60)
    print("SUCCESS")
    print("=" * 60)

    print(
        "\nFeature dataset written to:"
    )

    print(
        output_path
    )

    print(
        "\nColumns generated:",
        len(journey_features.columns)
    )