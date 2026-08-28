import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "customer_journey_features.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "customer_risk_model.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("=" * 60)
    print("CUSTOMER RISK MODEL")
    print("=" * 60)

    print("\nLoading journey feature dataset...")

    df = pd.read_csv(INPUT_FILE)

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
# PREPARE JOURNEY FLAGS
# ============================================================

def prepare_journey_flags(df):

    print("\nPreparing journey-level risk signals...")

    df = df.copy()

    # --------------------------------------------------------
    # Make sure numeric columns are numeric
    # --------------------------------------------------------

    numeric_columns = [
        "friction_score",
        "failed_payments",
        "retry_count",
        "anomaly_count",
        "payment_attempts",
        "successful_payments"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            ).fillna(0)

    # --------------------------------------------------------
    # Define a problematic journey
    # --------------------------------------------------------
    #
    # A booking is considered problematic if it has:
    #
    # 1. At least one anomaly
    # OR
    # 2. HIGH risk
    # OR
    # 3. CRITICAL risk
    # OR
    # 4. Friction score >= 50
    #
    # IMPORTANT:
    # This is a BOOKING-level signal.
    # It prevents multiple anomalies inside the same booking
    # from being incorrectly treated as multiple journeys.
    # --------------------------------------------------------

    df["problematic_journey"] = (
        (
            df["anomaly_count"] > 0
        )
        |
        (
            df["risk_level"].isin(
                [
                    "HIGH",
                    "CRITICAL"
                ]
            )
        )
        |
        (
            df["friction_score"] >= 50
        )
    )

    # --------------------------------------------------------
    # High-risk journey
    # --------------------------------------------------------

    df["high_risk_journey_flag"] = (
        df["risk_level"]
        .isin(
            [
                "HIGH",
                "CRITICAL"
            ]
        )
    )

    return df


# ============================================================
# CUSTOMER AGGREGATION
# ============================================================

def aggregate_customers(df):

    print("Aggregating customer journey history...")

    # --------------------------------------------------------
    # Standard customer metrics
    # --------------------------------------------------------

    customer_df = (
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

            total_bookings=(
                "booking_id",
                "nunique"
            ),

            total_booking_value=(
                "booking_amount",
                "sum"
            ),

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

            high_risk_journeys=(
                "high_risk_journey_flag",
                "sum"
            ),

            critical_journeys=(
                "risk_level",
                lambda x: (
                    x == "CRITICAL"
                ).sum()
            ),

            problematic_journeys=(
                "problematic_journey",
                "sum"
            )
        )
    )

    return customer_df


# ============================================================
# SEVERITY
# ============================================================

def calculate_severity(df):

    print("Calculating severity dimension...")

    # Severity represents the worst journey observed
    # for the customer.

    df["severity_score"] = (
        df["maximum_friction_score"]
        .clip(
            lower=0,
            upper=100
        )
        .round(2)
    )

    return df


# ============================================================
# FREQUENCY
# ============================================================

def calculate_frequency(df):

    print("Calculating frequency dimension...")

    # --------------------------------------------------------
    # Failure frequency
    # --------------------------------------------------------

    failure_rate = np.where(

        df["total_bookings"] > 0,

        (
            df["total_failed_payments"]
            /
            df["total_bookings"]
        ),

        0
    )

    # --------------------------------------------------------
    # Retry frequency
    # --------------------------------------------------------

    retry_rate = np.where(

        df["total_bookings"] > 0,

        (
            df["total_retries"]
            /
            df["total_bookings"]
        ),

        0
    )

    # --------------------------------------------------------
    # Anomaly frequency
    # --------------------------------------------------------

    anomaly_rate = np.where(

        df["total_bookings"] > 0,

        (
            df["total_anomalies"]
            /
            df["total_bookings"]
        ),

        0
    )

    # --------------------------------------------------------
    # Convert to normalized components
    # --------------------------------------------------------

    failure_component = np.minimum(
        failure_rate * 25,
        100
    )

    retry_component = np.minimum(
        retry_rate * 15,
        100
    )

    anomaly_component = np.minimum(
        anomaly_rate * 10,
        100
    )

    # --------------------------------------------------------
    # Frequency score
    #
    # Failed payments = 50%
    # Retries         = 25%
    # Anomalies       = 25%
    # --------------------------------------------------------

    frequency_score = (

        (
            failure_component
            * 0.50
        )

        +

        (
            retry_component
            * 0.25
        )

        +

        (
            anomaly_component
            * 0.25
        )
    )

    df["failure_rate_per_booking"] = (
        failure_rate.round(3)
    )

    df["retry_rate_per_booking"] = (
        retry_rate.round(3)
    )

    df["anomaly_rate_per_booking"] = (
        anomaly_rate.round(3)
    )

    df["frequency_score"] = (
        np.clip(
            frequency_score,
            0,
            100
        )
        .round(2)
    )

    return df


# ============================================================
# PERSISTENCE
# ============================================================

def calculate_persistence(df):

    print(
        "Calculating persistence dimension..."
    )

    # ========================================================
    # IMPORTANT RESEARCH LOGIC
    # ========================================================
    #
    # Persistence is NOT based on total anomalies.
    #
    # It is based on:
    #
    #     problematic bookings
    #     --------------------
    #        total bookings
    #
    # This means multiple anomalies inside ONE booking
    # do not automatically create high persistence.
    # ========================================================

    problematic_rate = np.where(

        df["total_bookings"] > 0,

        (
            df["problematic_journeys"]
            /
            df["total_bookings"]
        ),

        0
    )

    # --------------------------------------------------------
    # Problematic journey rate
    # --------------------------------------------------------

    df["problematic_journey_rate"] = (
        problematic_rate.round(3)
    )

    # --------------------------------------------------------
    # Persistence based on repeated journeys
    # --------------------------------------------------------
    #
    # 0 problematic bookings:
    #       0
    #
    # 1 problematic booking:
    #       limited evidence
    #
    # 2 problematic bookings:
    #       moderate evidence
    #
    # 3+ problematic bookings:
    #       strong repeated behavior
    #
    # The rate is also included so that:
    #
    # 3 problematic / 3 bookings
    #
    # is treated differently from:
    #
    # 3 problematic / 20 bookings
    # --------------------------------------------------------

    repetition_score = np.select(

        [
            df["problematic_journeys"] >= 4,

            df["problematic_journeys"] == 3,

            df["problematic_journeys"] == 2,

            df["problematic_journeys"] == 1
        ],

        [
            100,
            85,
            65,
            30
        ],

        default=0
    )

    rate_score = (
        problematic_rate
        * 100
    )

    rate_score = np.clip(
        rate_score,
        0,
        100
    )

    # --------------------------------------------------------
    # Combine:
    #
    # Repetition count = 60%
    # Problematic rate = 40%
    # --------------------------------------------------------

    persistence_score = (

        (
            repetition_score
            * 0.60
        )

        +

        (
            rate_score
            * 0.40
        )
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # A single problematic booking cannot produce a
    # high persistence score.
    # --------------------------------------------------------

    persistence_score = np.where(

        df["problematic_journeys"] <= 1,

        np.minimum(
            persistence_score,
            30
        ),

        persistence_score
    )

    df["persistence_score"] = (
        np.clip(
            persistence_score,
            0,
            100
        )
        .round(2)
    )

    return df


# ============================================================
# COMBINED RISK SCORE
# ============================================================

def calculate_combined_risk(df):

    print(
        "Calculating combined customer risk score..."
    )

    # ========================================================
    # RESEARCH MODEL
    # ========================================================
    #
    # Severity     = 40%
    # Frequency    = 30%
    # Persistence  = 30%
    #
    # These dimensions are intentionally separated so the
    # model is interpretable.
    # ========================================================

    df["customer_risk_score"] = (

        (
            df["severity_score"]
            * 0.40
        )

        +

        (
            df["frequency_score"]
            * 0.30
        )

        +

        (
            df["persistence_score"]
            * 0.30
        )
    )

    df["customer_risk_score"] = (
        df["customer_risk_score"]
        .clip(
            0,
            100
        )
        .round(2)
    )

    # ========================================================
    # RISK LEVEL
    # ========================================================

    df["customer_risk_level"] = pd.cut(

        df["customer_risk_score"],

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

    return df


# ============================================================
# BEHAVIOR PROFILE
# ============================================================

def classify_behavior(row):

    # --------------------------------------------------------
    # Critical customers
    # --------------------------------------------------------

    if (
        row["customer_risk_level"]
        == "CRITICAL"
    ):

        return "HIGH_RISK_CUSTOMER"

    # --------------------------------------------------------
    # High-risk customers
    # --------------------------------------------------------

    if (
        row["customer_risk_level"]
        == "HIGH"
    ):

        return "FRICTION_PRONE_CUSTOMER"

    # --------------------------------------------------------
    # Loyal low-friction customers
    # --------------------------------------------------------

    if (

        row["total_bookings"] >= 3

        and

        row["average_friction_score"] < 30

        and

        row["problematic_journeys"] <= 1

    ):

        return "LOYAL_LOW_FRICTION_CUSTOMER"

    # --------------------------------------------------------
    # Default
    # --------------------------------------------------------

    return "NORMAL_CUSTOMER"


def build_behavior_profiles(df):

    print(
        "Building customer behavior profiles..."
    )

    df["behavior_profile"] = (
        df.apply(
            classify_behavior,
            axis=1
        )
    )

    return df


# ============================================================
# RESEARCH SIGNALS
# ============================================================

def build_research_signal(df):

    print(
        "Building research interpretation signals..."
    )

    def interpretation(row):

        signals = []

        # ----------------------------------------------------
        # Severity
        # ----------------------------------------------------

        if (
            row["severity_score"] >= 70
        ):

            signals.append(
                "HIGH_SEVERITY"
            )

        # ----------------------------------------------------
        # Frequency
        # ----------------------------------------------------

        if (
            row["frequency_score"] >= 50
        ):

            signals.append(
                "HIGH_FREQUENCY"
            )

        # ----------------------------------------------------
        # Persistence
        # ----------------------------------------------------

        if (
            row["persistence_score"] >= 50
        ):

            signals.append(
                "PERSISTENT_BEHAVIOR"
            )

        # ----------------------------------------------------
        # Repeated payment failures
        # ----------------------------------------------------

        if (
            row["total_failed_payments"] >= 2
        ):

            signals.append(
                "REPEATED_PAYMENT_FAILURES"
            )

        # ----------------------------------------------------
        # Multiple problematic journeys
        # ----------------------------------------------------

        if (
            row["problematic_journeys"] >= 2
        ):

            signals.append(
                "MULTIPLE_PROBLEMATIC_JOURNEYS"
            )

        # ----------------------------------------------------
        # Critical journey
        # ----------------------------------------------------

        if (
            row["critical_journeys"] >= 1
        ):

            signals.append(
                "CRITICAL_JOURNEY"
            )

        # ----------------------------------------------------
        # No major signal
        # ----------------------------------------------------

        if not signals:

            signals.append(
                "NO_MAJOR_RISK_SIGNAL"
            )

        return " | ".join(
            signals
        )

    df["research_risk_signals"] = (
        df.apply(
            interpretation,
            axis=1
        )
    )

    return df


# ============================================================
# REPORT
# ============================================================

def print_report(df):

    print("\n")
    print("=" * 60)
    print("CUSTOMER RISK MODEL REPORT")
    print("=" * 60)

    print(
        "\nTotal customers:",
        f"{len(df):,}"
    )

    # --------------------------------------------------------
    # Risk distribution
    # --------------------------------------------------------

    print(
        "\nCUSTOMER RISK DISTRIBUTION"
    )

    print("-" * 40)

    print(
        df[
            "customer_risk_level"
        ]
        .value_counts()
        .sort_index()
    )

    # --------------------------------------------------------
    # Risk dimension averages
    # --------------------------------------------------------

    print(
        "\nRISK DIMENSION AVERAGES"
    )

    print("-" * 40)

    print(
        "Average severity:",
        round(
            df[
                "severity_score"
            ].mean(),
            2
        )
    )

    print(
        "Average frequency:",
        round(
            df[
                "frequency_score"
            ].mean(),
            2
        )
    )

    print(
        "Average persistence:",
        round(
            df[
                "persistence_score"
            ].mean(),
            2
        )
    )

    print(
        "Average customer risk:",
        round(
            df[
                "customer_risk_score"
            ].mean(),
            2
        )
    )

    # --------------------------------------------------------
    # Persistence statistics
    # --------------------------------------------------------

    print(
        "\nPERSISTENCE ANALYSIS"
    )

    print("-" * 40)

    print(
        "Customers with 0 problematic journeys:",
        (
            df[
                "problematic_journeys"
            ] == 0
        ).sum()
    )

    print(
        "Customers with 1 problematic journey:",
        (
            df[
                "problematic_journeys"
            ] == 1
        ).sum()
    )

    print(
        "Customers with 2 problematic journeys:",
        (
            df[
                "problematic_journeys"
            ] == 2
        ).sum()
    )

    print(
        "Customers with 3+ problematic journeys:",
        (
            df[
                "problematic_journeys"
            ] >= 3
        ).sum()
    )

    # --------------------------------------------------------
    # Behavior profile
    # --------------------------------------------------------

    print(
        "\nBEHAVIOR PROFILE DISTRIBUTION"
    )

    print("-" * 40)

    print(
        df[
            "behavior_profile"
        ]
        .value_counts()
    )

    # --------------------------------------------------------
    # Top customers
    # --------------------------------------------------------

    print(
        "\nTOP 10 CUSTOMER RISK"
    )

    print("-" * 40)

    columns = [

        "customer_id",

        "first_name",

        "last_name",

        "total_bookings",

        "problematic_journeys",

        "total_failed_payments",

        "total_retries",

        "total_anomalies",

        "severity_score",

        "frequency_score",

        "persistence_score",

        "customer_risk_score",

        "customer_risk_level",

        "behavior_profile",

        "research_risk_signals"
    ]

    print(

        df
        .sort_values(
            "customer_risk_score",
            ascending=False
        )
        [
            columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_model(df):

    print("\n")
    print("=" * 60)
    print("CUSTOMER RISK MODEL VALIDATION")
    print("=" * 60)

    checks = {}

    # --------------------------------------------------------
    # Score ranges
    # --------------------------------------------------------

    checks[
        "Severity range"
    ] = (
        df[
            "severity_score"
        ]
        .between(
            0,
            100
        )
        .all()
    )

    checks[
        "Frequency range"
    ] = (
        df[
            "frequency_score"
        ]
        .between(
            0,
            100
        )
        .all()
    )

    checks[
        "Persistence range"
    ] = (
        df[
            "persistence_score"
        ]
        .between(
            0,
            100
        )
        .all()
    )

    checks[
        "Risk score range"
    ] = (
        df[
            "customer_risk_score"
        ]
        .between(
            0,
            100
        )
        .all()
    )

    # --------------------------------------------------------
    # Customer uniqueness
    # --------------------------------------------------------

    checks[
        "Unique customer IDs"
    ] = (
        df[
            "customer_id"
        ]
        .is_unique
    )

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    checks[
        "No missing risk scores"
    ] = (
        df[
            "customer_risk_score"
        ]
        .notna()
        .all()
    )

    checks[
        "No missing risk levels"
    ] = (
        df[
            "customer_risk_level"
        ]
        .notna()
        .all()
    )

    # --------------------------------------------------------
    # Persistence logical validation
    # --------------------------------------------------------
    #
    # A customer with <= 1 problematic journey must not have
    # persistence above 30.
    # --------------------------------------------------------

    single_journey_persistence_valid = (

        df.loc[
            df[
                "problematic_journeys"
            ] <= 1,

            "persistence_score"
        ]

        <= 30

    ).all()

    checks[
        "Single problematic journey capped"
    ] = (
        single_journey_persistence_valid
    )

    # --------------------------------------------------------
    # No negative problematic journeys
    # --------------------------------------------------------

    checks[
        "Problematic journey counts valid"
    ] = (
        df[
            "problematic_journeys"
        ]
        >= 0
    ).all()

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    for name, result in checks.items():

        print(
            f"{name}:",
            "PASS"
            if result
            else "FAIL"
        )

    print(
        "\nOverall validation:",
        "PASSED"
        if all(
            checks.values()
        )
        else "FAILED"
    )

    return all(
        checks.values()
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    data = load_data()

    # --------------------------------------------------------
    # Journey flags
    # --------------------------------------------------------

    data = prepare_journey_flags(
        data
    )

    # --------------------------------------------------------
    # Customer aggregation
    # --------------------------------------------------------

    customer_features = (
        aggregate_customers(
            data
        )
    )

    # --------------------------------------------------------
    # Risk dimensions
    # --------------------------------------------------------

    customer_features = (
        calculate_severity(
            customer_features
        )
    )

    customer_features = (
        calculate_frequency(
            customer_features
        )
    )

    customer_features = (
        calculate_persistence(
            customer_features
        )
    )

    # --------------------------------------------------------
    # Combined risk
    # --------------------------------------------------------

    customer_features = (
        calculate_combined_risk(
            customer_features
        )
    )

    # --------------------------------------------------------
    # Behavior
    # --------------------------------------------------------

    customer_features = (
        build_behavior_profiles(
            customer_features
        )
    )

    # --------------------------------------------------------
    # Research signals
    # --------------------------------------------------------

    customer_features = (
        build_research_signal(
            customer_features
        )
    )

    # --------------------------------------------------------
    # Rounding
    # --------------------------------------------------------

    numeric_columns = [

        "total_booking_value",

        "average_friction_score",

        "maximum_friction_score",

        "failure_rate_per_booking",

        "retry_rate_per_booking",

        "anomaly_rate_per_booking",

        "problematic_journey_rate",

        "severity_score",

        "frequency_score",

        "persistence_score",

        "customer_risk_score"
    ]

    for column in numeric_columns:

        if column in customer_features.columns:

            customer_features[column] = (
                customer_features[
                    column
                ]
                .round(2)
            )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    customer_features.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print_report(
        customer_features
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    validation_passed = (
        validate_model(
            customer_features
        )
    )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)

    if validation_passed:

        print(
            "CUSTOMER RISK MODEL SUCCESS"
        )

    else:

        print(
            "CUSTOMER RISK MODEL FAILED VALIDATION"
        )

    print("=" * 60)

    print(
        "\nOutput file:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nCustomer records:",
        f"{len(customer_features):,}"
    )

    print(
        "Features generated:",
        f"{len(customer_features.columns):,}"
    )