import os
import sys

import numpy as np
import pandas as pd

try:
    from scipy import stats
except ImportError:
    print("ERROR: scipy is required.")
    print("Install it with:")
    print("pip install scipy")
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
    "customer_journey_features.csv"
)

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day6_hypothesis_test.csv"
)

ALPHA = 0.05
CONFIDENCE_LEVEL = 0.95


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not os.path.isfile(INPUT_FILE):
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "failed_payments",
        "journey_duration_minutes"
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

    df["failed_payments"] = pd.to_numeric(
        df["failed_payments"],
        errors="coerce"
    )

    df["journey_duration_minutes"] = pd.to_numeric(
        df["journey_duration_minutes"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "failed_payments",
            "journey_duration_minutes"
        ]
    )

    return df


# ============================================================
# COHEN'S D
# ============================================================

def cohens_d(group_a, group_b):

    n_a = len(group_a)
    n_b = len(group_b)

    if n_a < 2 or n_b < 2:
        return np.nan

    variance_a = group_a.var(ddof=1)
    variance_b = group_b.var(ddof=1)

    pooled_sd = np.sqrt(
        (
            (n_a - 1) * variance_a
            +
            (n_b - 1) * variance_b
        )
        /
        (
            n_a + n_b - 2
        )
    )

    if pooled_sd == 0:
        return np.nan

    return (
        group_b.mean()
        -
        group_a.mean()
    ) / pooled_sd


# ============================================================
# EFFECT SIZE INTERPRETATION
# ============================================================

def interpret_effect_size(d):

    absolute_d = abs(d)

    if absolute_d < 0.20:
        return "NEGLIGIBLE"

    if absolute_d < 0.50:
        return "SMALL"

    if absolute_d < 0.80:
        return "MEDIUM"

    return "LARGE"


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 6 — HYPOTHESIS TESTING ENGINE")
    print("=" * 60)

    # ========================================================
    # LOAD
    # ========================================================

    print()
    print(
        "Loading journey feature dataset..."
    )

    df = load_data()

    print(
        f"Total journeys: {len(df):,}"
    )

    # ========================================================
    # HYPOTHESES
    # ========================================================

    null_hypothesis = (
        "H0: Mean journey duration is equal between "
        "journeys with payment failure and journeys "
        "without payment failure."
    )

    alternative_hypothesis = (
        "H1: Mean journey duration is different between "
        "journeys with payment failure and journeys "
        "without payment failure."
    )

    # ========================================================
    # GROUPS
    # ========================================================

    print()
    print(
        "Preparing hypothesis test groups..."
    )

    no_failure = (
        df[
            df["failed_payments"] == 0
        ][
            "journey_duration_minutes"
        ]
        .astype(float)
    )

    payment_failure = (
        df[
            df["failed_payments"] > 0
        ][
            "journey_duration_minutes"
        ]
        .astype(float)
    )

    if no_failure.empty:
        raise ValueError(
            "No-payment-failure group is empty."
        )

    if payment_failure.empty:
        raise ValueError(
            "Payment-failure group is empty."
        )

    # ========================================================
    # DESCRIPTIVE STATISTICS
    # ========================================================

    no_failure_mean = no_failure.mean()
    failure_mean = payment_failure.mean()

    no_failure_median = no_failure.median()
    failure_median = payment_failure.median()

    no_failure_std = no_failure.std(ddof=1)
    failure_std = payment_failure.std(ddof=1)

    mean_difference = (
        failure_mean
        -
        no_failure_mean
    )

    # ========================================================
    # WELCH TEST
    # ========================================================

    print(
        "Running Welch two-sample t-test..."
    )

    test_result = stats.ttest_ind(
        payment_failure,
        no_failure,
        equal_var=False,
        alternative="two-sided"
    )

    t_statistic = float(
        test_result.statistic
    )

    p_value = float(
        test_result.pvalue
    )

    # ========================================================
    # WELCH DEGREES OF FREEDOM
    # ========================================================

    n_failure = len(payment_failure)
    n_no_failure = len(no_failure)

    variance_failure = failure_std ** 2
    variance_no_failure = no_failure_std ** 2

    numerator = (
        variance_failure / n_failure
        +
        variance_no_failure / n_no_failure
    ) ** 2

    denominator = (
        (
            variance_failure / n_failure
        ) ** 2
        /
        (n_failure - 1)
        +
        (
            variance_no_failure / n_no_failure
        ) ** 2
        /
        (n_no_failure - 1)
    )

    degrees_of_freedom = (
        numerator / denominator
    )

    # ========================================================
    # CONFIDENCE INTERVAL
    # ========================================================

    standard_error = np.sqrt(
        variance_failure / n_failure
        +
        variance_no_failure / n_no_failure
    )

    critical_t = stats.t.ppf(
        1 - (1 - CONFIDENCE_LEVEL) / 2,
        degrees_of_freedom
    )

    margin_of_error = (
        critical_t
        *
        standard_error
    )

    ci_lower = (
        mean_difference
        -
        margin_of_error
    )

    ci_upper = (
        mean_difference
        +
        margin_of_error
    )

    # ========================================================
    # EFFECT SIZE
    # ========================================================

    effect_size = cohens_d(
        no_failure,
        payment_failure
    )

    effect_interpretation = (
        interpret_effect_size(
            effect_size
        )
    )

    # ========================================================
    # DECISION
    # ========================================================

    statistically_significant = (
        p_value < ALPHA
    )

    decision = (
        "REJECT_H0"
        if statistically_significant
        else
        "FAIL_TO_REJECT_H0"
    )

    # ========================================================
    # BUSINESS INTERPRETATION
    # ========================================================

    if statistically_significant:

        business_interpretation = (
            "Journeys with at least one payment failure "
            "have a statistically significant difference "
            f"in mean duration of {mean_difference:.2f} "
            "minutes compared with journeys without "
            "payment failure."
        )

    else:

        business_interpretation = (
            "The observed difference in journey duration "
            "is not statistically significant at the "
            "5% significance level."
        )

    # ========================================================
    # RESULT
    # ========================================================

    result = {

        "investigation":
            "Payment failure vs journey duration",

        "null_hypothesis":
            null_hypothesis,

        "alternative_hypothesis":
            alternative_hypothesis,

        "group_a":
            "NO_PAYMENT_FAILURE",

        "group_b":
            "PAYMENT_FAILURE",

        "group_a_count":
            n_no_failure,

        "group_b_count":
            n_failure,

        "group_a_mean_minutes":
            round(
                no_failure_mean,
                4
            ),

        "group_b_mean_minutes":
            round(
                failure_mean,
                4
            ),

        "group_a_median_minutes":
            round(
                no_failure_median,
                4
            ),

        "group_b_median_minutes":
            round(
                failure_median,
                4
            ),

        "group_a_std_minutes":
            round(
                no_failure_std,
                4
            ),

        "group_b_std_minutes":
            round(
                failure_std,
                4
            ),

        "mean_difference_minutes":
            round(
                mean_difference,
                4
            ),

        "test":
            "Welch two-sample t-test",

        "t_statistic":
            round(
                t_statistic,
                6
            ),

        "degrees_of_freedom":
            round(
                degrees_of_freedom,
                4
            ),

        "p_value":
            p_value,

        "alpha":
            ALPHA,

        "confidence_level":
            CONFIDENCE_LEVEL,

        "confidence_interval_lower":
            round(
                ci_lower,
                4
            ),

        "confidence_interval_upper":
            round(
                ci_upper,
                4
            ),

        "effect_size_cohens_d":
            round(
                effect_size,
                6
            ),

        "effect_size_interpretation":
            effect_interpretation,

        "statistically_significant":
            statistically_significant,

        "decision":
            decision,

        "business_interpretation":
            business_interpretation
    }

    result_df = pd.DataFrame(
        [result]
    )

    os.makedirs(
        PROCESSED_DIR,
        exist_ok=True
    )

    result_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # REPORT
    # ========================================================

    print()
    print("=" * 60)
    print("HYPOTHESIS TEST REPORT")
    print("=" * 60)

    print()
    print("HYPOTHESES")
    print("-" * 40)

    print(
        null_hypothesis
    )

    print(
        alternative_hypothesis
    )

    print()
    print("GROUPS")
    print("-" * 40)

    print(
        f"No payment failure: "
        f"{n_no_failure:,} journeys"
    )

    print(
        f"Payment failure: "
        f"{n_failure:,} journeys"
    )

    print()
    print("DESCRIPTIVE STATISTICS")
    print("-" * 40)

    print(
        f"No-failure mean: "
        f"{no_failure_mean:.2f} minutes"
    )

    print(
        f"Failure mean: "
        f"{failure_mean:.2f} minutes"
    )

    print(
        f"Mean difference: "
        f"{mean_difference:.2f} minutes"
    )

    print()
    print("STATISTICAL TEST")
    print("-" * 40)

    print(
        "Test: Welch two-sample t-test"
    )

    print(
        f"t-statistic: "
        f"{t_statistic:.6f}"
    )

    print(
        f"Degrees of freedom: "
        f"{degrees_of_freedom:.2f}"
    )

    print(
        f"p-value: "
        f"{p_value:.12g}"
    )

    print(
        f"Alpha: "
        f"{ALPHA}"
    )

    print()
    print("CONFIDENCE INTERVAL")
    print("-" * 40)

    print(
        f"95% CI for mean difference: "
        f"[{ci_lower:.2f}, {ci_upper:.2f}] minutes"
    )

    print()
    print("EFFECT SIZE")
    print("-" * 40)

    print(
        f"Cohen's d: "
        f"{effect_size:.4f}"
    )

    print(
        f"Interpretation: "
        f"{effect_interpretation}"
    )

    print()
    print("DECISION")
    print("-" * 40)

    print(
        decision
    )

    print(
        f"Statistically significant: "
        f"{statistically_significant}"
    )

    print()
    print("BUSINESS INTERPRETATION")
    print("-" * 40)

    print(
        business_interpretation
    )

    print()
    print("=" * 60)
    print("DAY 6 HYPOTHESIS TESTING ENGINE COMPLETE")
    print("=" * 60)

    print()
    print("Output file:")
    print(OUTPUT_FILE)

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(main())