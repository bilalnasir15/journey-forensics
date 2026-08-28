import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

FEATURE_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "customer_journey_features.csv"
)

CUSTOMER_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "customer_forensics_features.csv"
)

CUSTOMER_ID = "C000921"


journeys = pd.read_csv(FEATURE_FILE)

customers = pd.read_csv(CUSTOMER_FILE)


# ============================================================
# CUSTOMER JOURNEYS
# ============================================================

customer_journeys = journeys[
    journeys["customer_id"] == CUSTOMER_ID
].copy()


print("=" * 60)
print("CUSTOMER JOURNEY HISTORY")
print("=" * 60)

print(
    customer_journeys[
        [
            "customer_id",
            "booking_id",
            "booking_status",
            "payment_attempts",
            "failed_payments",
            "retry_count",
            "friction_score",
            "risk_level",
            "anomaly_count",
            "anomaly_summary"
        ]
    ].to_string(index=False)
)


# ============================================================
# MANUAL CUSTOMER METRICS
# ============================================================

total_bookings = len(customer_journeys)

total_failed = (
    customer_journeys[
        "failed_payments"
    ].sum()
)

total_retries = (
    customer_journeys[
        "retry_count"
    ].sum()
)

average_friction = (
    customer_journeys[
        "friction_score"
    ].mean()
)

maximum_friction = (
    customer_journeys[
        "friction_score"
    ].max()
)

total_anomalies = (
    customer_journeys[
        "anomaly_count"
    ].sum()
)

critical_journeys = (
    customer_journeys[
        "risk_level"
    ]
    .eq("CRITICAL")
    .sum()
)

high_risk_journeys = (
    customer_journeys[
        "risk_level"
    ]
    .eq("HIGH")
    .sum()
)


print("\n")
print("=" * 60)
print("MANUAL CUSTOMER CALCULATION")
print("=" * 60)

print(
    "Total bookings:",
    total_bookings
)

print(
    "Total failed payments:",
    total_failed
)

print(
    "Total retries:",
    total_retries
)

print(
    "Average friction:",
    round(
        average_friction,
        2
    )
)

print(
    "Maximum friction:",
    maximum_friction
)

print(
    "Total anomalies:",
    total_anomalies
)

print(
    "Critical journeys:",
    critical_journeys
)

print(
    "High-risk journeys:",
    high_risk_journeys
)


# ============================================================
# DERIVED CUSTOMER PROFILE
# ============================================================

customer = customers[
    customers["customer_id"]
    == CUSTOMER_ID
].iloc[0]


print("\n")
print("=" * 60)
print("DERIVED CUSTOMER PROFILE")
print("=" * 60)

print(
    "Customer risk score:",
    customer["customer_risk_score"]
)

print(
    "Customer risk level:",
    customer["customer_risk_level"]
)

print(
    "Behavior profile:",
    customer["behavior_profile"]
)


# ============================================================
# VALIDATION
# ============================================================

print("\n")
print("=" * 60)
print("VALIDATION")
print("=" * 60)

checks = {

    "Bookings":
        total_bookings
        == customer["total_bookings"],

    "Failed payments":
        total_failed
        == customer["total_failed_payments"],

    "Retries":
        total_retries
        == customer["total_retries"],

    "Average friction":
        round(
            average_friction,
            2
        )
        == round(
            customer["average_friction_score"],
            2
        ),

    "Maximum friction":
        maximum_friction
        == customer["maximum_friction_score"],

    "Anomalies":
        total_anomalies
        == customer["total_anomalies"],

    "Critical journeys":
        critical_journeys
        == customer["critical_journeys"],

    "High-risk journeys":
        high_risk_journeys
        == customer["high_risk_journeys"]
}


for name, result in checks.items():

    print(
        f"{name}:",
        "PASS" if result else "FAIL"
    )


print(
    "\nOverall validation:",
    "PASSED"
    if all(checks.values())
    else "FAILED"
)