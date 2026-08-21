import pandas as pd
import numpy as np
from faker import Faker


SEED = 42

fake = Faker()
fake.seed_instance(SEED)


def generate_customers(num_customers=5000):
    np.random.seed(SEED)

    customers = pd.DataFrame({
        "customer_id": [
            f"C{i:06d}" for i in range(1, num_customers + 1)
        ],

        "first_name": [
            fake.first_name() for _ in range(num_customers)
        ],

        "last_name": [
            fake.last_name() for _ in range(num_customers)
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
            p=[0.30, 0.20, 0.15, 0.10, 0.10, 0.15]
        ),

        "signup_date": pd.to_datetime(
            np.random.choice(
                pd.date_range(
                    start="2023-01-01",
                    end="2026-06-30"
                ),
                size=num_customers
            )
        ),

        "date_of_birth": pd.to_datetime(
            np.random.choice(
                pd.date_range(
                    start="1960-01-01",
                    end="2005-12-31"
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
            p=[0.70, 0.25, 0.05]
        )
    })

    return customers


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
                start="2026-01-01",
                end="2026-12-31"
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
            f"T{i:06d}" for i in range(1, num_trips + 1)
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
            [500, 1000, 1500, 2000, 2500],
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
        p=[0.75, 0.15, 0.10]
    )

    bookings = pd.DataFrame({
        "booking_id": [
            f"B{i:06d}" for i in range(1, num_bookings + 1)
        ],

        "customer_id": selected_customers,

        "trip_id": selected_trips,

        "booking_date": booking_dates,

        "booking_amount": booking_amounts,

        "booking_status": booking_statuses
    })

    return bookings


def validate_data(
    customers,
    trips,
    bookings
):
    print("\n" + "=" * 50)
    print("DATA QUALITY VALIDATION")
    print("=" * 50)

    validation_passed = True

    # --------------------------------------------------
    # CUSTOMER VALIDATION
    # --------------------------------------------------

    duplicate_customer_ids = (
        customers["customer_id"].duplicated().sum()
    )

    missing_customer_ids = (
        customers["customer_id"].isna().sum()
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

    if duplicate_customer_ids > 0 or missing_customer_ids > 0:
        validation_passed = False

    # --------------------------------------------------
    # TRIP VALIDATION
    # --------------------------------------------------

    duplicate_trip_ids = (
        trips["trip_id"].duplicated().sum()
    )

    missing_trip_ids = (
        trips["trip_id"].isna().sum()
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

    # --------------------------------------------------
    # BOOKING PRIMARY KEY VALIDATION
    # --------------------------------------------------

    duplicate_booking_ids = (
        bookings["booking_id"].duplicated().sum()
    )

    missing_booking_ids = (
        bookings["booking_id"].isna().sum()
    )

    print("\nBOOKINGS")

    print(
        "Duplicate booking IDs:",
        duplicate_booking_ids
    )

    print(
        "Missing booking IDs:",
        missing_booking_ids
    )

    if (
        duplicate_booking_ids > 0
        or missing_booking_ids > 0
    ):
        validation_passed = False

    # --------------------------------------------------
    # FOREIGN KEY VALIDATION
    # --------------------------------------------------

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

    print(
        "Invalid customer references:",
        invalid_customer_references
    )

    print(
        "Invalid trip references:",
        invalid_trip_references
    )

    if (
        invalid_customer_references > 0
        or invalid_trip_references > 0
    ):
        validation_passed = False

    # --------------------------------------------------
    # BOOKING DATE VALIDATION
    # --------------------------------------------------

    trip_dates = trips[
        [
            "trip_id",
            "departure_date"
        ]
    ]

    bookings_with_trips = bookings.merge(
        trip_dates,
        on="trip_id",
        how="left"
    )

    invalid_booking_dates = (
        bookings_with_trips["booking_date"]
        >= bookings_with_trips["departure_date"]
    ).sum()

    print(
        "Invalid booking dates:",
        invalid_booking_dates
    )

    if invalid_booking_dates > 0:
        validation_passed = False

    # --------------------------------------------------
    # NULL VALIDATION
    # --------------------------------------------------

    booking_nulls = (
        bookings[
            [
                "booking_id",
                "customer_id",
                "trip_id",
                "booking_date"
            ]
        ]
        .isna()
        .sum()
        .sum()
    )

    print(
        "Critical booking NULL values:",
        booking_nulls
    )

    if booking_nulls > 0:
        validation_passed = False

    # --------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------

    print("\n" + "-" * 50)

    if validation_passed:
        print("DATA QUALITY STATUS: PASSED")
    else:
        print("DATA QUALITY STATUS: FAILED")

    print("-" * 50)

    return validation_passed


if __name__ == "__main__":

    print("Generating Journey Forensics dataset...")

    customers = generate_customers()

    trips = generate_trips()

    bookings = generate_bookings(
        customers,
        trips
    )

    print("\nDATASET SUMMARY")
    print("-" * 50)

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

    validation_passed = validate_data(
        customers,
        trips,
        bookings
    )

    if not validation_passed:
        raise ValueError(
            "Data validation failed. "
            "Fix the data-generation logic before "
            "continuing."
        )

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

    print("\nDatasets successfully written to data/raw/")