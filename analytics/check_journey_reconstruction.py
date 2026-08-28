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

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "customer_journey_reconstructed.csv"
)

VALIDATION_FILE = os.path.join(
    PROCESSED_DIR,
    "day4_validation_report.csv"
)

EXPECTED_EVENTS = 61673


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
# LOAD CSV
# ============================================================

def load_csv(path):

    if not os.path.isfile(path):

        return None

    try:

        return pd.read_csv(path)

    except Exception:

        return None


# ============================================================
# PARSE TIMESTAMPS
# ============================================================

def parse_timestamps(df):

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

        if column in df.columns:

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 4 JOURNEY RECONSTRUCTION CHECK")
    print("=" * 60)

    # ========================================================
    # FILE EXISTS
    # ========================================================

    check(
        "Reconstructed journey file exists",
        os.path.isfile(OUTPUT_FILE),
        OUTPUT_FILE
    )

    if not os.path.isfile(
        OUTPUT_FILE
    ):

        return 1

    # ========================================================
    # LOAD
    # ========================================================

    try:

        df = pd.read_csv(
            OUTPUT_FILE
        )

    except Exception as exc:

        check(
            "Reconstructed journey file can be loaded",
            False,
            str(exc)
        )

        return 1

    check(
        "Reconstructed journey file can be loaded",
        True,
        f"{len(df):,} records"
    )

    # ========================================================
    # PARSE TIMESTAMPS
    # ========================================================

    df = parse_timestamps(
        df
    )

    # ========================================================
    # EVENT COUNT
    # ========================================================

    check(
        "Event count preserved",
        len(df) == EXPECTED_EVENTS,
        (
            f"Expected={EXPECTED_EVENTS:,}, "
            f"Actual={len(df):,}"
        )
    )

    # ========================================================
    # REQUIRED COLUMNS
    # ========================================================

    required_columns = [

        "customer_id",
        "booking_id",
        "event_id",
        "event_type",
        "event_timestamp",

        "customer_event_sequence",
        "booking_event_sequence",

        "previous_event_type",
        "previous_event_timestamp",

        "next_event_type",
        "next_event_timestamp",

        "minutes_since_previous_event",
        "minutes_until_next_event",

        "session_id",
        "session_number",
        "session_start",
        "session_end",
        "session_duration_minutes",

        "journey_start",
        "journey_end",
        "journey_event_count",
        "journey_session_count",
        "journey_duration_minutes",

        "journey_outcome",
        "journey_health"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    check(
        "Required reconstruction columns exist",
        len(missing_columns) == 0,
        (
            "All required columns present"
            if not missing_columns
            else f"Missing={missing_columns}"
        )
    )

    # ========================================================
    # UNIQUE EVENT IDs
    # ========================================================

    check(
        "Event IDs are unique",
        df["event_id"].is_unique,
        (
            f"Duplicates="
            f"{df['event_id'].duplicated().sum()}"
        )
    )

    # ========================================================
    # CRITICAL FIELDS
    # ========================================================

    critical_columns = [

        "customer_id",
        "booking_id",
        "event_id",
        "event_type",
        "event_timestamp",
        "session_id",
        "session_number",
        "journey_outcome",
        "journey_health"
    ]

    missing_critical = int(
        df[
            critical_columns
        ]
        .isna()
        .sum()
        .sum()
    )

    check(
        "No missing critical journey fields",
        missing_critical == 0,
        f"Missing={missing_critical}"
    )

    # ========================================================
    # EVENT TIMESTAMP VALIDATION
    # ========================================================

    event_timestamp_invalid = int(
        df[
            "event_timestamp"
        ]
        .isna()
        .sum()
    )

    check(
        "Event timestamps are valid",
        event_timestamp_invalid == 0,
        f"Invalid={event_timestamp_invalid}"
    )

    # ========================================================
    # TIMESTAMP COLUMN TYPES
    # ========================================================

    check(
        "Event timestamp parsed correctly",
        pd.api.types.is_datetime64_any_dtype(
            df["event_timestamp"]
        ),
        str(
            df["event_timestamp"].dtype
        )
    )

    # ========================================================
    # SESSION NUMBERS
    # ========================================================

    session_numbers = pd.to_numeric(
        df["session_number"],
        errors="coerce"
    )

    check(
        "Session numbers are >= 1",
        session_numbers
        .ge(1)
        .all(),
        (
            f"Min={session_numbers.min()}"
        )
    )

    # ========================================================
    # JOURNEY DURATIONS
    # ========================================================

    journey_duration = pd.to_numeric(
        df[
            "journey_duration_minutes"
        ],
        errors="coerce"
    )

    check(
        "Journey durations are non-negative",
        journey_duration
        .ge(0)
        .all(),
        (
            f"Min={journey_duration.min():.2f}, "
            f"Max={journey_duration.max():.2f}"
        )
    )

    # ========================================================
    # SESSION DURATIONS
    # ========================================================

    session_duration = pd.to_numeric(
        df[
            "session_duration_minutes"
        ],
        errors="coerce"
    )

    check(
        "Session durations are non-negative",
        session_duration
        .ge(0)
        .all(),
        (
            f"Min={session_duration.min():.2f}, "
            f"Max={session_duration.max():.2f}"
        )
    )

    # ========================================================
    # CUSTOMER COVERAGE
    # ========================================================

    raw_events_file = os.path.join(
        RAW_DIR,
        "events.csv"
    )

    raw_events = pd.read_csv(
        raw_events_file
    )

    check(
        "Customer coverage preserved",
        (
            df[
                "customer_id"
            ].nunique()
            ==
            raw_events[
                "customer_id"
            ].nunique()
        ),
        (
            f"Raw="
            f"{raw_events['customer_id'].nunique():,}, "
            f"Reconstructed="
            f"{df['customer_id'].nunique():,}"
        )
    )

    # ========================================================
    # BOOKING COVERAGE
    # ========================================================

    check(
        "Booking coverage preserved",
        (
            df[
                "booking_id"
            ].nunique()
            ==
            raw_events[
                "booking_id"
            ].nunique()
        ),
        (
            f"Raw="
            f"{raw_events['booking_id'].nunique():,}, "
            f"Reconstructed="
            f"{df['booking_id'].nunique():,}"
        )
    )

    # ========================================================
    # SESSION IDS
    # ========================================================

    check(
        "Session IDs populated",
        df[
            "session_id"
        ].notna().all(),
        (
            f"Missing="
            f"{df['session_id'].isna().sum()}"
        )
    )

    # ========================================================
    # OUTCOMES
    # ========================================================

    valid_outcomes = {

        "COMPLETED",

        "PAYMENT_COMPLETED_UNRESOLVED",

        "CANCELLED",

        "PENDING",

        "IN_PROGRESS"
    }

    actual_outcomes = set(
        df[
            "journey_outcome"
        ]
        .dropna()
        .astype(str)
    )

    check(
        "Journey outcomes are valid",
        actual_outcomes.issubset(
            valid_outcomes
        ),
        str(
            sorted(
                actual_outcomes
            )
        )
    )

    # ========================================================
    # JOURNEY HEALTH
    # ========================================================

    valid_health = {

        "HEALTHY",

        "NORMAL",

        "FRICTION_DETECTED",

        "HIGH_FRICTION",

        "LONG_JOURNEY"
    }

    actual_health = set(
        df[
            "journey_health"
        ]
        .dropna()
        .astype(str)
    )

    check(
        "Journey health values are valid",
        actual_health.issubset(
            valid_health
        ),
        str(
            sorted(
                actual_health
            )
        )
    )

    # ========================================================
    # CUSTOMER EVENT SEQUENCE
    # ========================================================

    ordered = df.sort_values(
        [
            "customer_id",
            "event_timestamp",
            "event_id"
        ]
    ).copy()

    expected_sequence = (
        ordered
        .groupby(
            "customer_id"
        )
        .cumcount()
        + 1
    )

    actual_sequence = pd.to_numeric(
        ordered[
            "customer_event_sequence"
        ],
        errors="coerce"
    )

    sequence_valid = (
        expected_sequence
        .reset_index(drop=True)
        ==
        actual_sequence
        .reset_index(drop=True)
    ).all()

    check(
        "Customer event sequences are chronological",
        bool(sequence_valid)
    )

    # ========================================================
    # PREVIOUS/NEXT TIMESTAMP LOGIC
    # ========================================================

    sequence_df = ordered.copy()

    expected_previous = (
        sequence_df
        .groupby(
            "customer_id"
        )[
            "event_timestamp"
        ]
        .shift(1)
    )

    expected_next = (
        sequence_df
        .groupby(
            "customer_id"
        )[
            "event_timestamp"
        ]
        .shift(-1)
    )

    actual_previous = (
        pd.to_datetime(
            sequence_df[
                "previous_event_timestamp"
            ],
            errors="coerce"
        )
    )

    actual_next = (
        pd.to_datetime(
            sequence_df[
                "next_event_timestamp"
            ],
            errors="coerce"
        )
    )

    previous_valid = (
        expected_previous.reset_index(
            drop=True
        )
        ==
        actual_previous.reset_index(
            drop=True
        )
    ) | (
        expected_previous.isna().reset_index(
            drop=True
        )
        &
        actual_previous.isna().reset_index(
            drop=True
        )
    )

    next_valid = (
        expected_next.reset_index(
            drop=True
        )
        ==
        actual_next.reset_index(
            drop=True
        )
    ) | (
        expected_next.isna().reset_index(
            drop=True
        )
        &
        actual_next.isna().reset_index(
            drop=True
        )
    )

    check(
        "Previous event timestamps are correct",
        bool(previous_valid.all())
    )

    check(
        "Next event timestamps are correct",
        bool(next_valid.all())
    )

    # ========================================================
    # SESSIONIZATION
    # ========================================================

    session_check = ordered.copy()

    session_check[
        "previous_timestamp"
    ] = (
        session_check
        .groupby(
            "customer_id"
        )[
            "event_timestamp"
        ]
        .shift(1)
    )

    session_check[
        "gap_minutes"
    ] = (

        (
            session_check[
                "event_timestamp"
            ]
            -
            session_check[
                "previous_timestamp"
            ]
        )
        .dt.total_seconds()
        / 60.0
    )

    expected_new_session = (

        session_check[
            "previous_timestamp"
        ].isna()

        |

        session_check[
            "gap_minutes"
        ].gt(30)
    )

    expected_session_number = (
        expected_new_session
        .groupby(
            session_check[
                "customer_id"
            ]
        )
        .cumsum()
        .astype(int)
    )

    actual_session_number = pd.to_numeric(
        session_check[
            "session_number"
        ],
        errors="coerce"
    ).astype(int)

    session_valid = (
        expected_session_number
        .reset_index(drop=True)
        ==
        actual_session_number
        .reset_index(drop=True)
    ).all()

    check(
        "30-minute sessionization rule is valid",
        bool(session_valid),
        "New session when event gap > 30 minutes"
    )

    # ========================================================
    # RAW EVENT COUNT RECONCILIATION
    # ========================================================

    check(
        "Reconstructed events match raw events",
        len(df) == len(raw_events),
        (
            f"Raw={len(raw_events):,}, "
            f"Reconstructed={len(df):,}"
        )
    )

    # ========================================================
    # EVENT IDS RECONCILIATION
    # ========================================================

    raw_event_ids = set(
        raw_events[
            "event_id"
        ]
        .astype(str)
    )

    reconstructed_event_ids = set(
        df[
            "event_id"
        ]
        .astype(str)
    )

    check(
        "All raw event IDs represented",
        raw_event_ids
        ==
        reconstructed_event_ids,
        (
            f"Missing="
            f"{len(raw_event_ids - reconstructed_event_ids)}, "
            f"Extra="
            f"{len(reconstructed_event_ids - raw_event_ids)}"
        )
    )

    # ========================================================
    # VALIDATION REPORT
    # ========================================================

    validation_df = pd.DataFrame(
        results
    )

    validation_df.to_csv(
        VALIDATION_FILE,
        index=False
    )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    total = len(
        validation_df
    )

    passed = int(
        (
            validation_df["status"]
            == "PASS"
        ).sum()
    )

    failed = total - passed

    pass_rate = round(
        (
            passed
            /
            total
        )
        *
        100,
        2
    )

    print()
    print("=" * 60)
    print("DAY 4 VALIDATION SUMMARY")
    print("=" * 60)

    print(
        f"Total checks: {total}"
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
            "DAY 4 JOURNEY RECONSTRUCTION: PASSED"
        )
        print("=" * 60)

        print()
        print(
            "Journey reconstruction, sessionization, "
            "event navigation, and reconciliation "
            "are validated successfully."
        )

        print()
        print(
            "Validation report:"
        )

        print(
            VALIDATION_FILE
        )

        return 0

    else:

        print("=" * 60)
        print(
            "DAY 4 JOURNEY RECONSTRUCTION: FAILED"
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

        print()
        print(
            "Validation report:"
        )

        print(
            VALIDATION_FILE
        )

        return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )