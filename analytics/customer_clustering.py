import os
import sys

import numpy as np
import pandas as pd

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score
except ImportError:
    print("ERROR: scikit-learn is required.")
    print("Install with:")
    print("pip install scikit-learn")
    sys.exit(1)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

INPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_behavior_metrics.csv"
)

OUTPUT_CUSTOMER_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_clusters.csv"
)

OUTPUT_PROFILE_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_cluster_profiles.csv"
)

OUTPUT_EVALUATION_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_cluster_evaluation.csv"
)

FEATURES = [
    "total_bookings",
    "total_revenue",
    "average_booking_value",
    "recency_days",
    "booking_frequency"
]

MIN_CLUSTERS = 3
MAX_CLUSTERS = 6
RANDOM_STATE = 42


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not os.path.isfile(INPUT_FILE):

        raise FileNotFoundError(
            f"Behavior metrics file not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    required_columns = [
        "customer_id"
    ] + FEATURES

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Missing required columns: {missing}"
        )

    for column in FEATURES:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    return df


# ============================================================
# PREPARE FEATURES
# ============================================================

def prepare_features(df):

    print(
        "\nPreparing clustering features..."
    )

    result = df.copy()

    # --------------------------------------------------------
    # Customers with no bookings have no behavioral activity.
    # Keep them in the final output but exclude them from
    # behavioral clustering.
    # --------------------------------------------------------

    active_mask = (
        result[
            "total_bookings"
        ]
        > 0
    )

    active = result.loc[
        active_mask,
        [
            "customer_id"
        ] + FEATURES
    ].copy()

    if active.empty:

        raise ValueError(
            "No active customers available for clustering."
        )

    if active[FEATURES].isna().any().any():

        missing_counts = (
            active[FEATURES]
            .isna()
            .sum()
        )

        raise ValueError(
            "Missing clustering values:\n"
            + missing_counts.to_string()
        )

    return result, active, active_mask


# ============================================================
# CLUSTER ANALYSIS
# ============================================================

def run_clustering(active):

    print(
        "\nScaling clustering features..."
    )

    scaler = StandardScaler()

    X = scaler.fit_transform(
        active[FEATURES]
    )

    # --------------------------------------------------------
    # Evaluate K = 3 through 6
    # --------------------------------------------------------

    print(
        "Evaluating candidate cluster counts..."
    )

    evaluations = []

    for k in range(
        MIN_CLUSTERS,
        MAX_CLUSTERS + 1
    ):

        model = KMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            n_init=20
        )

        labels = model.fit_predict(
            X
        )

        score = silhouette_score(
            X,
            labels
        )

        evaluations.append(
            {
                "k": k,
                "silhouette_score": round(
                    float(score),
                    6
                ),
                "inertia": round(
                    float(model.inertia_),
                    4
                )
            }
        )

    evaluation_df = pd.DataFrame(
        evaluations
    )

    # --------------------------------------------------------
    # Best K
    # --------------------------------------------------------

    best_k = int(
        evaluation_df.loc[
            evaluation_df[
                "silhouette_score"
            ].idxmax(),
            "k"
        ]
    )

    best_score = float(
        evaluation_df.loc[
            evaluation_df[
                "silhouette_score"
            ].idxmax(),
            "silhouette_score"
        ]
    )

    print(
        f"Best cluster count: {best_k}"
    )

    print(
        f"Best silhouette score: "
        f"{best_score:.6f}"
    )

    # --------------------------------------------------------
    # Final KMeans
    # --------------------------------------------------------

    print(
        f"Building final K-Means model "
        f"with K={best_k}..."
    )

    final_model = KMeans(
        n_clusters=best_k,
        random_state=RANDOM_STATE,
        n_init=20
    )

    active["cluster_id"] = (
        final_model.fit_predict(
            X
        )
        .astype(int)
    )

    return (
        active,
        evaluation_df,
        best_k,
        best_score
    )


# ============================================================
# CLUSTER PROFILES
# ============================================================

def build_cluster_profiles(
    active
):

    print(
        "Building cluster profiles..."
    )

    profiles = (
        active
        .groupby(
            "cluster_id",
            as_index=False
        )
        .agg(

            customer_count=(
                "customer_id",
                "count"
            ),

            average_bookings=(
                "total_bookings",
                "mean"
            ),

            average_revenue=(
                "total_revenue",
                "mean"
            ),

            average_booking_value=(
                "average_booking_value",
                "mean"
            ),

            average_recency_days=(
                "recency_days",
                "mean"
            ),

            average_booking_frequency=(
                "booking_frequency",
                "mean"
            )
        )
    )

    total_customers = len(
        active
    )

    profiles[
        "customer_percentage"
    ] = (
        profiles[
            "customer_count"
        ]
        /
        total_customers
        *
        100
    )

    profiles = profiles.round(
        4
    )

    return profiles


# ============================================================
# BUILD FINAL CUSTOMER OUTPUT
# ============================================================

def build_customer_output(
    original,
    clustered
):

    print(
        "Building final customer cluster dataset..."
    )

    cluster_lookup = clustered[
        [
            "customer_id",
            "cluster_id"
        ]
    ]

    result = original.merge(
        cluster_lookup,
        on="customer_id",
        how="left",
        validate="one_to_one"
    )

    result[
        "cluster_status"
    ] = np.where(
        result[
            "total_bookings"
        ] > 0,
        "CLUSTERED",
        "NO_BOOKING_ACTIVITY"
    )

    result[
        "cluster_id"
    ] = (
        pd.to_numeric(
            result[
                "cluster_id"
            ],
            errors="coerce"
        )
        .astype("Int64")
    )

    return result


# ============================================================
# VALIDATION
# ============================================================

def validate_clustering(
    original,
    active,
    clustered,
    profiles,
    evaluation,
    final_output,
    best_k
):

    print()
    print("=" * 60)
    print(
        "DAY 7 CLUSTERING VALIDATION"
    )
    print("=" * 60)

    checks = []

    # --------------------------------------------------------
    # Customer coverage
    # --------------------------------------------------------

    checks.append(
        (
            "Customer count preserved",
            len(final_output)
            ==
            len(original),
            (
                f"Source={len(original):,}, "
                f"Output={len(final_output):,}"
            )
        )
    )

    # --------------------------------------------------------
    # Unique customer
    # --------------------------------------------------------

    checks.append(
        (
            "One row per customer",
            final_output[
                "customer_id"
            ].is_unique,
            (
                f"Duplicates="
                f"{final_output['customer_id'].duplicated().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # Active customers clustered
    # --------------------------------------------------------

    expected_active = (
        original[
            "total_bookings"
        ] > 0
    ).sum()

    actual_clustered = (
        final_output[
            "cluster_id"
        ]
        .notna()
        .sum()
    )

    checks.append(
        (
            "All active customers are clustered",
            actual_clustered
            ==
            expected_active,
            (
                f"Expected={expected_active:,}, "
                f"Actual={actual_clustered:,}"
            )
        )
    )

    # --------------------------------------------------------
    # Zero-booking customers
    # --------------------------------------------------------

    zero_booking = final_output[
        final_output[
            "total_bookings"
        ] == 0
    ]

    checks.append(
        (
            "Zero-booking customers remain unclustered",
            zero_booking[
                "cluster_id"
            ]
            .isna()
            .all(),
            (
                f"Zero-booking="
                f"{len(zero_booking):,}"
            )
        )
    )

    # --------------------------------------------------------
    # Cluster ID validity
    # --------------------------------------------------------

    cluster_values = set(
        clustered[
            "cluster_id"
        ]
        .unique()
    )

    expected_cluster_values = set(
        range(
            best_k
        )
    )

    checks.append(
        (
            "Cluster IDs are valid",
            cluster_values
            ==
            expected_cluster_values,
            (
                f"Expected={sorted(expected_cluster_values)}, "
                f"Actual={sorted(cluster_values)}"
            )
        )
    )

    # --------------------------------------------------------
    # Cluster count
    # --------------------------------------------------------

    checks.append(
        (
            "Correct number of clusters generated",
            len(cluster_values)
            ==
            best_k,
            (
                f"Expected={best_k}, "
                f"Actual={len(cluster_values)}"
            )
        )
    )

    # --------------------------------------------------------
    # Profile coverage
    # --------------------------------------------------------

    checks.append(
        (
            "Every cluster has a profile",
            set(
                profiles[
                    "cluster_id"
                ]
            )
            ==
            cluster_values,
            (
                f"Profiles={len(profiles):,}"
            )
        )
    )

    # --------------------------------------------------------
    # Profile customer conservation
    # --------------------------------------------------------

    checks.append(
        (
            "Cluster profile counts reconcile",
            profiles[
                "customer_count"
            ].sum()
            ==
            len(active),
            (
                f"Active={len(active):,}, "
                f"Profile total="
                f"{int(profiles['customer_count'].sum()):,}"
            )
        )
    )

    # --------------------------------------------------------
    # Silhouette score
    # --------------------------------------------------------

    best_row = evaluation[
        evaluation[
            "k"
        ]
        ==
        best_k
    ]

    best_score = float(
        best_row[
            "silhouette_score"
        ].iloc[0]
    )

    checks.append(
        (
            "Best silhouette score is valid",
            -1
            <=
            best_score
            <=
            1,
            (
                f"Score={best_score:.6f}"
            )
        )
    )

    # --------------------------------------------------------
    # Evaluation completeness
    # --------------------------------------------------------

    expected_k_count = (
        MAX_CLUSTERS
        -
        MIN_CLUSTERS
        +
        1
    )

    checks.append(
        (
            "All candidate K values evaluated",
            len(evaluation)
            ==
            expected_k_count,
            (
                f"Expected={expected_k_count}, "
                f"Actual={len(evaluation)}"
            )
        )
    )

    # --------------------------------------------------------
    # Feature integrity
    # --------------------------------------------------------

    checks.append(
        (
            "Clustering features contain no missing values",
            active[
                FEATURES
            ]
            .notna()
            .all()
            .all(),
            "All clustering features populated"
        )
    )

    # --------------------------------------------------------
    # Print
    # --------------------------------------------------------

    passed = 0

    for name, condition, detail in checks:

        status = (
            "PASS"
            if condition
            else
            "FAIL"
        )

        print(
            f"{name}: {status}"
        )

        if detail:

            print(
                f"    {detail}"
            )

        if condition:

            passed += 1

    failed = (
        len(checks)
        -
        passed
    )

    pass_rate = round(
        passed
        /
        len(checks)
        *
        100,
        2
    )

    print()

    print(
        f"Total checks: {len(checks)}"
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

    return (
        failed == 0
    )


# ============================================================
# REPORT
# ============================================================

def print_report(
    original,
    clustered,
    profiles,
    evaluation,
    best_k,
    best_score
):

    print()
    print("=" * 60)
    print(
        "DAY 7 BASIC CLUSTERING REPORT"
    )
    print("=" * 60)

    print()
    print(
        f"Total customers: "
        f"{len(original):,}"
    )

    print(
        f"Customers clustered: "
        f"{len(clustered):,}"
    )

    print(
        f"Selected K: "
        f"{best_k}"
    )

    print(
        f"Silhouette score: "
        f"{best_score:.6f}"
    )

    print()
    print("CLUSTER EVALUATION")
    print("-" * 40)

    print(
        evaluation.to_string(
            index=False
        )
    )

    print()
    print("CLUSTER PROFILES")
    print("-" * 40)

    print(
        profiles.to_string(
            index=False
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        "DAY 7 — BASIC CUSTOMER CLUSTERING"
    )
    print("=" * 60)

    try:

        print()
        print(
            "Loading behavioral metrics..."
        )

        original = load_data()

        print(
            f"Customers loaded: "
            f"{len(original):,}"
        )

        working, active, active_mask = (
            prepare_features(
                original
            )
        )

        clustered, evaluation, best_k, best_score = (
            run_clustering(
                active
            )
        )

        profiles = build_cluster_profiles(
            clustered
        )

        final_output = build_customer_output(
            working,
            clustered
        )

        print_report(
            original,
            clustered,
            profiles,
            evaluation,
            best_k,
            best_score
        )

        validation_passed = (
            validate_clustering(
                original,
                active,
                clustered,
                profiles,
                evaluation,
                final_output,
                best_k
            )
        )

        os.makedirs(
            PROCESSED_DIR,
            exist_ok=True
        )

        final_output.to_csv(
            OUTPUT_CUSTOMER_FILE,
            index=False
        )

        profiles.to_csv(
            OUTPUT_PROFILE_FILE,
            index=False
        )

        evaluation.to_csv(
            OUTPUT_EVALUATION_FILE,
            index=False
        )

        print()
        print("=" * 60)

        if validation_passed:

            print(
                "DAY 7 BASIC CLUSTERING: PASSED"
            )

        else:

            print(
                "DAY 7 BASIC CLUSTERING: FAILED"
            )

        print("=" * 60)

        print()
        print(
            "Customer clusters:"
        )

        print(
            OUTPUT_CUSTOMER_FILE
        )

        print()
        print(
            "Cluster profiles:"
        )

        print(
            OUTPUT_PROFILE_FILE
        )

        print()
        print(
            "Cluster evaluation:"
        )

        print(
            OUTPUT_EVALUATION_FILE
        )

        return (
            0
            if validation_passed
            else
            1
        )

    except Exception as exc:

        print()
        print("=" * 60)
        print(
            "DAY 7 BASIC CLUSTERING: FAILED"
        )
        print("=" * 60)

        print()
        print(
            f"ERROR: {exc}"
        )

        return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )