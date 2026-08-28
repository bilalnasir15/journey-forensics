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
    "customer_journey_reconstructed.csv"
)

VALIDATION_FILE = os.path.join(
    PROCESSED_DIR,
    "day4_validation_report.csv"
)

SESSION_GAP_MINUTES = 30


# ============================================================
# INPUT FILES
# ============================================================

CUSTOMERS_FILE = os.path.join(
    RAW_DIR,
    "customers.csv"
)

BOOKINGS_FILE = os.path.join(
    RAW_DIR,
    "bookings.csv"
)

TRIPS_FILE = os.path.join(
    RAW_DIR,
    "trips.csv"
)

EVENTS_FILE = os.path.join(
    RAW_DIR,
    "events.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_csv(path, dataset_name):

    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"{dataset_name} not found:\n{path}"
        )

    try:
        return pd.read_csv(path)
    except Exception as exc:
        raise RuntimeError(
            f"Could not load {dataset_name}: {exc}"
        )


def load_data():

    print("=" * 60)
    print("DAY 4 — JOURNEY RECONSTRUCTION")
    print("=" * 60)

    print("\nLoading raw journey data...")

    customers = load_csv(
        CUSTOMERS_FILE,
        "customers.csv"
    )

    bookings = load_csv(
        BOOKINGS_FILE,
        "bookings.csv"
    )

    trips = load_csv(
        TRIPS_FILE,
        "trips.csv"
    )

    events = load_csv(
        EVENTS_FILE,
        "events.csv"
    )

    print(
        f"Customers: {len(customers):,}"
    )

    print(
        f"Bookings: {len(bookings):,}"
    )

    print(
        f"Trips: {len(trips):,}"
    )

    print(
        f"Events: {len(events):,}"
    )

    return (
        customers,
        bookings,
        trips,
        events
    )


# ============================================================
# VALIDATE INPUT SCHEMA
# ============================================================

def validate_input_schema(
    customers,
    bookings,
    trips,
    events
):

    required_columns = {

        "customers": [
            "customer_id",
            "first_name",
            "last_name",
            "country",
            "customer_segment"
        ],

        "bookings": [
            "booking_id",
            "customer_id",
            "trip_id",
            "booking_date",
            "booking_amount",
            "booking_status"
        ],

        "trips": [
            "trip_id",
            "destination",
            "trip_type",
            "departure_date",
            "return_date"
        ],

        "events": [
            "event_id",
            "customer_id",
            "booking_id",
            "event_type",
            "event_timestamp"
        ]
    }

    datasets = {
        "customers": customers,
        "bookings": bookings,
        "trips": trips,
        "events": events
    }

    errors = []

    for dataset_name, required in required_columns.items():

        actual = set(
            datasets[dataset_name].columns
        )

        missing = set(required) - actual

        if missing:
            errors.append(
                f"{dataset_name}: {sorted(missing)}"
            )

    if errors:
        raise ValueError(
            "Input schema validation failed:\n"
            + "\n".join(errors)
        )


# ============================================================
# PREPARE EVENTS
# ============================================================

def prepare_events(events):

    print(
        "\nPreparing event stream..."
    )

    df = events.copy()

    df["event_timestamp"] = pd.to_datetime(
        df["event_timestamp"],
        errors="coerce"
    )

    if df["event_timestamp"].isna().any():

        invalid = int(
            df["event_timestamp"].isna().sum()
        )

        raise ValueError(
            f"Found {invalid} invalid event timestamps."
        )

    df = df.sort_values(
        [
            "customer_id",
            "event_timestamp",
            "event_id"
        ]
    ).reset_index(
        drop=True
    )

    return df


# ============================================================
# EVENT MODELING
# ============================================================

def build_event_model(events):

    print(
        "Building event model..."
    )

    df = events.copy()

    # --------------------------------------------------------
    # Previous event
    # --------------------------------------------------------

    df["previous_event_timestamp"] = (
        df.groupby(
            "customer_id"
        )[
            "event_timestamp"
        ]
        .shift(1)
    )

    df["previous_event_type"] = (
        df.groupby(
            "customer_id"
        )[
            "event_type"
        ]
        .shift(1)
    )

    # --------------------------------------------------------
    # Next event
    # --------------------------------------------------------

    df["next_event_timestamp"] = (
        df.groupby(
            "customer_id"
        )[
            "event_timestamp"
        ]
        .shift(-1)
    )

    df["next_event_type"] = (
        df.groupby(
            "customer_id"
        )[
            "event_type"
        ]
        .shift(-1)
    )

    # --------------------------------------------------------
    # Time since previous
    # --------------------------------------------------------

    df["minutes_since_previous_event"] = (

        (
            df["event_timestamp"]
            -
            df["previous_event_timestamp"]
        )
        .dt.total_seconds()
        / 60.0

    )

    df["minutes_since_previous_event"] = (
        df["minutes_since_previous_event"]
        .fillna(0)
        .round(2)
    )

    # --------------------------------------------------------
    # Time until next
    # --------------------------------------------------------

    df["minutes_until_next_event"] = (

        (
            df["next_event_timestamp"]
            -
            df["event_timestamp"]
        )
        .dt.total_seconds()
        / 60.0

    )

    df["minutes_until_next_event"] = (
        df["minutes_until_next_event"]
        .fillna(0)
        .round(2)
    )

    # --------------------------------------------------------
    # Customer event sequence
    # --------------------------------------------------------

    df["customer_event_sequence"] = (
        df.groupby(
            "customer_id"
        )
        .cumcount()
        + 1
    )

    # --------------------------------------------------------
    # Booking event sequence
    # --------------------------------------------------------

    df["booking_event_sequence"] = (
        df.groupby(
            "booking_id"
        )
        .cumcount()
        + 1
    )

    return df


# ============================================================
# SESSIONIZATION
# ============================================================

def sessionize_events(events):

    print(
        f"Sessionizing events "
        f"(gap > {SESSION_GAP_MINUTES} minutes = new session)..."
    )

    df = events.copy()

    df["new_session_flag"] = np.where(

        df["previous_event_timestamp"].isna()
        |
        (
            df["minutes_since_previous_event"]
            >
            SESSION_GAP_MINUTES
        ),

        1,
        0
    )

    df["session_number"] = (
        df.groupby(
            "customer_id"
        )[
            "new_session_flag"
        ]
        .cumsum()
        .astype(int)
    )

    df["session_id"] = (
        df["customer_id"].astype(str)
        + "_S"
        + df["session_number"]
        .astype(str)
        .str.zfill(4)
    )

    return df


# ============================================================
# SESSION METRICS
# ============================================================

def build_session_metrics(events):

    print(
        "Building session metrics..."
    )

    session_metrics = (
        events
        .groupby(
            [
                "customer_id",
                "session_id",
                "session_number"
            ],
            as_index=False
        )
        .agg(
            session_start=(
                "event_timestamp",
                "min"
            ),
            session_end=(
                "event_timestamp",
                "max"
            ),
            session_event_count=(
                "event_id",
                "count"
            ),
            session_booking_count=(
                "booking_id",
                "nunique"
            )
        )
    )

    session_metrics[
        "session_duration_minutes"
    ] = (
        (
            session_metrics["session_end"]
            -
            session_metrics["session_start"]
        )
        .dt.total_seconds()
        / 60.0
    ).round(2)

    return session_metrics


# ============================================================
# BOOKING JOURNEY METRICS
# ============================================================

def build_booking_journey_metrics(events):

    print(
        "Building booking journey metrics..."
    )

    metrics = (
        events
        .groupby(
            [
                "customer_id",
                "booking_id"
            ],
            as_index=False
        )
        .agg(
            journey_start=(
                "event_timestamp",
                "min"
            ),
            journey_end=(
                "event_timestamp",
                "max"
            ),
            journey_event_count=(
                "event_id",
                "count"
            ),
            journey_session_count=(
                "session_id",
                "nunique"
            ),
            search_events=(
                "event_type",
                lambda x: (
                    x == "SEARCH"
                ).sum()
            ),
            view_trip_events=(
                "event_type",
                lambda x: (
                    x == "VIEW_TRIP"
                ).sum()
            ),
            booking_started_events=(
                "event_type",
                lambda x: (
                    x == "BOOKING_STARTED"
                ).sum()
            ),
            booking_created_events=(
                "event_type",
                lambda x: (
                    x == "BOOKING_CREATED"
                ).sum()
            ),
            payment_started_events=(
                "event_type",
                lambda x: (
                    x == "PAYMENT_STARTED"
                ).sum()
            ),
            payment_failed_events=(
                "event_type",
                lambda x: (
                    x == "PAYMENT_FAILED"
                ).sum()
            ),
            payment_retry_events=(
                "event_type",
                lambda x: (
                    x == "PAYMENT_RETRY"
                ).sum()
            ),
            payment_completed_events=(
                "event_type",
                lambda x: (
                    x == "PAYMENT_COMPLETED"
                ).sum()
            ),
            booking_confirmed_events=(
                "event_type",
                lambda x: (
                    x == "BOOKING_CONFIRMED"
                ).sum()
            )
        )
    )

    metrics[
        "journey_duration_minutes"
    ] = (
        (
            metrics["journey_end"]
            -
            metrics["journey_start"]
        )
        .dt.total_seconds()
        / 60.0
    ).round(2)

    return metrics


# ============================================================
# BUILD CUSTOMER JOURNEY
# ============================================================

def build_customer_journey(
    events,
    customers,
    bookings,
    trips,
    session_metrics,
    booking_metrics
):

    print(
        "Building reconstructed customer journey..."
    )

    df = events.merge(
        customers[
            [
                "customer_id",
                "first_name",
                "last_name",
                "country",
                "customer_segment"
            ]
        ],
        on="customer_id",
        how="left",
        validate="many_to_one"
    )

    df = df.merge(
        bookings[
            [
                "booking_id",
                "trip_id",
                "booking_date",
                "booking_amount",
                "booking_status"
            ]
        ],
        on="booking_id",
        how="left",
        validate="many_to_one"
    )

    df = df.merge(
        trips[
            [
                "trip_id",
                "destination",
                "trip_type"
            ]
        ],
        on="trip_id",
        how="left",
        validate="many_to_one"
    )

    df = df.merge(
        session_metrics,
        on=[
            "customer_id",
            "session_id",
            "session_number"
        ],
        how="left",
        validate="many_to_one"
    )

    df = df.merge(
        booking_metrics,
        on=[
            "customer_id",
            "booking_id"
        ],
        how="left",
        validate="many_to_one"
    )

    return df


# ============================================================
# JOURNEY STATES
# ============================================================

def derive_journey_states(df):

    print(
        "Deriving journey states..."
    )

    df = df.copy()

    booking_status = (
        df["booking_status"]
        .astype(str)
        .str.upper()
    )

    df["journey_outcome"] = np.select(

        [

            df[
                "booking_confirmed_events"
            ] > 0,

            (
                df[
                    "payment_completed_events"
                ] > 0
            )
            &
            (
                df[
                    "booking_confirmed_events"
                ] == 0
            ),

            booking_status.eq(
                "CANCELLED"
            ),

            booking_status.eq(
                "PENDING"
            )
        ],

        [

            "COMPLETED",

            "PAYMENT_COMPLETED_UNRESOLVED",

            "CANCELLED",

            "PENDING"
        ],

        default="IN_PROGRESS"
    )

    df["journey_health"] = np.select(

        [

            df[
                "payment_failed_events"
            ] >= 2,

            df[
                "payment_failed_events"
            ] > 0,

            df[
                "journey_duration_minutes"
            ] > 90,

            df[
                "journey_outcome"
            ].eq("COMPLETED")
        ],

        [

            "HIGH_FRICTION",

            "FRICTION_DETECTED",

            "LONG_JOURNEY",

            "HEALTHY"
        ],

        default="NORMAL"
    )

    return df


# ============================================================
# FINALIZE OUTPUT
# ============================================================

def finalize_output(df):

    output_columns = [

        # ----------------------------------------------------
        # Customer
        # ----------------------------------------------------

        "customer_id",
        "first_name",
        "last_name",
        "country",
        "customer_segment",

        # ----------------------------------------------------
        # Booking
        # ----------------------------------------------------

        "booking_id",
        "trip_id",
        "booking_date",
        "booking_amount",
        "booking_status",
        "destination",
        "trip_type",

        # ----------------------------------------------------
        # Event
        # ----------------------------------------------------

        "event_id",
        "event_type",
        "event_timestamp",

        # ----------------------------------------------------
        # Event sequence / navigation
        # ----------------------------------------------------

        "customer_event_sequence",
        "booking_event_sequence",

        "previous_event_type",
        "previous_event_timestamp",

        "next_event_type",
        "next_event_timestamp",

        "minutes_since_previous_event",
        "minutes_until_next_event",

        # ----------------------------------------------------
        # Session
        # ----------------------------------------------------

        "session_id",
        "session_number",
        "session_start",
        "session_end",
        "session_duration_minutes",
        "session_event_count",
        "session_booking_count",

        # ----------------------------------------------------
        # Journey
        # ----------------------------------------------------

        "journey_start",
        "journey_end",
        "journey_event_count",
        "journey_session_count",
        "journey_duration_minutes",

        # ----------------------------------------------------
        # Event counts
        # ----------------------------------------------------

        "search_events",
        "view_trip_events",
        "booking_started_events",
        "booking_created_events",
        "payment_started_events",
        "payment_failed_events",
        "payment_retry_events",
        "payment_completed_events",
        "booking_confirmed_events",

        # ----------------------------------------------------
        # Derived states
        # ----------------------------------------------------

        "journey_outcome",
        "journey_health"
    ]

    output_columns = [
        column
        for column in output_columns
        if column in df.columns
    ]

    result = df[
        output_columns
    ].copy()

    # --------------------------------------------------------
    # Ensure timestamp columns remain real datetimes
    # before writing
    # --------------------------------------------------------

    timestamp_columns = [
        "event_timestamp",
        "previous_event_timestamp",
        "next_event_timestamp",
        "session_start",
        "session_end",
        "journey_start",
        "journey_end"
    ]

    for column in timestamp_columns:

        if column in result.columns:

            result[column] = pd.to_datetime(
                result[column],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "minutes_since_previous_event",
        "minutes_until_next_event",
        "session_duration_minutes",
        "journey_duration_minutes"
    ]

    for column in numeric_columns:

        if column in result.columns:

            result[column] = (
                pd.to_numeric(
                    result[column],
                    errors="coerce"
                )
                .fillna(0)
                .round(2)
            )

    return result


# ============================================================
# REPORT
# ============================================================

def print_report(
    events,
    session_metrics,
    booking_metrics,
    result
):

    print()
    print("=" * 60)
    print("JOURNEY RECONSTRUCTION REPORT")
    print("=" * 60)

    print()
    print(
        f"Reconstructed event records: "
        f"{len(result):,}"
    )

    print(
        f"Unique customers: "
        f"{result['customer_id'].nunique():,}"
    )

    print(
        f"Unique bookings: "
        f"{result['booking_id'].nunique():,}"
    )

    print(
        f"Unique sessions: "
        f"{result['session_id'].nunique():,}"
    )

    print()
    print("JOURNEY OUTCOME DISTRIBUTION")
    print("-" * 40)

    print(
        result[
            [
                "booking_id",
                "journey_outcome"
            ]
        ]
        .drop_duplicates()
        [
            "journey_outcome"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print("JOURNEY HEALTH DISTRIBUTION")
    print("-" * 40)

    print(
        result[
            [
                "booking_id",
                "journey_health"
            ]
        ]
        .drop_duplicates()
        [
            "journey_health"
        ]
        .value_counts()
        .to_string()
    )

    # --------------------------------------------------------
    # Example booking
    # --------------------------------------------------------

    example_booking = (
        "B007998"
        if "B007998"
        in set(result["booking_id"])
        else result["booking_id"].iloc[0]
    )

    example = (
        result[
            result["booking_id"]
            == example_booking
        ]
        .sort_values(
            [
                "event_timestamp",
                "event_id"
            ]
        )
    )

    print()
    print("=" * 60)
    print(
        f"EXAMPLE RECONSTRUCTED JOURNEY: "
        f"{example_booking}"
    )
    print("=" * 60)

    display_columns = [
        "customer_id",
        "booking_id",
        "session_id",
        "customer_event_sequence",
        "event_type",
        "event_timestamp",
        "previous_event_type",
        "previous_event_timestamp",
        "next_event_type",
        "next_event_timestamp",
        "minutes_since_previous_event"
    ]

    display_columns = [
        column
        for column in display_columns
        if column in example.columns
    ]

    print(
        example[
            display_columns
        ].to_string(
            index=False
        )
    )


# ============================================================
# INTERNAL VALIDATION
# ============================================================

def validate_reconstruction(
    customers,
    bookings,
    events,
    result,
    session_metrics,
    booking_metrics
):

    print()
    print("=" * 60)
    print("DAY 4 INTERNAL VALIDATION")
    print("=" * 60)

    checks = []

    # --------------------------------------------------------
    # Event count
    # --------------------------------------------------------

    checks.append(
        (
            "Event count preserved",
            len(result) == len(events),
            (
                f"Raw={len(events):,}, "
                f"Reconstructed={len(result):,}"
            )
        )
    )

    # --------------------------------------------------------
    # Customer coverage
    # --------------------------------------------------------

    checks.append(
        (
            "Customer coverage preserved",
            (
                result["customer_id"].nunique()
                ==
                events["customer_id"].nunique()
            ),
            (
                f"Raw={events['customer_id'].nunique():,}, "
                f"Reconstructed={result['customer_id'].nunique():,}"
            )
        )
    )

    # --------------------------------------------------------
    # Booking coverage
    # --------------------------------------------------------

    checks.append(
        (
            "Booking coverage preserved",
            (
                result["booking_id"].nunique()
                ==
                events["booking_id"].nunique()
            ),
            (
                f"Raw={events['booking_id'].nunique():,}, "
                f"Reconstructed={result['booking_id'].nunique():,}"
            )
        )
    )

    # --------------------------------------------------------
    # Event IDs
    # --------------------------------------------------------

    checks.append(
        (
            "Event IDs remain unique",
            result["event_id"].is_unique,
            (
                f"Duplicates="
                f"{result['event_id'].duplicated().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # Customer join
    # --------------------------------------------------------

    checks.append(
        (
            "No missing customer attributes",
            result["first_name"].notna().all(),
            (
                f"Missing="
                f"{result['first_name'].isna().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # Booking join
    # --------------------------------------------------------

    checks.append(
        (
            "No missing booking attributes",
            result["booking_status"].notna().all(),
            (
                f"Missing="
                f"{result['booking_status'].isna().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # Trip join
    # --------------------------------------------------------

    checks.append(
        (
            "No missing trip attributes",
            result["destination"].notna().all(),
            (
                f"Missing="
                f"{result['destination'].isna().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # Session
    # --------------------------------------------------------

    checks.append(
        (
            "Session IDs populated",
            result["session_id"].notna().all(),
            (
                f"Missing="
                f"{result['session_id'].isna().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # Session numbers
    # --------------------------------------------------------

    session_numbers = pd.to_numeric(
        result["session_number"],
        errors="coerce"
    )

    checks.append(
        (
            "Session numbers valid",
            session_numbers.ge(1).all(),
            (
                f"Min={session_numbers.min()}"
            )
        )
    )

    # --------------------------------------------------------
    # Session metric count
    # --------------------------------------------------------

    checks.append(
        (
            "Session event counts reconcile",
            (
                session_metrics[
                    "session_event_count"
                ].sum()
                ==
                len(events)
            ),
            (
                f"Sessions events="
                f"{session_metrics['session_event_count'].sum():,}, "
                f"Raw events={len(events):,}"
            )
        )
    )

    # --------------------------------------------------------
    # Booking journey coverage
    # --------------------------------------------------------

    checks.append(
        (
            "Booking journey metrics cover all bookings",
            (
                booking_metrics["booking_id"].nunique()
                ==
                events["booking_id"].nunique()
            ),
            (
                f"Metrics="
                f"{booking_metrics['booking_id'].nunique():,}, "
                f"Raw="
                f"{events['booking_id'].nunique():,}"
            )
        )
    )

    # --------------------------------------------------------
    # Journey duration
    # --------------------------------------------------------

    journey_duration = pd.to_numeric(
        result["journey_duration_minutes"],
        errors="coerce"
    )

    checks.append(
        (
            "Journey duration is non-negative",
            journey_duration.ge(0).all(),
            (
                f"Min={journey_duration.min():.2f}, "
                f"Max={journey_duration.max():.2f}"
            )
        )
    )

    # --------------------------------------------------------
    # Session duration
    # --------------------------------------------------------

    session_duration = pd.to_numeric(
        result["session_duration_minutes"],
        errors="coerce"
    )

    checks.append(
        (
            "Session duration is non-negative",
            session_duration.ge(0).all(),
            (
                f"Min={session_duration.min():.2f}, "
                f"Max={session_duration.max():.2f}"
            )
        )
    )

    # --------------------------------------------------------
    # Timestamp columns
    # --------------------------------------------------------

    result_copy = result.copy()

    timestamp_columns = [
        "event_timestamp",
        "previous_event_timestamp",
        "next_event_timestamp"
    ]

    timestamp_checks = []

    for column in timestamp_columns:

        if column in result_copy.columns:

            result_copy[column] = pd.to_datetime(
                result_copy[column],
                errors="coerce"
            )

            # Allow nulls for previous/next at boundaries.
            if column == "event_timestamp":

                timestamp_checks.append(
                    result_copy[column].notna().all()
                )

    checks.append(
        (
            "Event timestamps are valid",
            all(timestamp_checks),
            "Event timestamps parsed successfully"
        )
    )

    # --------------------------------------------------------
    # Previous/next event logic
    # --------------------------------------------------------

    checks.append(
        (
            "Previous/next event fields exist",
            (
                "previous_event_timestamp"
                in result.columns
                and
                "next_event_timestamp"
                in result.columns
            ),
            "Navigation fields present"
        )
    )

    # --------------------------------------------------------
    # Journey outcomes
    # --------------------------------------------------------

    checks.append(
        (
            "Journey outcomes populated",
            result["journey_outcome"].notna().all(),
            (
                f"Missing="
                f"{result['journey_outcome'].isna().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # Journey health
    # --------------------------------------------------------

    checks.append(
        (
            "Journey health populated",
            result["journey_health"].notna().all(),
            (
                f"Missing="
                f"{result['journey_health'].isna().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # Display
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

    failed = len(checks) - passed

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

    return failed == 0


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        (
            customers,
            bookings,
            trips,
            events
        ) = load_data()

        validate_input_schema(
            customers,
            bookings,
            trips,
            events
        )

        events = prepare_events(
            events
        )

        events = build_event_model(
            events
        )

        events = sessionize_events(
            events
        )

        session_metrics = (
            build_session_metrics(
                events
            )
        )

        booking_metrics = (
            build_booking_journey_metrics(
                events
            )
        )

        reconstructed = (
            build_customer_journey(
                events,
                customers,
                bookings,
                trips,
                session_metrics,
                booking_metrics
            )
        )

        reconstructed = (
            derive_journey_states(
                reconstructed
            )
        )

        output = finalize_output(
            reconstructed
        )

        os.makedirs(
            PROCESSED_DIR,
            exist_ok=True
        )

        output.to_csv(
            OUTPUT_FILE,
            index=False
        )

        print_report(
            events,
            session_metrics,
            booking_metrics,
            output
        )

        validation_passed = (
            validate_reconstruction(
                customers,
                bookings,
                events,
                output,
                session_metrics,
                booking_metrics
            )
        )

        print()
        print("=" * 60)

        if validation_passed:

            print(
                "DAY 4 JOURNEY RECONSTRUCTION: PASSED"
            )

        else:

            print(
                "DAY 4 JOURNEY RECONSTRUCTION: FAILED"
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
            f"Output records: {len(output):,}"
        )

        print(
            f"Output columns: {len(output.columns):,}"
        )

        return 0 if validation_passed else 1

    except Exception as exc:

        print()
        print("=" * 60)
        print(
            "DAY 4 JOURNEY RECONSTRUCTION: FAILED"
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