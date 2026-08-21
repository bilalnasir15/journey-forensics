import pandas as pd


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

customers = pd.read_csv(
    "data/raw/customers.csv"
)

bookings = pd.read_csv(
    "data/raw/bookings.csv"
)

payments = pd.read_csv(
    "data/raw/payments.csv"
)

events = pd.read_csv(
    "data/raw/events.csv"
)


# --------------------------------------------------
# FIND THE MOST PROBLEMATIC BOOKING
# --------------------------------------------------

failed_payment_counts = (
    payments[
        payments["payment_status"] == "Failed"
    ]
    .groupby("booking_id")
    .size()
    .sort_values(
        ascending=False
    )
)

if failed_payment_counts.empty:
    raise ValueError(
        "No failed payments found."
    )

booking_id = failed_payment_counts.index[0]

failed_payment_count = failed_payment_counts.iloc[0]


# --------------------------------------------------
# FIND CUSTOMER + BOOKING
# --------------------------------------------------

booking = bookings[
    bookings["booking_id"] == booking_id
].iloc[0]

customer = customers[
    customers["customer_id"] == booking["customer_id"]
].iloc[0]


# --------------------------------------------------
# DISPLAY CUSTOMER
# --------------------------------------------------

print("\n" + "=" * 60)
print("CUSTOMER")
print("=" * 60)

print(
    f"Customer ID: {customer['customer_id']}"
)

print(
    f"Name: {customer['first_name']} "
    f"{customer['last_name']}"
)

print(
    f"Country: {customer['country']}"
)

print(
    f"Segment: {customer['customer_segment']}"
)


# --------------------------------------------------
# DISPLAY BOOKING
# --------------------------------------------------

print("\n" + "=" * 60)
print("BOOKING")
print("=" * 60)

print(
    f"Booking ID: {booking['booking_id']}"
)

print(
    f"Trip ID: {booking['trip_id']}"
)

print(
    f"Booking Date: {booking['booking_date']}"
)

print(
    f"Booking Amount: {booking['booking_amount']}"
)

print(
    f"Booking Status: {booking['booking_status']}"
)


# --------------------------------------------------
# DISPLAY PAYMENT HISTORY
# --------------------------------------------------

booking_payments = payments[
    payments["booking_id"] == booking_id
].copy()

booking_payments = booking_payments.sort_values(
    "attempt_number"
)

print("\n" + "=" * 60)
print("PAYMENT HISTORY")
print("=" * 60)

print(
    booking_payments[
        [
            "payment_id",
            "attempt_number",
            "payment_method",
            "payment_amount",
            "payment_status",
            "payment_timestamp",
            "failure_reason"
        ]
    ].to_string(index=False)
)


# --------------------------------------------------
# DISPLAY EVENT JOURNEY
# --------------------------------------------------

booking_events = events[
    events["booking_id"] == booking_id
].copy()

booking_events["event_timestamp"] = pd.to_datetime(
    booking_events["event_timestamp"]
)

booking_events = booking_events.sort_values(
    "event_timestamp"
)

print("\n" + "=" * 60)
print("CUSTOMER JOURNEY")
print("=" * 60)

print(
    booking_events[
        [
            "event_timestamp",
            "event_type"
        ]
    ].to_string(index=False)
)


# --------------------------------------------------
# JOURNEY SUMMARY
# --------------------------------------------------

total_payment_attempts = len(
    booking_payments
)

failed_payments = (
    booking_payments[
        booking_payments["payment_status"] == "Failed"
    ]
)

successful_payments = (
    booking_payments[
        booking_payments["payment_status"] == "Success"
    ]
)

print("\n" + "=" * 60)
print("JOURNEY FORENSICS SUMMARY")
print("=" * 60)

print(
    f"Customer: {customer['customer_id']}"
)

print(
    f"Booking: {booking_id}"
)

print(
    f"Booking status: {booking['booking_status']}"
)

print(
    f"Payment attempts: {total_payment_attempts}"
)

print(
    f"Failed payments: {len(failed_payments)}"
)

print(
    f"Successful payments: {len(successful_payments)}"
)

print(
    f"Total events: {len(booking_events)}"
)

print(
    f"Most failure-heavy booking: "
    f"{failed_payment_count} failed payment(s)"
)