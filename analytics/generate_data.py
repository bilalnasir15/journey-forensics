import pandas as pd
import numpy as np
from faker import Faker


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 42

np.random.seed(SEED)

fake = Faker()
fake.seed_instance(SEED)


# ============================================================
# CUSTOMERS
# ============================================================

def generate_customers(num_customers=5000):

    np.random.seed(SEED)

    customers = pd.DataFrame({

        "customer_id": [
            f"C{i:06d}"
            for i in range(1, num_customers + 1)
        ],

        "first_name": [
            fake.first_name()
            for _ in range(num_customers)
        ],

        "last_name": [
            fake.last_name()
            for _ in range(num_customers)
        ],

        "country": np.random.choice(
            [
                "Saudi Arabia",
                "United Arab Emirates",
                "Pakistan",
                "United Kingdom",
                "United States",
                "Other"
            ],
            size=num_customers,
            p=[
                0.30,
                0.20,
                0.15,
                0.10,
                0.10,
                0.15
            ]
        ),

        "signup_date": pd.to_datetime(
            np.random.choice(
                pd.date_range(
                    "2023-01-01",
                    "2026-06-30"
                ),
                size=num_customers
            )
        ),

        "date_of_birth": pd.to_datetime(
            np.random.choice(
                pd.date_range(
                    "1960-01-01",
                    "2005-12-31"
                ),
                size=num_customers
            )
        ),

        "customer_segment": np.random.choice(
            [
                "Standard",
                "Premium",
                "VIP"
            ],
            size=num_customers,
            p=[
                0.70,
                0.25,
                0.05
            ]
        )
    })

    return customers


# ============================================================
# TRIPS
# ============================================================

def generate_trips(num_trips=50):

    np.random.seed(SEED)

    destinations = [
        "Jeddah",
        "Dubai",
        "Abu Dhabi",
        "Red Sea",
        "Mediterranean"
    ]

    trip_types = [
        "Cruise",
        "Luxury",
        "Family",
        "Adventure",
        "Business"
    ]

    departure_dates = pd.to_datetime(
        np.random.choice(
            pd.date_range(
                "2026-01-01",
                "2026-12-31"
            ),
            size=num_trips
        )
    )

    trip_durations = np.random.randint(
        3,
        11,
        size=num_trips
    )

    return_dates = (
        departure_dates
        + pd.to_timedelta(
            trip_durations,
            unit="D"
        )
    )

    trips = pd.DataFrame({

        "trip_id": [
            f"T{i:06d}"
            for i in range(1, num_trips + 1)
        ],

        "destination": np.random.choice(
            destinations,
            size=num_trips
        ),

        "trip_type": np.random.choice(
            trip_types,
            size=num_trips
        ),

        "departure_date": departure_dates,

        "return_date": return_dates,

        "capacity": np.random.choice(
            [
                500,
                1000,
                1500,
                2000,
                2500
            ],
            size=num_trips
        ),

        "base_price": np.round(
            np.random.uniform(
                500,
                5000,
                size=num_trips
            ),
            2
        )
    })

    return trips


# ============================================================
# BOOKINGS
# ============================================================

def generate_bookings(
    customers,
    trips,
    num_bookings=8000
):

    np.random.seed(SEED)

    selected_customers = np.random.choice(
        customers["customer_id"],
        size=num_bookings
    )

    selected_trips = np.random.choice(
        trips["trip_id"],
        size=num_bookings
    )

    selected_trip_dates = (
        trips
        .set_index("trip_id")
        .loc[
            selected_trips,
            "departure_date"
        ]
        .reset_index(drop=True)
    )

    booking_lead_days = np.random.randint(
        7,
        181,
        size=num_bookings
    )

    booking_dates = (
        selected_trip_dates
        - pd.to_timedelta(
            booking_lead_days,
            unit="D"
        )
    )

    booking_amounts = np.round(
        np.random.uniform(
            500,
            5000,
            size=num_bookings
        ),
        2
    )

    booking_statuses = np.random.choice(
        [
            "Confirmed",
            "Cancelled",
            "Pending"
        ],
        size=num_bookings,
        p=[
            0.75,
            0.15,
            0.10
        ]
    )

    bookings = pd.DataFrame({

        "booking_id": [
            f"B{i:06d}"
            for i in range(1, num_bookings + 1)
        ],

        "customer_id": selected_customers,

        "trip_id": selected_trips,

        "booking_date": booking_dates,

        "booking_amount": booking_amounts,

        "booking_status": booking_statuses
    })

    return bookings


# ============================================================
# PAYMENTS
# ============================================================

def generate_payments(bookings):

    np.random.seed(SEED)

    payment_methods = [
        "Credit Card",
        "Debit Card",
        "Apple Pay",
        "Bank Transfer",
        "Digital Wallet"
    ]

    failure_reasons = [
        "Card Declined",
        "Insufficient Funds",
        "Payment Timeout",
        "Technical Error",
        "Fraud Check"
    ]

    payment_records = []

    payment_id = 1

    for _, booking in bookings.iterrows():

        # ----------------------------------------------------
        # Decide how many attempts this booking needs.
        # ----------------------------------------------------

        first_attempt_success = (
            np.random.random() < 0.75
        )

        if first_attempt_success:

            num_attempts = 1

        else:

            num_attempts = np.random.choice(
                [2, 3],
                p=[
                    0.70,
                    0.30
                ]
            )

        # ----------------------------------------------------
        # First payment attempt
        # ----------------------------------------------------

        current_payment_time = (
            pd.Timestamp(
                booking["booking_date"]
            )
            + pd.Timedelta(
                minutes=int(
                    np.random.randint(
                        5,
                        61
                    )
                )
            )
        )

        # ----------------------------------------------------
        # Generate payment attempts sequentially
        # ----------------------------------------------------

        for attempt_number in range(
            1,
            num_attempts + 1
        ):

            # -----------------------------------------------
            # Determine payment status
            # -----------------------------------------------

            if (
                attempt_number == num_attempts
                and num_attempts > 1
            ):

                payment_status = "Success"
                failure_reason = None

            elif (
                attempt_number == 1
                and first_attempt_success
            ):

                payment_status = "Success"
                failure_reason = None

            else:

                payment_status = "Failed"

                failure_reason = np.random.choice(
                    failure_reasons
                )

            # -----------------------------------------------
            # Create payment record
            # -----------------------------------------------

            payment_records.append({

                "payment_id":
                    f"P{payment_id:06d}",

                "booking_id":
                    booking["booking_id"],

                "attempt_number":
                    attempt_number,

                "payment_method":
                    np.random.choice(
                        payment_methods
                    ),

                "payment_amount":
                    booking["booking_amount"],

                "payment_status":
                    payment_status,

                "payment_timestamp":
                    current_payment_time,

                "failure_reason":
                    failure_reason
            })

            payment_id += 1

            # -----------------------------------------------
            # Generate next attempt time
            # -----------------------------------------------

            if attempt_number < num_attempts:

                failure_time = (
                    current_payment_time
                    + pd.Timedelta(
                        seconds=int(
                            np.random.randint(
                                10,
                                60
                            )
                        )
                    )
                )

                retry_delay = pd.Timedelta(
                    minutes=int(
                        np.random.randint(
                            1,
                            15
                        )
                    )
                )

                current_payment_time = (
                    failure_time
                    + retry_delay
                )

    return pd.DataFrame(
        payment_records
    )


# ============================================================
# EVENTS
# ============================================================

def generate_events(
    bookings,
    payments
):

    event_records = []

    event_id = 1

    payments_by_booking = (
        payments
        .sort_values(
            [
                "booking_id",
                "attempt_number"
            ]
        )
        .groupby("booking_id")
    )

    for _, booking in bookings.iterrows():

        booking_id = booking["booking_id"]

        customer_id = booking["customer_id"]

        booking_date = pd.Timestamp(
            booking["booking_date"]
        )

        # ----------------------------------------------------
        # CUSTOMER JOURNEY BEFORE BOOKING
        # ----------------------------------------------------

        # Search happens before booking starts.
        search_time = (
            booking_date
            - pd.Timedelta(
                minutes=int(
                    np.random.randint(
                        16,
                        40
                    )
                )
            )
        )

        # View trip happens after search.
        view_trip_time = (
            search_time
            + pd.Timedelta(
                minutes=int(
                    np.random.randint(
                        5,
                        12
                    )
                )
            )
        )

        # Booking starts shortly before booking is created.
        booking_started_time = (
            booking_date
            - pd.Timedelta(
                minutes=int(
                    np.random.randint(
                        1,
                        6
                    )
                )
            )
        )

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        event_records.append({

            "event_id":
                f"E{event_id:07d}",

            "customer_id":
                customer_id,

            "booking_id":
                booking_id,

            "event_type":
                "SEARCH",

            "event_timestamp":
                search_time
        })

        event_id += 1

        # ----------------------------------------------------
        # VIEW TRIP
        # ----------------------------------------------------

        event_records.append({

            "event_id":
                f"E{event_id:07d}",

            "customer_id":
                customer_id,

            "booking_id":
                booking_id,

            "event_type":
                "VIEW_TRIP",

            "event_timestamp":
                view_trip_time
        })

        event_id += 1

        # ----------------------------------------------------
        # BOOKING STARTED
        # ----------------------------------------------------

        event_records.append({

            "event_id":
                f"E{event_id:07d}",

            "customer_id":
                customer_id,

            "booking_id":
                booking_id,

            "event_type":
                "BOOKING_STARTED",

            "event_timestamp":
                booking_started_time
        })

        event_id += 1

        # ----------------------------------------------------
        # BOOKING CREATED
        # ----------------------------------------------------

        event_records.append({

            "event_id":
                f"E{event_id:07d}",

            "customer_id":
                customer_id,

            "booking_id":
                booking_id,

            "event_type":
                "BOOKING_CREATED",

            "event_timestamp":
                booking_date
        })

        event_id += 1

        # ----------------------------------------------------
        # PAYMENT EVENTS
        # ----------------------------------------------------

        booking_payments = (
            payments_by_booking
            .get_group(
                booking_id
            )
            .sort_values(
                "attempt_number"
            )
            .reset_index(drop=True)
        )

        for payment_index, payment in booking_payments.iterrows():

            payment_time = pd.Timestamp(
                payment["payment_timestamp"]
            )

            # ------------------------------------------------
            # PAYMENT STARTED
            # ------------------------------------------------

            event_records.append({

                "event_id":
                    f"E{event_id:07d}",

                "customer_id":
                    customer_id,

                "booking_id":
                    booking_id,

                "event_type":
                    "PAYMENT_STARTED",

                "event_timestamp":
                    payment_time
            })

            event_id += 1

            # ------------------------------------------------
            # FAILED PAYMENT
            # ------------------------------------------------

            if payment["payment_status"] == "Failed":

                failed_time = (
                    payment_time
                    + pd.Timedelta(
                        seconds=int(
                            np.random.randint(
                                10,
                                60
                            )
                        )
                    )
                )

                event_records.append({

                    "event_id":
                        f"E{event_id:07d}",

                    "customer_id":
                        customer_id,

                    "booking_id":
                        booking_id,

                    "event_type":
                        "PAYMENT_FAILED",

                    "event_timestamp":
                        failed_time
                })

                event_id += 1

                # ------------------------------------------------
                # RETRY
                #
                # We explicitly place retry between:
                #
                # FAILED
                #    ↓
                # RETRY
                #    ↓
                # NEXT PAYMENT STARTED
                # ------------------------------------------------

                if (
                    payment_index
                    < len(booking_payments) - 1
                ):

                    next_payment_time = pd.Timestamp(
                        booking_payments.iloc[
                            payment_index + 1
                        ]["payment_timestamp"]
                    )

                    available_seconds = int(
                        (
                            next_payment_time
                            - failed_time
                        ).total_seconds()
                    )

                    if available_seconds > 2:

                        retry_seconds = np.random.randint(
                            1,
                            available_seconds
                        )

                        retry_time = (
                            failed_time
                            + pd.Timedelta(
                                seconds=int(
                                    retry_seconds
                                )
                            )
                        )

                    else:

                        retry_time = (
                            next_payment_time
                            - pd.Timedelta(
                                seconds=1
                            )
                        )

                    event_records.append({

                        "event_id":
                            f"E{event_id:07d}",

                        "customer_id":
                            customer_id,

                        "booking_id":
                            booking_id,

                        "event_type":
                            "PAYMENT_RETRY",

                        "event_timestamp":
                            retry_time
                    })

                    event_id += 1

            # ------------------------------------------------
            # SUCCESSFUL PAYMENT
            # ------------------------------------------------

            else:

                completed_time = (
                    payment_time
                    + pd.Timedelta(
                        seconds=int(
                            np.random.randint(
                                10,
                                60
                            )
                        )
                    )
                )

                event_records.append({

                    "event_id":
                        f"E{event_id:07d}",

                    "customer_id":
                        customer_id,

                    "booking_id":
                        booking_id,

                    "event_type":
                        "PAYMENT_COMPLETED",

                    "event_timestamp":
                        completed_time
                })

                event_id += 1

                # ------------------------------------------------
                # BOOKING CONFIRMED
                # ------------------------------------------------

                if (
                    booking["booking_status"]
                    == "Confirmed"
                ):

                    confirmed_time = (
                        completed_time
                        + pd.Timedelta(
                            minutes=int(
                                np.random.randint(
                                    1,
                                    10
                                )
                            )
                        )
                    )

                    event_records.append({

                        "event_id":
                            f"E{event_id:07d}",

                        "customer_id":
                            customer_id,

                        "booking_id":
                            booking_id,

                        "event_type":
                            "BOOKING_CONFIRMED",

                        "event_timestamp":
                            confirmed_time
                    })

                    event_id += 1

    return pd.DataFrame(
        event_records
    )


# ============================================================
# DATA QUALITY VALIDATION
# ============================================================

def validate_data(
    customers,
    trips,
    bookings,
    payments,
    events
):

    print("\n" + "=" * 60)
    print("DATA QUALITY VALIDATION")
    print("=" * 60)

    validation_passed = True

    # ========================================================
    # CUSTOMERS
    # ========================================================

    duplicate_customer_ids = (
        customers["customer_id"]
        .duplicated()
        .sum()
    )

    missing_customer_ids = (
        customers["customer_id"]
        .isna()
        .sum()
    )

    print("\nCUSTOMERS")

    print(
        "Duplicate customer IDs:",
        duplicate_customer_ids
    )

    print(
        "Missing customer IDs:",
        missing_customer_ids
    )

    if (
        duplicate_customer_ids > 0
        or missing_customer_ids > 0
    ):
        validation_passed = False

    # ========================================================
    # TRIPS
    # ========================================================

    duplicate_trip_ids = (
        trips["trip_id"]
        .duplicated()
        .sum()
    )

    missing_trip_ids = (
        trips["trip_id"]
        .isna()
        .sum()
    )

    invalid_trip_dates = (
        trips["departure_date"]
        >= trips["return_date"]
    ).sum()

    print("\nTRIPS")

    print(
        "Duplicate trip IDs:",
        duplicate_trip_ids
    )

    print(
        "Missing trip IDs:",
        missing_trip_ids
    )

    print(
        "Invalid trip date ranges:",
        invalid_trip_dates
    )

    if (
        duplicate_trip_ids > 0
        or missing_trip_ids > 0
        or invalid_trip_dates > 0
    ):
        validation_passed = False

    # ========================================================
    # BOOKINGS
    # ========================================================

    duplicate_booking_ids = (
        bookings["booking_id"]
        .duplicated()
        .sum()
    )

    missing_booking_ids = (
        bookings["booking_id"]
        .isna()
        .sum()
    )

    invalid_customer_references = (
        ~bookings["customer_id"].isin(
            customers["customer_id"]
        )
    ).sum()

    invalid_trip_references = (
        ~bookings["trip_id"].isin(
            trips["trip_id"]
        )
    ).sum()

    bookings_with_trips = bookings.merge(
        trips[
            [
                "trip_id",
                "departure_date"
            ]
        ],
        on="trip_id",
        how="left"
    )

    invalid_booking_dates = (
        bookings_with_trips["booking_date"]
        >= bookings_with_trips["departure_date"]
    ).sum()

    print("\nBOOKINGS")

    print(
        "Duplicate booking IDs:",
        duplicate_booking_ids
    )

    print(
        "Missing booking IDs:",
        missing_booking_ids
    )

    print(
        "Invalid customer references:",
        invalid_customer_references
    )

    print(
        "Invalid trip references:",
        invalid_trip_references
    )

    print(
        "Invalid booking dates:",
        invalid_booking_dates
    )

    if (
        duplicate_booking_ids > 0
        or missing_booking_ids > 0
        or invalid_customer_references > 0
        or invalid_trip_references > 0
        or invalid_booking_dates > 0
    ):
        validation_passed = False

    # ========================================================
    # PAYMENTS
    # ========================================================

    duplicate_payment_ids = (
        payments["payment_id"]
        .duplicated()
        .sum()
    )

    missing_payment_ids = (
        payments["payment_id"]
        .isna()
        .sum()
    )

    invalid_payment_bookings = (
        ~payments["booking_id"].isin(
            bookings["booking_id"]
        )
    ).sum()

    payments_with_bookings = payments.merge(
        bookings[
            [
                "booking_id",
                "booking_date"
            ]
        ],
        on="booking_id",
        how="left"
    )

    invalid_payment_timestamps = (
        payments_with_bookings["payment_timestamp"]
        < payments_with_bookings["booking_date"]
    ).sum()

    failed_without_reason = (
        (
            payments["payment_status"]
            == "Failed"
        )
        &
        payments["failure_reason"].isna()
    ).sum()

    success_with_reason = (
        (
            payments["payment_status"]
            == "Success"
        )
        &
        payments["failure_reason"].notna()
    ).sum()

    successful_payments_per_booking = (
        payments[
            payments["payment_status"]
            == "Success"
        ]
        .groupby("booking_id")
        .size()
    )

    bookings_with_multiple_successes = (
        successful_payments_per_booking
        > 1
    ).sum()

    # --------------------------------------------------------
    # Payment attempt ordering
    # --------------------------------------------------------

    invalid_attempt_sequences = 0

    for booking_id, group in payments.groupby(
        "booking_id"
    ):

        ordered = group.sort_values(
            "attempt_number"
        )

        timestamps = pd.to_datetime(
            ordered["payment_timestamp"]
        ).reset_index(drop=True)

        if not timestamps.is_monotonic_increasing:

            invalid_attempt_sequences += 1

    print("\nPAYMENTS")

    print(
        "Total payment attempts:",
        len(payments)
    )

    print(
        "Duplicate payment IDs:",
        duplicate_payment_ids
    )

    print(
        "Missing payment IDs:",
        missing_payment_ids
    )

    print(
        "Invalid booking references:",
        invalid_payment_bookings
    )

    print(
        "Invalid payment timestamps:",
        invalid_payment_timestamps
    )

    print(
        "Failed payments without failure reason:",
        failed_without_reason
    )

    print(
        "Successful payments with failure reason:",
        success_with_reason
    )

    print(
        "Bookings with multiple successful payments:",
        bookings_with_multiple_successes
    )

    print(
        "Invalid payment attempt sequences:",
        invalid_attempt_sequences
    )

    if (
        duplicate_payment_ids > 0
        or missing_payment_ids > 0
        or invalid_payment_bookings > 0
        or invalid_payment_timestamps > 0
        or failed_without_reason > 0
        or success_with_reason > 0
        or bookings_with_multiple_successes > 0
        or invalid_attempt_sequences > 0
    ):
        validation_passed = False

    # ========================================================
    # EVENTS
    # ========================================================

    duplicate_event_ids = (
        events["event_id"]
        .duplicated()
        .sum()
    )

    missing_event_ids = (
        events["event_id"]
        .isna()
        .sum()
    )

    invalid_event_customers = (
        ~events["customer_id"].isin(
            customers["customer_id"]
        )
    ).sum()

    invalid_event_bookings = (
        ~events["booking_id"].isin(
            bookings["booking_id"]
        )
    ).sum()

    event_time_nulls = (
        events["event_timestamp"]
        .isna()
        .sum()
    )

    # --------------------------------------------------------
    # Event ordering validation
    # --------------------------------------------------------

    invalid_event_sequences = 0

    for booking_id, group in events.groupby(
        "booking_id"
    ):

        timestamps = pd.to_datetime(
            group["event_timestamp"]
        )

        if not timestamps.is_monotonic_increasing:

            invalid_event_sequences += 1

    print("\nEVENTS")

    print(
        "Total events:",
        len(events)
    )

    print(
        "Duplicate event IDs:",
        duplicate_event_ids
    )

    print(
        "Missing event IDs:",
        missing_event_ids
    )

    print(
        "Invalid customer references:",
        invalid_event_customers
    )

    print(
        "Invalid booking references:",
        invalid_event_bookings
    )

    print(
        "Missing event timestamps:",
        event_time_nulls
    )

    print(
        "Invalid event sequences:",
        invalid_event_sequences
    )

    if (
        duplicate_event_ids > 0
        or missing_event_ids > 0
        or invalid_event_customers > 0
        or invalid_event_bookings > 0
        or event_time_nulls > 0
        or invalid_event_sequences > 0
    ):
        validation_passed = False

    # ========================================================
    # FINAL STATUS
    # ========================================================

    print("\n" + "-" * 60)

    if validation_passed:

        print(
            "DATA QUALITY STATUS: PASSED"
        )

    else:

        print(
            "DATA QUALITY STATUS: FAILED"
        )

    print("-" * 60)

    return validation_passed


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "Generating Journey Forensics dataset..."
    )

    # --------------------------------------------------------
    # Generate source datasets
    # --------------------------------------------------------

    customers = generate_customers()

    trips = generate_trips()

    bookings = generate_bookings(
        customers,
        trips
    )

    payments = generate_payments(
        bookings
    )

    events = generate_events(
        bookings,
        payments
    )

    # --------------------------------------------------------
    # Dataset summary
    # --------------------------------------------------------

    print("\nDATASET SUMMARY")
    print("-" * 60)

    print(
        "Customers:",
        len(customers)
    )

    print(
        "Trips:",
        len(trips)
    )

    print(
        "Bookings:",
        len(bookings)
    )

    print(
        "Payment attempts:",
        len(payments)
    )

    print(
        "Events:",
        len(events)
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validation_passed = validate_data(
        customers,
        trips,
        bookings,
        payments,
        events
    )

    if not validation_passed:

        raise ValueError(
            "Data validation failed. "
            "Fix the data-generation logic before "
            "continuing."
        )

    # --------------------------------------------------------
    # Save datasets
    # --------------------------------------------------------

    customers.to_csv(
        "data/raw/customers.csv",
        index=False
    )

    trips.to_csv(
        "data/raw/trips.csv",
        index=False
    )

    bookings.to_csv(
        "data/raw/bookings.csv",
        index=False
    )

    payments.to_csv(
        "data/raw/payments.csv",
        index=False
    )

    events.to_csv(
        "data/raw/events.csv",
        index=False
    )

    print(
        "\nDatasets successfully written to data/raw/"
    )