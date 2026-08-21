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


if __name__ == "__main__":
    customers = generate_customers()

    print(customers.head())
    print("\nTotal customers:", len(customers))
    print("\nCountry distribution:")
    print(customers["country"].value_counts())

    print("\nSegment distribution:")
    print(customers["customer_segment"].value_counts())

    customers.to_csv("data/raw/customers.csv", index=False)