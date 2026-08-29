import os
import sys

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

BEHAVIOR_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_behavior_metrics.csv"
)

SEGMENT_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_segments.csv"
)

COHORT_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_cohorts.csv"
)

CLUSTER_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_clusters.csv"
)

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_segmentation_final.csv"
)


# ============================================================
# LOAD FILE
# ============================================================

def load_file(
    path,
    name
):

    if not os.path.isfile(path):

        raise FileNotFoundError(
            f"{name} not found:\n{path}"
        )

    try:

        return pd.read_csv(
            path
        )

    except Exception as exc:

        raise RuntimeError(
            f"Could not load {name}: {exc}"
        )


# ============================================================
# PREPARE COHORT DATA
# ============================================================

def prepare_cohort_data(
    cohort
):

    columns = [
        "customer_id",
        "cohort_month",
        "cohort_status"
    ]

    missing = [
        column
        for column in columns
        if column not in cohort.columns
    ]

    if missing:

        raise ValueError(
            f"Missing cohort columns: {missing}"
        )

    return cohort[
        columns
    ].copy()


# ============================================================
# PREPARE CLUSTER DATA
# ============================================================

def prepare_cluster_data(
    clusters
):

    columns = [
        "customer_id",
        "cluster_id",
        "cluster_status"
    ]

    missing = [
        column
        for column in columns
        if column not in clusters.columns
    ]

    if missing:

        raise ValueError(
            f"Missing cluster columns: {missing}"
        )

    return clusters[
        columns
    ].copy()


# ============================================================
# BUILD FINAL MODULE
# ============================================================

def build_final_dataset(
    behavior,
    segments,
    cohort,
    clusters
):

    print(
        "\nCombining customer intelligence layers..."
    )

    # --------------------------------------------------------
    # Behavior
    # --------------------------------------------------------

    result = behavior.copy()

    # --------------------------------------------------------
    # Rule-based segment
    # --------------------------------------------------------

    segment_columns = [
        "customer_id",
        "customer_segment",
        "segment_reason",
        "complaint_segment_status",
        "complaint_segment_reason",
        "is_vip",
        "is_loyal",
        "is_new",
        "is_at_risk",
        "is_dormant"
    ]

    missing_segment_columns = [
        column
        for column in segment_columns
        if column not in segments.columns
    ]

    if missing_segment_columns:

        raise ValueError(
            "Missing segmentation columns: "
            f"{missing_segment_columns}"
        )

    segment_data = segments[
        segment_columns
    ].copy()

    result = result.merge(
        segment_data,
        on="customer_id",
        how="left",
        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Cohort
    # --------------------------------------------------------

    cohort_data = prepare_cohort_data(
        cohort
    )

    result = result.merge(
        cohort_data,
        on="customer_id",
        how="left",
        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Clustering
    # --------------------------------------------------------

    cluster_data = prepare_cluster_data(
        clusters
    )

    result = result.merge(
        cluster_data,
        on="customer_id",
        how="left",
        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    result["segmentation_status"] = (
        "READY"
    )

    result[
        "segmentation_method"
    ] = (
        "RULE_BASED_PRIMARY_WITH_COHORT_AND_EXPLORATORY_CLUSTER"
    )

    return result


# ============================================================
# VALIDATION
# ============================================================

def validate_final_module(
    behavior,
    segments,
    cohort,
    clusters,
    result
):

    print()
    print("=" * 60)
    print(
        "DAY 7 FINAL SEGMENTATION MODULE VALIDATION"
    )
    print("=" * 60)

    checks = []

    # --------------------------------------------------------
    # Customer count
    # --------------------------------------------------------

    checks.append(
        (
            "Customer count preserved",
            len(result)
            ==
            len(behavior),
            (
                f"Behavior={len(behavior):,}, "
                f"Final={len(result):,}"
            )
        )
    )

    # --------------------------------------------------------
    # One row per customer
    # --------------------------------------------------------

    checks.append(
        (
            "One row per customer",
            result[
                "customer_id"
            ].is_unique,
            (
                f"Duplicates="
                f"{result['customer_id'].duplicated().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # Behavioral metrics preserved
    # --------------------------------------------------------

    behavior_columns = [
        "total_bookings",
        "total_revenue",
        "average_booking_value",
        "recency_days",
        "booking_frequency",
        "repeat_booking_flag"
    ]

    missing_behavior = [
        column
        for column in behavior_columns
        if column not in result.columns
    ]

    checks.append(
        (
            "Behavioral metrics preserved",
            len(missing_behavior) == 0,
            (
                "All behavioral metrics present"
                if not missing_behavior
                else f"Missing={missing_behavior}"
            )
        )
    )

    # --------------------------------------------------------
    # Rule-based segmentation
    # --------------------------------------------------------

    checks.append(
        (
            "Rule-based segment preserved",
            result[
                "customer_segment"
            ].notna().all(),
            (
                f"Missing="
                f"{result['customer_segment'].isna().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # Segment reasons
    # --------------------------------------------------------

    checks.append(
        (
            "Segment reasons preserved",
            result[
                "segment_reason"
            ].notna().all(),
            (
                f"Missing="
                f"{result['segment_reason'].isna().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # Complaint limitation
    # --------------------------------------------------------

    checks.append(
        (
            "Complaint limitation preserved",
            result[
                "complaint_segment_status"
            ]
            .eq("NOT_SUPPORTED")
            .all(),
            "Complaint source remains explicitly unsupported"
        )
    )

    # --------------------------------------------------------
    # Cohort
    # --------------------------------------------------------

    active = result[
        result[
            "total_bookings"
        ]
        > 0
    ]

    cohort_active = (
        active[
            "cohort_month"
        ]
        .notna()
        .sum()
    )

    expected_active = (
        active[
            "customer_id"
        ]
        .nunique()
    )

    checks.append(
        (
            "Active customers have cohort assignments",
            cohort_active == expected_active,
            (
                f"Expected={expected_active:,}, "
                f"Actual={cohort_active:,}"
            )
        )
    )

    # --------------------------------------------------------
    # Cohort coverage
    # --------------------------------------------------------

    checks.append(
        (
            "Cohort customer coverage preserved",
            result[
                "customer_id"
            ].isin(
                cohort[
                    "customer_id"
                ]
            ).all(),
            "All final customers represented in cohort layer"
        )
    )

    # --------------------------------------------------------
    # Cluster status
    # --------------------------------------------------------

    clustered_active = result.loc[
        result[
            "total_bookings"
        ] > 0,
        "cluster_id"
    ].notna().sum()

    checks.append(
        (
            "All active customers retain cluster assignment",
            clustered_active == expected_active,
            (
                f"Expected={expected_active:,}, "
                f"Actual={clustered_active:,}"
            )
        )
    )

    # --------------------------------------------------------
    # Zero-booking customers
    # --------------------------------------------------------

    zero_booking = result[
        result[
            "total_bookings"
        ] == 0
    ]

    checks.append(
        (
            "Zero-booking customers retain no cluster",
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
    # Segmentation method
    # --------------------------------------------------------

    checks.append(
        (
            "Segmentation method is documented",
            result[
                "segmentation_method"
            ]
            .eq(
                "RULE_BASED_PRIMARY_WITH_COHORT_AND_EXPLORATORY_CLUSTER"
            )
            .all(),
            "Primary = business rules; cluster = exploratory"
        )
    )

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    checks.append(
        (
            "Segmentation status is READY",
            result[
                "segmentation_status"
            ]
            .eq("READY")
            .all(),
            "All final records marked READY"
        )
    )

    # --------------------------------------------------------
    # Customer ID consistency
    # --------------------------------------------------------

    checks.append(
        (
            "Customer IDs match behavior dataset",
            set(
                result[
                    "customer_id"
                ]
            )
            ==
            set(
                behavior[
                    "customer_id"
                ]
            ),
            "Customer ID sets match"
        )
    )

    # --------------------------------------------------------
    # Segment distribution conservation
    # --------------------------------------------------------

    segment_counts = (
        result[
            "customer_segment"
        ]
        .value_counts()
        .sum()
    )

    checks.append(
        (
            "Segment population is conserved",
            int(
                segment_counts
            )
            ==
            len(result),
            (
                f"Segments={int(segment_counts):,}, "
                f"Customers={len(result):,}"
            )
        )
    )

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    passed = 0

    for name, condition, detail in checks:

        status = (
            "PASS"
            if condition
            else "FAIL"
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

    return failed == 0


# ============================================================
# REPORT
# ============================================================

def print_report(
    result
):

    print()
    print("=" * 60)
    print(
        "DAY 7 FINAL CUSTOMER SEGMENTATION REPORT"
    )
    print("=" * 60)

    print()
    print(
        f"Total customers: "
        f"{len(result):,}"
    )

    print(
        f"Customers with bookings: "
        f"{int(result['total_bookings'].gt(0).sum()):,}"
    )

    print(
        f"Customers without bookings: "
        f"{int(result['total_bookings'].eq(0).sum()):,}"
    )

    # --------------------------------------------------------
    # Rule-based distribution
    # --------------------------------------------------------

    print()
    print("PRIMARY BUSINESS SEGMENTS")
    print("-" * 40)

    distribution = (
        result[
            "customer_segment"
        ]
        .value_counts()
        .to_frame(
            "customer_count"
        )
    )

    distribution[
        "percentage"
    ] = (
        distribution[
            "customer_count"
        ]
        /
        len(result)
        *
        100
    ).round(2)

    print(
        distribution.to_string()
    )

    # --------------------------------------------------------
    # Cluster distribution
    # --------------------------------------------------------

    print()
    print("EXPLORATORY CLUSTERS")
    print("-" * 40)

    cluster_distribution = (
        result[
            result[
                "cluster_id"
            ].notna()
        ][
            "cluster_id"
        ]
        .astype(int)
        .value_counts()
        .sort_index()
        .to_frame(
            "customer_count"
        )
    )

    cluster_distribution[
        "percentage"
    ] = (
        cluster_distribution[
            "customer_count"
        ]
        /
        cluster_distribution[
            "customer_count"
        ].sum()
        *
        100
    ).round(2)

    print(
        cluster_distribution.to_string()
    )

    # --------------------------------------------------------
    # Segment + cohort snapshot
    # --------------------------------------------------------

    print()
    print(
        "SEGMENT / COHORT SNAPSHOT"
    )
    print("-" * 40)

    snapshot = (
        result[
            result[
                "total_bookings"
            ] > 0
        ]
        .groupby(
            "customer_segment"
        )
        .agg(
            customers=(
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

            average_recency_days=(
                "recency_days",
                "mean"
            )
        )
        .round(2)
    )

    print(
        snapshot.to_string()
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        "DAY 7 — FINAL CUSTOMER SEGMENTATION MODULE"
    )
    print("=" * 60)

    try:

        print()
        print(
            "Loading Day 7 analytical layers..."
        )

        behavior = load_file(
            BEHAVIOR_FILE,
            "Behavior metrics"
        )

        segments = load_file(
            SEGMENT_FILE,
            "Rule-based segmentation"
        )

        cohort = load_file(
            COHORT_FILE,
            "Customer cohorts"
        )

        clusters = load_file(
            CLUSTER_FILE,
            "Customer clusters"
        )

        print(
            f"Behavior records: "
            f"{len(behavior):,}"
        )

        print(
            f"Segment records: "
            f"{len(segments):,}"
        )

        print(
            f"Cohort records: "
            f"{len(cohort):,}"
        )

        print(
            f"Cluster records: "
            f"{len(clusters):,}"
        )

        # ----------------------------------------------------
        # Build
        # ----------------------------------------------------

        result = build_final_dataset(
            behavior,
            segments,
            cohort,
            clusters
        )

        # ----------------------------------------------------
        # Report
        # ----------------------------------------------------

        print_report(
            result
        )

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        validation_passed = (
            validate_final_module(
                behavior,
                segments,
                cohort,
                clusters,
                result
            )
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        os.makedirs(
            PROCESSED_DIR,
            exist_ok=True
        )

        result.to_csv(
            OUTPUT_FILE,
            index=False
        )

        # ----------------------------------------------------
        # Final
        # ----------------------------------------------------

        print()
        print("=" * 60)

        if validation_passed:

            print(
                "DAY 7 FINAL SEGMENTATION MODULE: PASSED"
            )

        else:

            print(
                "DAY 7 FINAL SEGMENTATION MODULE: FAILED"
            )

        print("=" * 60)

        print()
        print(
            "Output file:"
        )

        print(
            OUTPUT_FILE
        )

        print()
        print(
            f"Final customer records: "
            f"{len(result):,}"
        )

        print(
            f"Final features: "
            f"{len(result.columns):,}"
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
            "DAY 7 FINAL SEGMENTATION MODULE: FAILED"
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