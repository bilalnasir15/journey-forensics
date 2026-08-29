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

INPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_behavior_metrics.csv"
)

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_segments.csv"
)


# ============================================================
# SEGMENT RULES
# ============================================================

VIP_REVENUE_PERCENTILE = 0.90

LOYAL_MAX_RECENCY = 180

NEW_MAX_RECENCY = 90

DORMANT_MIN_RECENCY = 365


# ============================================================
# LOAD DATA
# ============================================================

def load_metrics():

    if not os.path.isfile(INPUT_FILE):

        raise FileNotFoundError(
            f"Behavior metrics file not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    required_columns = [

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

    missing = [

        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Missing required columns: {missing}"
        )

    numeric_columns = [

        "total_bookings",
        "total_revenue",
        "average_booking_value",
        "recency_days",
        "booking_frequency",
        "repeat_booking_flag"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    return df


# ============================================================
# BUILD SEGMENTS
# ============================================================

def assign_segments(df):

    print(
        "\nCalculating segmentation thresholds..."
    )

    result = df.copy()

    # --------------------------------------------------------
    # VIP threshold
    # --------------------------------------------------------

    active_revenue = result.loc[
        result["total_bookings"] > 0,
        "total_revenue"
    ]

    if active_revenue.empty:

        vip_threshold = np.inf

    else:

        vip_threshold = active_revenue.quantile(
            VIP_REVENUE_PERCENTILE
        )

    print(
        f"VIP revenue threshold: "
        f"{vip_threshold:.2f}"
    )

    # --------------------------------------------------------
    # Base behavior conditions
    # --------------------------------------------------------

    has_booking = (
        result["total_bookings"] > 0
    )

    repeat_customer = (
        result["total_bookings"] >= 2
    )

    single_booking = (
        result["total_bookings"] == 1
    )

    recent_customer = (
        result["recency_days"]
        <= NEW_MAX_RECENCY
    )

    loyal_recent = (
        result["recency_days"]
        <= LOYAL_MAX_RECENCY
    )

    # --------------------------------------------------------
    # AT RISK
    # --------------------------------------------------------

    at_risk = (

        repeat_customer

        &

        (
            result["recency_days"]
            > LOYAL_MAX_RECENCY
        )

        &

        (
            result["recency_days"]
            <= DORMANT_MIN_RECENCY
        )
    )

    # --------------------------------------------------------
    # DORMANT
    # --------------------------------------------------------

    dormant = (

        has_booking

        &

        (
            result["recency_days"]
            >
            DORMANT_MIN_RECENCY
        )
    )

    # --------------------------------------------------------
    # VIP
    # --------------------------------------------------------

    vip = (

        has_booking

        &

        (
            result["total_revenue"]
            >= vip_threshold
        )
    )

    # --------------------------------------------------------
    # NEW
    # --------------------------------------------------------

    new_customer = (

        single_booking

        &

        recent_customer

        &

        ~vip
    )

    # --------------------------------------------------------
    # LOYAL
    # --------------------------------------------------------

    loyal = (

        repeat_customer

        &

        loyal_recent

        &

        ~vip
    )

    # --------------------------------------------------------
    # FINAL SEGMENT PRIORITY
    #
    # VIP
    # NEW
    # LOYAL
    # AT_RISK
    # DORMANT
    # OTHER
    # --------------------------------------------------------

    result["customer_segment"] = np.select(

        [
            vip,
            new_customer,
            loyal,
            at_risk,
            dormant
        ],

        [
            "VIP",
            "NEW",
            "LOYAL",
            "AT_RISK",
            "DORMANT"
        ],

        default="OTHER"
    )

    # ========================================================
    # COMPLAINT DATA LIMITATION
    # ========================================================

    result[
        "complaint_segment_status"
    ] = "NOT_SUPPORTED"

    result[
        "complaint_segment_reason"
    ] = (
        "Complaint data is not available "
        "in the current dataset."
    )

    # ========================================================
    # SEGMENT REASON
    # ========================================================

    result["segment_reason"] = np.select(

        [

            result[
                "customer_segment"
            ].eq("VIP"),

            result[
                "customer_segment"
            ].eq("NEW"),

            result[
                "customer_segment"
            ].eq("LOYAL"),

            result[
                "customer_segment"
            ].eq("AT_RISK"),

            result[
                "customer_segment"
            ].eq("DORMANT")
        ],

        [

            (
                "Top-value customer with total "
                "revenue at or above the 90th "
                "percentile."
            ),

            (
                "Single-booking customer with "
                f"recency <= {NEW_MAX_RECENCY} days."
            ),

            (
                "Repeat customer with "
                f"recency <= {LOYAL_MAX_RECENCY} days."
            ),

            (
                "Repeat customer inactive for more "
                f"than {LOYAL_MAX_RECENCY} days "
                f"and not beyond {DORMANT_MIN_RECENCY} days."
            ),

            (
                "Customer with booking history and "
                f"recency > {DORMANT_MIN_RECENCY} days."
            )
        ],

        default=(
            "Does not match an active roadmap "
            "segment rule."
        )
    )

    # ========================================================
    # SEGMENT FLAGS
    # ========================================================

    result["is_vip"] = (
        result["customer_segment"]
        .eq("VIP")
        .astype(int)
    )

    result["is_loyal"] = (
        result["customer_segment"]
        .eq("LOYAL")
        .astype(int)
    )

    result["is_new"] = (
        result["customer_segment"]
        .eq("NEW")
        .astype(int)
    )

    result["is_at_risk"] = (
        result["customer_segment"]
        .eq("AT_RISK")
        .astype(int)
    )

    result["is_dormant"] = (
        result["customer_segment"]
        .eq("DORMANT")
        .astype(int)
    )

    return result, vip_threshold


# ============================================================
# VALIDATION
# ============================================================

def validate_segments(
    source,
    result,
    vip_threshold
):

    print()
    print("=" * 60)
    print(
        "DAY 7 RULE-BASED SEGMENTATION VALIDATION"
    )
    print("=" * 60)

    checks = []

    # --------------------------------------------------------
    # Customer count
    # --------------------------------------------------------

    checks.append(
        (
            "Customer count preserved",

            len(result) == len(source),

            (
                f"Source={len(source):,}, "
                f"Segments={len(result):,}"
            )
        )
    )

    # --------------------------------------------------------
    # Unique customers
    # --------------------------------------------------------

    checks.append(
        (
            "One row per customer",

            result["customer_id"].is_unique,

            (
                f"Duplicates="
                f"{result['customer_id'].duplicated().sum()}"
            )
        )
    )

    # --------------------------------------------------------
    # No missing segments
    # --------------------------------------------------------

    checks.append(
        (
            "No missing customer segments",

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
    # Valid segment values
    # --------------------------------------------------------

    valid_segments = {

        "VIP",
        "NEW",
        "LOYAL",
        "AT_RISK",
        "DORMANT",
        "OTHER"
    }

    actual_segments = set(
        result[
            "customer_segment"
        ]
        .dropna()
        .unique()
    )

    checks.append(
        (
            "Segment values are valid",

            actual_segments.issubset(
                valid_segments
            ),

            str(
                sorted(
                    actual_segments
                )
            )
        )
    )

    # --------------------------------------------------------
    # VIP
    # --------------------------------------------------------

    vip_rows = result[
        result[
            "customer_segment"
        ].eq("VIP")
    ]

    checks.append(
        (
            "VIP customers meet revenue threshold",

            vip_rows[
                "total_revenue"
            ]
            .ge(vip_threshold)
            .all(),

            (
                f"Threshold={vip_threshold:.2f}, "
                f"Checked={len(vip_rows):,}"
            )
        )
    )

    # --------------------------------------------------------
    # NEW
    # --------------------------------------------------------

    new_rows = result[
        result[
            "customer_segment"
        ].eq("NEW")
    ]

    checks.append(
        (
            "New customers have one booking",

            new_rows[
                "total_bookings"
            ]
            .eq(1)
            .all(),

            (
                f"Checked={len(new_rows):,}"
            )
        )
    )

    checks.append(
        (
            "New customers are recent",

            new_rows[
                "recency_days"
            ]
            .le(NEW_MAX_RECENCY)
            .all(),

            (
                f"Threshold={NEW_MAX_RECENCY} days"
            )
        )
    )

    # --------------------------------------------------------
    # LOYAL
    # --------------------------------------------------------

    loyal_rows = result[
        result[
            "customer_segment"
        ].eq("LOYAL")
    ]

    checks.append(
        (
            "Loyal customers are repeat customers",

            loyal_rows[
                "total_bookings"
            ]
            .ge(2)
            .all(),

            (
                f"Checked={len(loyal_rows):,}"
            )
        )
    )

    checks.append(
        (
            "Loyal customers are recent enough",

            loyal_rows[
                "recency_days"
            ]
            .le(LOYAL_MAX_RECENCY)
            .all(),

            (
                f"Threshold={LOYAL_MAX_RECENCY} days"
            )
        )
    )

    # --------------------------------------------------------
    # AT RISK
    # --------------------------------------------------------

    risk_rows = result[
        result[
            "customer_segment"
        ].eq("AT_RISK")
    ]

    checks.append(
        (
            "At-risk customers are repeat customers",

            risk_rows[
                "total_bookings"
            ]
            .ge(2)
            .all(),

            (
                f"Checked={len(risk_rows):,}"
            )
        )
    )

    checks.append(
        (
            "At-risk customers have recency > 180 days",

            risk_rows[
                "recency_days"
            ]
            .gt(LOYAL_MAX_RECENCY)
            .all(),

            (
                f"Threshold={LOYAL_MAX_RECENCY} days"
            )
        )
    )

    checks.append(
        (
            "At-risk customers are not dormant",

            risk_rows[
                "recency_days"
            ]
            .le(DORMANT_MIN_RECENCY)
            .all(),

            (
                f"Upper boundary={DORMANT_MIN_RECENCY} days"
            )
        )
    )

    # --------------------------------------------------------
    # DORMANT
    # --------------------------------------------------------

    dormant_rows = result[
        result[
            "customer_segment"
        ].eq("DORMANT")
    ]

    checks.append(
        (
            "Dormant customers have booking history",

            dormant_rows[
                "total_bookings"
            ]
            .gt(0)
            .all(),

            (
                f"Checked={len(dormant_rows):,}"
            )
        )
    )

    checks.append(
        (
            "Dormant customers have recency > 365 days",

            dormant_rows[
                "recency_days"
            ]
            .gt(DORMANT_MIN_RECENCY)
            .all(),

            (
                f"Threshold={DORMANT_MIN_RECENCY} days"
            )
        )
    )

    # --------------------------------------------------------
    # COMPLAINT LIMITATION
    # --------------------------------------------------------

    checks.append(
        (
            "Complaint segment limitation is explicit",

            result[
                "complaint_segment_status"
            ]
            .eq("NOT_SUPPORTED")
            .all(),

            (
                "Complaint source is unavailable"
            )
        )
    )

    # --------------------------------------------------------
    # FLAGS
    #
    # Every validation entry has exactly:
    #   name
    #   condition
    #   detail
    # --------------------------------------------------------

    vip_flags_correct = (
        result["is_vip"]
        ==
        result[
            "customer_segment"
        ]
        .eq("VIP")
        .astype(int)
    ).all()

    checks.append(
        (
            "VIP flags are correct",

            vip_flags_correct,

            (
                f"Invalid flags="
                f"{int((
                    result['is_vip']
                    !=
                    result['customer_segment']
                    .eq('VIP')
                    .astype(int)
                ).sum())}"
            )
        )
    )

    loyal_flags_correct = (
        result["is_loyal"]
        ==
        result[
            "customer_segment"
        ]
        .eq("LOYAL")
        .astype(int)
    ).all()

    checks.append(
        (
            "Loyal flags are correct",

            loyal_flags_correct,

            (
                f"Invalid flags="
                f"{int((
                    result['is_loyal']
                    !=
                    result['customer_segment']
                    .eq('LOYAL')
                    .astype(int)
                ).sum())}"
            )
        )
    )

    new_flags_correct = (
        result["is_new"]
        ==
        result[
            "customer_segment"
        ]
        .eq("NEW")
        .astype(int)
    ).all()

    checks.append(
        (
            "New flags are correct",

            new_flags_correct,

            (
                f"Invalid flags="
                f"{int((
                    result['is_new']
                    !=
                    result['customer_segment']
                    .eq('NEW')
                    .astype(int)
                ).sum())}"
            )
        )
    )

    at_risk_flags_correct = (
        result["is_at_risk"]
        ==
        result[
            "customer_segment"
        ]
        .eq("AT_RISK")
        .astype(int)
    ).all()

    checks.append(
        (
            "At-risk flags are correct",

            at_risk_flags_correct,

            (
                f"Invalid flags="
                f"{int((
                    result['is_at_risk']
                    !=
                    result['customer_segment']
                    .eq('AT_RISK')
                    .astype(int)
                ).sum())}"
            )
        )
    )

    dormant_flags_correct = (
        result["is_dormant"]
        ==
        result[
            "customer_segment"
        ]
        .eq("DORMANT")
        .astype(int)
    ).all()

    checks.append(
        (
            "Dormant flags are correct",

            dormant_flags_correct,

            (
                f"Invalid flags="
                f"{int((
                    result['is_dormant']
                    !=
                    result['customer_segment']
                    .eq('DORMANT')
                    .astype(int)
                ).sum())}"
            )
        )
    )

    # --------------------------------------------------------
    # Segment exclusivity
    # --------------------------------------------------------

    segment_flag_sum = (
        result[
            [
                "is_vip",
                "is_loyal",
                "is_new",
                "is_at_risk",
                "is_dormant"
            ]
        ]
        .sum(axis=1)
    )

    checks.append(
        (
            "Customers receive at most one active segment",

            segment_flag_sum.le(1).all(),

            (
                f"Violations="
                f"{int(segment_flag_sum.gt(1).sum())}"
            )
        )
    )

    # ========================================================
    # PRINT VALIDATION
    # ========================================================

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
        (
            passed
            /
            len(checks)
        )
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
        failed == 0,
        checks
    )


# ============================================================
# REPORT
# ============================================================

def print_report(
    result,
    vip_threshold
):

    print()
    print("=" * 60)
    print(
        "DAY 7 CUSTOMER SEGMENTATION REPORT"
    )
    print("=" * 60)

    print()
    print(
        f"Customers: {len(result):,}"
    )

    print(
        f"VIP revenue threshold: "
        f"{vip_threshold:.2f}"
    )

    # --------------------------------------------------------
    # Distribution
    # --------------------------------------------------------

    print()
    print("SEGMENT DISTRIBUTION")
    print("-" * 40)

    segment_counts = (
        result[
            "customer_segment"
        ]
        .value_counts()
    )

    segment_percentages = (
        result[
            "customer_segment"
        ]
        .value_counts(
            normalize=True
        )
        *
        100
    )

    segment_report = pd.DataFrame(
        {
            "customer_count":
                segment_counts,

            "percentage":
                segment_percentages.round(2)
        }
    )

    print(
        segment_report.to_string()
    )

    # --------------------------------------------------------
    # Profile
    # --------------------------------------------------------

    print()
    print("SEGMENT PROFILE")
    print("-" * 40)

    profile = (
        result
        .groupby(
            "customer_segment"
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

            average_recency_days=(
                "recency_days",
                "mean"
            ),

            average_booking_value=(
                "average_booking_value",
                "mean"
            )
        )
        .round(2)
        .sort_values(
            "customer_count",
            ascending=False
        )
    )

    print(
        profile.to_string()
    )

    # --------------------------------------------------------
    # Top customers
    # --------------------------------------------------------

    print()
    print("TOP CUSTOMERS")
    print("-" * 40)

    top_customers = (
        result[
            [
                "customer_id",
                "customer_segment",
                "total_bookings",
                "total_revenue",
                "average_booking_value",
                "recency_days",
                "booking_frequency",
                "segment_reason"
            ]
        ]
        .sort_values(
            [
                "total_revenue",
                "total_bookings"
            ],
            ascending=False
        )
        .head(10)
    )

    print(
        top_customers.to_string(
            index=False
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        "DAY 7 — RULE-BASED CUSTOMER SEGMENTATION"
    )
    print("=" * 60)

    try:

        print()
        print(
            "Loading behavioral metrics..."
        )

        source = load_metrics()

        print(
            f"Customers loaded: "
            f"{len(source):,}"
        )

        result, vip_threshold = (
            assign_segments(
                source
            )
        )

        print_report(
            result,
            vip_threshold
        )

        validation_passed, checks = (
            validate_segments(
                source,
                result,
                vip_threshold
            )
        )

        os.makedirs(
            PROCESSED_DIR,
            exist_ok=True
        )

        result.to_csv(
            OUTPUT_FILE,
            index=False
        )

        print()
        print("=" * 60)

        if validation_passed:

            print(
                "DAY 7 RULE-BASED SEGMENTATION: PASSED"
            )

        else:

            print(
                "DAY 7 RULE-BASED SEGMENTATION: FAILED"
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
            f"Customer records: "
            f"{len(result):,}"
        )

        print(
            f"Features generated: "
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
            "DAY 7 RULE-BASED SEGMENTATION: FAILED"
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