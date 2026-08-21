import pandas as pd


payments = pd.read_csv(
    "data/raw/payments.csv"
)


print("\nPAYMENT STATUS")
print("-" * 40)

print(
    payments["payment_status"]
    .value_counts()
)


print("\nFAILURE REASONS")
print("-" * 40)

failed_payments = payments[
    payments["payment_status"] == "Failed"
]

print(
    failed_payments["failure_reason"]
    .value_counts()
)


print("\nPAYMENT METHODS")
print("-" * 40)

print(
    payments["payment_method"]
    .value_counts()
)


print("\nPAYMENT ATTEMPTS PER BOOKING")
print("-" * 40)

attempts_per_booking = (
    payments
    .groupby("booking_id")
    .size()
)

print(
    attempts_per_booking
    .value_counts()
    .sort_index()
)


print("\nSUCCESS RATE")
print("-" * 40)

success_rate = (
    payments["payment_status"]
    .eq("Success")
    .mean()
    * 100
)

print(
    f"Payment success rate: {success_rate:.2f}%"
)