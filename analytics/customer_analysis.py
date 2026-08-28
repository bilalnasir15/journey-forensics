import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

FEATURE_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "customer_journey_features.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "customer_forensics_features.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_features():

    print("=" * 60)
    print("LOADING JOURNEY FEATURES")
    print("=" * 60)

    df = pd.read_csv(
        FEATURE_FILE
    )

    print(
        f"Journey records: {len(df):,}"
    )

    print(
        f"Unique customers: "
        f"{df['customer_id'].nunique():,}"
    )

    print(
        f"Unique bookings: "
        f"{df['booking_id'].nunique():,}"
    )

    return df


# ============================================================
# CUSTOMER AGGREGATION
# ============================================================

def build_customer_features(df):

    print("\nBuilding customer-level features...")

    customer_features = (
        df
        .groupby(
            [
                "customer_id",
                "first_name",
                "last_name",
                "country",
                "customer_segment"
            ],
            as_index=False
        )
        .agg(

            # ------------------------------------------------
            # Booking behavior
            # ------------------------------------------------

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

            # ------------------------------------------------
            # Payment behavior
            # ------------------------------------------------

            total_payment_attempts=(
                "payment_attempts",
                "sum"
            ),

            total_failed_payments=(
                "failed_payments",
                "sum"
            ),

            total_successful_payments=(
                "successful_payments",
                "sum"
            ),

            total_retries=(
                "retry_count",
                "sum"
            ),

            # ------------------------------------------------
            # Journey behavior
            # ------------------------------------------------

            total_events=(
                "total_events",
                "sum"
            ),

            average_journey_duration=(
                "journey_duration_minutes",
                "mean"
            ),

            maximum_journey_duration=(
                "journey_duration_minutes",
                "max"
            ),

            # ------------------------------------------------
            # Forensics
            # ------------------------------------------------

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
            ),

            critical_journeys=(
                "risk_level",
                lambda x: (
                    x == "CRITICAL"
                ).sum()
            ),

            high_risk_journeys=(
                "risk_level",
                lambda x: (
                    x == "HIGH"
                ).sum()
            )
        )
    )

    return customer_features


# ============================================================
# CUSTOMER PAYMENT METRICS
# ============================================================

def calculate_payment_metrics(df):

    print("Calculating customer payment metrics...")

    payment_metrics = (
        df
        .groupby("customer_id")
        .agg(
            customer_payment_attempts=(
                "payment_attempts",
                "sum"
            ),

            customer_successful_payments=(
                "successful_payments",
                "sum"
            ),

            customer_failed_payments=(
                "failed_payments",
                "sum"
            )
        )
        .reset_index()
    )

    payment_metrics[
        "customer_payment_success_rate"
    ] = (
        payment_metrics[
            "customer_successful_payments"
        ]
        /
        payment_metrics[
            "customer_payment_attempts"
        ]
    ).fillna(0)

    return payment_metrics


# ============================================================
# CUSTOMER RISK SCORE
# ============================================================

def calculate_customer_risk(
    customer_features
):

    print("Calculating customer risk scores...")

    score = pd.Series(
        0.0,
        index=customer_features.index
    )

    # --------------------------------------------------------
    # Repeated payment failures
    # --------------------------------------------------------

    score += (
        customer_features[
            "total_failed_payments"
        ]
        * 5
    )

    # --------------------------------------------------------
    # Repeated retries
    # --------------------------------------------------------

    score += (
        customer_features[
            "total_retries"
        ]
        * 3
    )

    # --------------------------------------------------------
    # High-risk journeys
    # --------------------------------------------------------

    score += (
        customer_features[
            "high_risk_journeys"
        ]
        * 10
    )

    # --------------------------------------------------------
    # Critical journeys
    # --------------------------------------------------------

    score += (
        customer_features[
            "critical_journeys"
        ]
        * 20
    )

    # --------------------------------------------------------
    # Anomalies
    # --------------------------------------------------------

    score += (
        customer_features[
            "total_anomalies"
        ]
        * 5
    )

    customer_features[
        "customer_risk_score"
    ] = score.clip(
        upper=100
    )

    # --------------------------------------------------------
    # Risk level
    # --------------------------------------------------------

    customer_features[
        "customer_risk_level"
    ] = pd.cut(
        customer_features[
            "customer_risk_score"
        ],
        bins=[
            -1,
            24,
            49,
            74,
            100
        ],
        labels=[
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL"
        ]
    )

    return customer_features


# ============================================================
# CUSTOMER PROFILE
# ============================================================

def build_customer_profile(
    customer_features
):

    print("Building customer behavioral profiles...")

    def classify_customer(row):

        if (
            row["critical_journeys"] >= 2
            or row["customer_risk_score"] >= 75
        ):
            return "HIGH_RISK_CUSTOMER"

        if (
            row["high_risk_journeys"] >= 1
            or row["total_failed_payments"] >= 2
        ):
            return "FRICTION_PRONE_CUSTOMER"

        if (
            row["total_bookings"] >= 3
            and row["average_friction_score"] < 30
        ):
            return "LOYAL_LOW_FRICTION_CUSTOMER"

        return "NORMAL_CUSTOMER"

    customer_features[
        "behavior_profile"
    ] = customer_features.apply(
        classify_customer,
        axis=1
    )

    return customer_features


# ============================================================
# REPORT
# ============================================================

def print_customer_report(
    customer_features
):

    print("\n")
    print("=" * 60)
    print("CUSTOMER FORENSICS REPORT")
    print("=" * 60)

    print(
        "\nTotal customers:",
        f"{len(customer_features):,}"
    )

    print("\nCUSTOMER RISK DISTRIBUTION")
    print("-" * 40)

    print(
        customer_features[
            "customer_risk_level"
        ]
        .value_counts()
        .sort_index()
    )

    print("\nBEHAVIOR PROFILE DISTRIBUTION")
    print("-" * 40)

    print(
        customer_features[
            "behavior_profile"
        ]
        .value_counts()
    )

    print("\nTOP 10 CUSTOMER RISK")
    print("-" * 40)

    columns = [
        "customer_id",
        "first_name",
        "last_name",
        "total_bookings",
        "total_failed_payments",
        "total_retries",
        "average_friction_score",
        "maximum_friction_score",
        "total_anomalies",
        "customer_risk_score",
        "customer_risk_level",
        "behavior_profile"
    ]

    print(
        customer_features
        .sort_values(
            "customer_risk_score",
            ascending=False
        )
        [columns]
        .head(10)
        .to_string(index=False)
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "Building customer-level forensic intelligence..."
    )

    journey_features = load_features()

    customer_features = (
        build_customer_features(
            journey_features
        )
    )

    payment_metrics = (
        calculate_payment_metrics(
            journey_features
        )
    )

    customer_features = (
        customer_features.merge(
            payment_metrics,
            on="customer_id",
            how="left"
        )
    )

    customer_features = (
        calculate_customer_risk(
            customer_features
        )
    )

    customer_features = (
        build_customer_profile(
            customer_features
        )
    )

    # --------------------------------------------------------
    # Rounding
    # --------------------------------------------------------

    numeric_columns = [
        "total_booking_value",
        "average_booking_value",
        "average_journey_duration",
        "maximum_journey_duration",
        "average_friction_score",
        "maximum_friction_score",
        "customer_payment_success_rate",
        "customer_risk_score"
    ]

    for column in numeric_columns:

        if column in customer_features.columns:

            customer_features[column] = (
                customer_features[column]
                .round(2)
            )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    customer_features.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print_customer_report(
        customer_features
    )

    print("\n")
    print("=" * 60)
    print("SUCCESS")
    print("=" * 60)

    print(
        "\nCustomer feature dataset written to:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nCustomer-level features:",
        len(customer_features.columns)
    )