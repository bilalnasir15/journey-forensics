import pandas as pd
import numpy as np
from faker import Faker


fake = Faker()


def generate_customers(num_customers=5000):
    np.random.seed(42)

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
    np.random.seed(42)

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
        + pd.to_timedelta(trip_durations, unit="D")
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


def generate_bookings(customers, trips, num_bookings=8000):
    np.random.seed(42)

    selected_customers = np.random.choice(
        customers["customer_id"],
        size=num_bookings
    )

    selected_trips = np.random.choice(
        trips["trip_id"],
        size=num_bookings
    )

    selected_trip_dates = trips.set_index(
        "trip_id"
    ).loc[
        selected_trips,
        "departure_date"
    ].reset_index(drop=True)

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


def validate_bookings(bookings, customers, trips):
    print("\nVALIDATING BOOKINGS...")

    invalid_customers = ~bookings["customer_id"].isin(
        customers["customer_id"]
    )

    invalid_trips = ~bookings["trip_id"].isin(
        trips["trip_id"]
    )

    trip_dates = trips[
        ["trip_id", "departure_date"]
    ]

    bookings_with_trips = bookings.merge(
        trip_dates,
        on="trip_id",
        how="left"
    )

    invalid_booking_dates = (
        bookings_with_trips["booking_date"]
        >= bookings_with_trips["departure_date"]
    )

    print(
        "Invalid customer references:",
        invalid_customers.sum()
    )

    print(
        "Invalid trip references:",
        invalid_trips.sum()
    )

    print(
        "Invalid booking dates:",
        invalid_booking_dates.sum()
    )


if __name__ == "__main__":
    customers = generate_customers()
    trips = generate_trips()
    bookings = generate_bookings(
        customers,
        trips
    )

    print("CUSTOMERS")
    print(customers.head())

    print("\nTotal customers:", len(customers))

    print("\nTRIPS")
    print(trips.head())

    print("\nTotal trips:", len(trips))

    print("\nBOOKINGS")
    print(bookings.head())

    print("\nTotal bookings:", len(bookings))

    validate_bookings(
        bookings,
        customers,
        trips
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