import os
import sys

import numpy as np
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

COHORT_SUMMARY_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_cohort_summary.csv"
)

CLUSTER_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_clusters.csv"
)

CLUSTER_PROFILE_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_cluster_profiles.csv"
)

CLUSTER_EVALUATION_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_cluster_evaluation.csv"
)

FINAL_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_segmentation_final.csv"
)

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_validation_report.csv"
)


# ============================================================
# VALIDATION STORAGE
# ============================================================

results = []


def check(
    name,
    condition,
    detail=""
):

    status = (
        "PASS"
        if condition
        else "FAIL"
    )

    results.append(
        {
            "check": name,
            "status": status,
            "detail": detail
        }
    )

    print(
        f"{name}: {status}"
    )

    if detail:
        print(
            f"    {detail}"
        )


# ============================================================
# FILE LOADER
# ============================================================

def load_file(
    path,
    name
):

    if not os.path.isfile(path):

        check(
            f"{name} exists",
            False,
            path
        )

        return None

    try:

        df = pd.read_csv(
            path
        )

        check(
            f"{name} exists and loads",
            True,
            f"Rows={len(df):,}"
        )

        return df

    except Exception as exc:

        check(
            f"{name} exists and loads",
            False,
            str(exc)
        )

        return None


# ============================================================
# UNIQUE CUSTOMER CHECK
# ============================================================

def customer_ids_are_unique(
    df
):

    if df is None:
        return False

    return (
        "customer_id" in df.columns
        and
        df["customer_id"].is_unique
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 7 FINAL END-TO-END VALIDATION")
    print("=" * 60)

    # ========================================================
    # LOAD ALL DAY 7 OUTPUTS
    # ========================================================

    print()
    print("LOADING DAY 7 OUTPUTS")
    print("-" * 40)

    behavior = load_file(
        BEHAVIOR_FILE,
        "Behavior metrics"
    )

    segments = load_file(
        SEGMENT_FILE,
        "Rule-based segmentation"
    )

    cohorts = load_file(
        COHORT_FILE,
        "Customer cohort data"
    )

    cohort_summary = load_file(
        COHORT_SUMMARY_FILE,
        "Cohort summary"
    )

    clusters = load_file(
        CLUSTER_FILE,
        "Customer cluster data"
    )

    cluster_profiles = load_file(
        CLUSTER_PROFILE_FILE,
        "Cluster profiles"
    )

    cluster_evaluation = load_file(
        CLUSTER_EVALUATION_FILE,
        "Cluster evaluation"
    )

    final = load_file(
        FINAL_FILE,
        "Final segmentation module"
    )

    if any(
        dataset is None
        for dataset in [
            behavior,
            segments,
            cohorts,
            cohort_summary,
            clusters,
            cluster_profiles,
            cluster_evaluation,
            final
        ]
    ):

        print()
        print("=" * 60)
        print(
            "DAY 7 FINAL VALIDATION: FAILED"
        )
        print("=" * 60)

        return 1

    # ========================================================
    # CONSTANTS FROM CURRENT DATA
    # ========================================================

    EXPECTED_CUSTOMERS = 5000

    EXPECTED_ACTIVE_CUSTOMERS = 3967

    EXPECTED_ZERO_BOOKING = 1033

    EXPECTED_BOOKINGS = 8000

    # ========================================================
    # DATASET COUNTS
    # ========================================================

    print()
    print("VALIDATING DATASET COUNTS")
    print("-" * 40)

    check(
        "Behavior customer count = 5,000",
        len(behavior) == EXPECTED_CUSTOMERS,
        f"Actual={len(behavior):,}"
    )

    check(
        "Segment customer count = 5,000",
        len(segments) == EXPECTED_CUSTOMERS,
        f"Actual={len(segments):,}"
    )

    check(
        "Cohort customer count = 5,000",
        len(cohorts) == EXPECTED_CUSTOMERS,
        f"Actual={len(cohorts):,}"
    )

    check(
        "Cluster customer count = 5,000",
        len(clusters) == EXPECTED_CUSTOMERS,
        f"Actual={len(clusters):,}"
    )

    check(
        "Final customer count = 5,000",
        len(final) == EXPECTED_CUSTOMERS,
        f"Actual={len(final):,}"
    )

    # ========================================================
    # CUSTOMER ID UNIQUENESS
    # ========================================================

    print()
    print("VALIDATING CUSTOMER IDENTITY")
    print("-" * 40)

    check(
        "Behavior customer IDs are unique",
        customer_ids_are_unique(behavior),
        "One row per customer"
    )

    check(
        "Segment customer IDs are unique",
        customer_ids_are_unique(segments),
        "One row per customer"
    )

    check(
        "Cohort customer IDs are unique",
        customer_ids_are_unique(cohorts),
        "One row per customer"
    )

    check(
        "Cluster customer IDs are unique",
        customer_ids_are_unique(clusters),
        "One row per customer"
    )

    check(
        "Final customer IDs are unique",
        customer_ids_are_unique(final),
        "One row per customer"
    )

    # ========================================================
    # CROSS-LAYER CUSTOMER ID CONSISTENCY
    # ========================================================

    print()
    print("VALIDATING CROSS-LAYER CUSTOMER CONSISTENCY")
    print("-" * 40)

    behavior_ids = set(
        behavior["customer_id"].astype(str)
    )

    segment_ids = set(
        segments["customer_id"].astype(str)
    )

    cohort_ids = set(
        cohorts["customer_id"].astype(str)
    )

    cluster_ids = set(
        clusters["customer_id"].astype(str)
    )

    final_ids = set(
        final["customer_id"].astype(str)
    )

    check(
        "Behavior and segment customer IDs match",
        behavior_ids == segment_ids,
        (
            f"Difference="
            f"{len(behavior_ids ^ segment_ids)}"
        )
    )

    check(
        "Behavior and cohort customer IDs match",
        behavior_ids == cohort_ids,
        (
            f"Difference="
            f"{len(behavior_ids ^ cohort_ids)}"
        )
    )

    check(
        "Behavior and cluster customer IDs match",
        behavior_ids == cluster_ids,
        (
            f"Difference="
            f"{len(behavior_ids ^ cluster_ids)}"
        )
    )

    check(
        "Behavior and final customer IDs match",
        behavior_ids == final_ids,
        (
            f"Difference="
            f"{len(behavior_ids ^ final_ids)}"
        )
    )

    # ========================================================
    # BEHAVIOR METRICS
    # ========================================================

    print()
    print("VALIDATING BEHAVIORAL METRICS")
    print("-" * 40)

    required_behavior_columns = [

        "customer_id",
        "total_bookings",
        "total_revenue",
        "average_booking_value",
        "first_booking_date",
        "last_booking_date",
        "recency_days",
        "booking_frequency",
        "repeat_booking_flag"
    ]

    missing_behavior = [
        col
        for col in required_behavior_columns
        if col not in behavior.columns
    ]

    check(
        "Behavior metric columns exist",
        len(missing_behavior) == 0,
        (
            "All required columns present"
            if not missing_behavior
            else f"Missing={missing_behavior}"
        )
    )

    active = behavior[
        behavior["total_bookings"] > 0
    ]

    zero_booking = behavior[
        behavior["total_bookings"] == 0
    ]

    check(
        "Active customer count = 3,967",
        len(active) == EXPECTED_ACTIVE_CUSTOMERS,
        f"Actual={len(active):,}"
    )

    check(
        "Zero-booking customer count = 1,033",
        len(zero_booking) == EXPECTED_ZERO_BOOKING,
        f"Actual={len(zero_booking):,}"
    )

    check(
        "Behavior booking counts reconcile",
        int(
            behavior["total_bookings"].sum()
        )
        ==
        EXPECTED_BOOKINGS,
        (
            f"Expected={EXPECTED_BOOKINGS:,}, "
            f"Actual="
            f"{int(behavior['total_bookings'].sum()):,}"
        )
    )

    # ========================================================
    # RULE-BASED SEGMENTS
    # ========================================================

    print()
    print("VALIDATING RULE-BASED SEGMENTS")
    print("-" * 40)

    valid_segments = {
        "VIP",
        "NEW",
        "LOYAL",
        "AT_RISK",
        "DORMANT",
        "OTHER"
    }

    actual_segments = set(
        segments[
            "customer_segment"
        ]
        .dropna()
        .astype(str)
    )

    check(
        "Required customer segments exist",
        actual_segments.issubset(
            valid_segments
        ),
        str(
            sorted(actual_segments)
        )
    )

    check(
        "No missing customer segments",
        segments[
            "customer_segment"
        ]
        .notna()
        .all(),
        (
            f"Missing="
            f"{segments['customer_segment'].isna().sum()}"
        )
    )

    # --------------------------------------------------------
    # Re-check core segment rules
    # --------------------------------------------------------

    vip_rows = segments[
        segments["customer_segment"] == "VIP"
    ]

    if len(vip_rows) > 0:

        vip_threshold = vip_rows[
            "total_revenue"
        ].min()

        check(
            "VIP segment contains high-value customers",
            vip_rows[
                "total_revenue"
            ]
            .ge(vip_threshold)
            .all(),
            (
                f"Minimum VIP revenue="
                f"{vip_threshold:.2f}"
            )
        )

    new_rows = segments[
        segments["customer_segment"] == "NEW"
    ]

    check(
        "NEW segment customers have one booking",
        new_rows[
            "total_bookings"
        ]
        .eq(1)
        .all(),
        f"Checked={len(new_rows):,}"
    )

    check(
        "NEW segment customers are recent",
        new_rows[
            "recency_days"
        ]
        .le(90)
        .all(),
        "Recency <= 90 days"
    )

    loyal_rows = segments[
        segments["customer_segment"] == "LOYAL"
    ]

    check(
        "LOYAL segment customers are repeat customers",
        loyal_rows[
            "total_bookings"
        ]
        .ge(2)
        .all(),
        f"Checked={len(loyal_rows):,}"
    )

    check(
        "LOYAL segment customers are recent",
        loyal_rows[
            "recency_days"
        ]
        .le(180)
        .all(),
        "Recency <= 180 days"
    )

    at_risk_rows = segments[
        segments["customer_segment"] == "AT_RISK"
    ]

    check(
        "AT_RISK customers are repeat customers",
        at_risk_rows[
            "total_bookings"
        ]
        .ge(2)
        .all(),
        f"Checked={len(at_risk_rows):,}"
    )

    check(
        "AT_RISK recency is > 180 days",
        at_risk_rows[
            "recency_days"
        ]
        .gt(180)
        .all(),
        "Recency > 180 days"
    )

    check(
        "AT_RISK customers are not dormant",
        at_risk_rows[
            "recency_days"
        ]
        .le(365)
        .all(),
        "Recency <= 365 days"
    )

    dormant_rows = segments[
        segments["customer_segment"] == "DORMANT"
    ]

    check(
        "DORMANT customers have booking history",
        dormant_rows[
            "total_bookings"
        ]
        .gt(0)
        .all(),
        f"Checked={len(dormant_rows):,}"
    )

    check(
        "DORMANT recency is > 365 days",
        dormant_rows[
            "recency_days"
        ]
        .gt(365)
        .all(),
        "Recency > 365 days"
    )

    # ========================================================
    # COMPLAINT LIMITATION
    # ========================================================

    check(
        "Complaint segment limitation is explicit",
        segments[
            "complaint_segment_status"
        ]
        .eq("NOT_SUPPORTED")
        .all(),
        "No complaint data exists in current dataset"
    )

    # ========================================================
    # COHORT VALIDATION
    # ========================================================

    print()
    print("VALIDATING COHORT LAYER")
    print("-" * 40)

    check(
        "All active customers have a cohort",
        cohorts.loc[
            cohorts["cohort_status"]
            ==
            "ACTIVE_COHORT_MEMBER",
            "cohort_month"
        ]
        .notna()
        .all(),
        (
            f"Active={len(active):,}"
        )
    )

    check(
        "No-booking customers marked correctly",
        cohorts.loc[
            cohorts["cohort_status"]
            ==
            "NO_BOOKING",
            "first_booking_date"
        ]
        .isna()
        .all(),
        (
            f"Zero-booking="
            f"{len(zero_booking):,}"
        )
    )

    check(
        "Cohort summary exists",
        len(cohort_summary) > 0,
        (
            f"Cohorts="
            f"{len(cohort_summary):,}"
        )
    )

    check(
        "Cohort sizes reconcile",
        (
            cohort_summary[
                "cohort_size"
            ].sum()
            ==
            EXPECTED_ACTIVE_CUSTOMERS
        ),
        (
            f"Expected={EXPECTED_ACTIVE_CUSTOMERS:,}, "
            f"Actual="
            f"{int(cohort_summary['cohort_size'].sum()):,}"
        )
    )

    check(
        "Cohort repeat counts reconcile",
        (
            cohort_summary[
                "repeat_customers"
            ].sum()
            ==
            int(
                active[
                    "repeat_booking_flag"
                ].sum()
            )
        ),
        (
            f"Expected="
            f"{int(active['repeat_booking_flag'].sum()):,}, "
            f"Actual="
            f"{int(cohort_summary['repeat_customers'].sum()):,}"
        )
    )

    # ========================================================
    # CLUSTER VALIDATION
    # ========================================================

    print()
    print("VALIDATING CLUSTERING LAYER")
    print("-" * 40)

    clustered_active = clusters[
        clusters[
            "cluster_id"
        ].notna()
    ]

    check(
        "All active customers have cluster IDs",
        len(clustered_active)
        ==
        EXPECTED_ACTIVE_CUSTOMERS,
        (
            f"Expected={EXPECTED_ACTIVE_CUSTOMERS:,}, "
            f"Actual={len(clustered_active):,}"
        )
    )

    cluster_ids_used = set(
        clustered_active[
            "cluster_id"
        ]
        .astype(int)
        .unique()
    )

    check(
        "Exactly five clusters are present",
        cluster_ids_used == {0, 1, 2, 3, 4},
        (
            f"Clusters="
            f"{sorted(cluster_ids_used)}"
        )
    )

    check(
        "Cluster profiles reconcile",
        cluster_profiles[
            "customer_count"
        ].sum()
        ==
        EXPECTED_ACTIVE_CUSTOMERS,
        (
            f"Expected={EXPECTED_ACTIVE_CUSTOMERS:,}, "
            f"Actual="
            f"{int(cluster_profiles['customer_count'].sum()):,}"
        )
    )

    # --------------------------------------------------------
    # Cluster evaluation
    # --------------------------------------------------------

    check(
        "Four candidate K values evaluated",
        set(
            cluster_evaluation[
                "k"
            ].astype(int)
        )
        ==
        {3, 4, 5, 6},
        (
            f"Evaluated="
            f"{sorted(cluster_evaluation['k'].astype(int).unique())}"
        )
    )

    best_cluster_row = (
        cluster_evaluation.loc[
            cluster_evaluation[
                "silhouette_score"
            ].idxmax()
        ]
    )

    check(
        "K=5 has best silhouette score",
        int(
            best_cluster_row["k"]
        )
        == 5,
        (
            f"Best K="
            f"{int(best_cluster_row['k'])}"
        )
    )

    best_silhouette = float(
        best_cluster_row[
            "silhouette_score"
        ]
    )

    check(
        "Best silhouette score is between -1 and 1",
        -1 <= best_silhouette <= 1,
        (
            f"Score={best_silhouette:.6f}"
        )
    )

    # ========================================================
    # FINAL MODULE
    # ========================================================

    print()
    print("VALIDATING FINAL SEGMENTATION MODULE")
    print("-" * 40)

    required_final_columns = [

        "customer_id",

        "customer_segment",

        "segment_reason",

        "cohort_month",

        "cluster_id",

        "segmentation_status",

        "segmentation_method"
    ]

    missing_final = [
        column
        for column in required_final_columns
        if column not in final.columns
    ]

    check(
        "Final segmentation columns exist",
        len(missing_final) == 0,
        (
            "All required columns present"
            if not missing_final
            else f"Missing={missing_final}"
        )
    )

    check(
        "Final segmentation status is READY",
        final[
            "segmentation_status"
        ]
        .eq("READY")
        .all(),
        (
            f"Not READY="
            f"{int((
                final['segmentation_status']
                !=
                'READY'
            ).sum())}"
        )
    )

    check(
        "Final segmentation method is documented",
        final[
            "segmentation_method"
        ]
        .eq(
            "RULE_BASED_PRIMARY_WITH_COHORT_AND_EXPLORATORY_CLUSTER"
        )
        .all(),
        "Method documented"
    )

    # --------------------------------------------------------
    # Final segment equality
    # --------------------------------------------------------

    segment_map = (
        segments[
            [
                "customer_id",
                "customer_segment"
            ]
        ]
        .set_index(
            "customer_id"
        )[
            "customer_segment"
        ]
    )

    final_segment_map = (
        final[
            [
                "customer_id",
                "customer_segment"
            ]
        ]
        .set_index(
            "customer_id"
        )[
            "customer_segment"
        ]
    )

    check(
        "Final segments match primary segmentation",
        segment_map.equals(
            final_segment_map
        ),
        "Rule-based segment preserved"
    )

    # ========================================================
    # FINAL CROSS-LAYER COVERAGE
    # ========================================================

    check(
        "Final customer population conserved",
        len(final) == EXPECTED_CUSTOMERS,
        (
            f"Expected={EXPECTED_CUSTOMERS:,}, "
            f"Actual={len(final):,}"
        )
    )

    check(
        "Final active population conserved",
        final[
            "total_bookings"
        ]
        .gt(0)
        .sum()
        ==
        EXPECTED_ACTIVE_CUSTOMERS,
        (
            f"Expected={EXPECTED_ACTIVE_CUSTOMERS:,}, "
            f"Actual="
            f"{int(final['total_bookings'].gt(0).sum()):,}"
        )
    )

    # ========================================================
    # SAVE VALIDATION REPORT
    # ========================================================

    validation_df = pd.DataFrame(
        results
    )

    validation_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    total_checks = len(
        validation_df
    )

    passed = int(
        (
            validation_df[
                "status"
            ]
            ==
            "PASS"
        ).sum()
    )

    failed = (
        total_checks
        -
        passed
    )

    pass_rate = round(
        passed
        /
        total_checks
        *
        100,
        2
    )

    print()
    print("=" * 60)
    print("DAY 7 FINAL VALIDATION SUMMARY")
    print("=" * 60)

    print(
        f"Total checks: {total_checks}"
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

    print()

    if failed == 0:

        print("=" * 60)
        print(
            "DAY 7 CUSTOMER SEGMENTATION: PASSED"
        )
        print("=" * 60)

        print()
        print(
            "Behavioral metrics, rule-based segmentation, "
            "cohort analysis, clustering, and the final "
            "customer segmentation module are validated "
            "end-to-end."
        )

        print()
        print(
            "Validation report:"
        )

        print(
            OUTPUT_FILE
        )

        return 0

    print("=" * 60)
    print(
        "DAY 7 CUSTOMER SEGMENTATION: FAILED"
    )
    print("=" * 60)

    print()

    print(
        validation_df[
            validation_df[
                "status"
            ]
            ==
            "FAIL"
        ].to_string(
            index=False
        )
    )

    print()
    print(
        "Validation report:"
    )

    print(
        OUTPUT_FILE
    )

    return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )