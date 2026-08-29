import os
import sys

import numpy as np
import pandas as pd
from scipy import stats


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
    "customer_journey_features.csv"
)

RESULT_FILE = os.path.join(
    PROCESSED_DIR,
    "day6_hypothesis_test.csv"
)

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "day6_validation_report.csv"
)

ALPHA = 0.05
CONFIDENCE_LEVEL = 0.95

EXPECTED_TOTAL_JOURNEYS = 8000
EXPECTED_NO_FAILURE = 6038
EXPECTED_FAILURE = 1962


# ============================================================
# VALIDATION STORAGE
# ============================================================

results = []


def check(name, condition, detail=""):

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
# LOAD SOURCE DATA
# ============================================================

def load_input_data():

    if not os.path.isfile(INPUT_FILE):

        raise FileNotFoundError(
            f"Input dataset not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE
    )

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

    return df.dropna(
        subset=[
            "failed_payments",
            "journey_duration_minutes"
        ]
    )


# ============================================================
# COHEN'S D
# ============================================================

def calculate_cohens_d(
    group_a,
    group_b
):

    n_a = len(group_a)
    n_b = len(group_b)

    variance_a = group_a.var(
        ddof=1
    )

    variance_b = group_b.var(
        ddof=1
    )

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

    d = abs(d)

    if d < 0.20:
        return "NEGLIGIBLE"

    if d < 0.50:
        return "SMALL"

    if d < 0.80:
        return "MEDIUM"

    return "LARGE"


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 6 HYPOTHESIS TESTING VALIDATION")
    print("=" * 60)

    # ========================================================
    # RESULT FILE
    # ========================================================

    check(
        "Hypothesis test result file exists",
        os.path.isfile(RESULT_FILE),
        RESULT_FILE
    )

    if not os.path.isfile(
        RESULT_FILE
    ):

        return 1

    # ========================================================
    # LOAD RESULT
    # ========================================================

    try:

        result = pd.read_csv(
            RESULT_FILE
        )

        check(
            "Hypothesis test result loads",
            len(result) == 1,
            f"Records={len(result)}"
        )

    except Exception as exc:

        check(
            "Hypothesis test result loads",
            False,
            str(exc)
        )

        return 1

    # ========================================================
    # LOAD SOURCE
    # ========================================================

    try:

        df = load_input_data()

        check(
            "Source journey dataset loads",
            True,
            f"Records={len(df):,}"
        )

    except Exception as exc:

        check(
            "Source journey dataset loads",
            False,
            str(exc)
        )

        return 1

    # ========================================================
    # SOURCE DATA
    # ========================================================

    print()
    print("VALIDATING SOURCE DATA")
    print("-" * 40)

    check(
        "Total journey records",
        len(df) == EXPECTED_TOTAL_JOURNEYS,
        (
            f"Expected={EXPECTED_TOTAL_JOURNEYS:,}, "
            f"Actual={len(df):,}"
        )
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

    check(
        "No-failure group size",
        len(no_failure) == EXPECTED_NO_FAILURE,
        (
            f"Expected={EXPECTED_NO_FAILURE:,}, "
            f"Actual={len(no_failure):,}"
        )
    )

    check(
        "Payment-failure group size",
        len(payment_failure) == EXPECTED_FAILURE,
        (
            f"Expected={EXPECTED_FAILURE:,}, "
            f"Actual={len(payment_failure):,}"
        )
    )

    # ========================================================
    # RESULT STRUCTURE
    # ========================================================

    print()
    print("VALIDATING RESULT STRUCTURE")
    print("-" * 40)

    required_result_columns = [

        "investigation",

        "null_hypothesis",

        "alternative_hypothesis",

        "group_a",

        "group_b",

        "group_a_count",

        "group_b_count",

        "group_a_mean_minutes",

        "group_b_mean_minutes",

        "group_a_median_minutes",

        "group_b_median_minutes",

        "group_a_std_minutes",

        "group_b_std_minutes",

        "mean_difference_minutes",

        "test",

        "t_statistic",

        "degrees_of_freedom",

        "p_value",

        "alpha",

        "confidence_level",

        "confidence_interval_lower",

        "confidence_interval_upper",

        "effect_size_cohens_d",

        "effect_size_interpretation",

        "statistically_significant",

        "decision",

        "business_interpretation"
    ]

    missing_result_columns = [
        column
        for column in required_result_columns
        if column not in result.columns
    ]

    check(
        "Required hypothesis result columns exist",
        len(missing_result_columns) == 0,
        (
            "All required columns present"
            if not missing_result_columns
            else f"Missing={missing_result_columns}"
        )
    )

    # ========================================================
    # SINGLE RESULT ROW
    # ========================================================

    row = result.iloc[0]

    # ========================================================
    # HYPOTHESES
    # ========================================================

    print()
    print("VALIDATING HYPOTHESES")
    print("-" * 40)

    h0 = str(
        row["null_hypothesis"]
    ).strip()

    h1 = str(
        row["alternative_hypothesis"]
    ).strip()

    check(
        "H0 is represented",
        (
            h0.startswith("H0:")
            and
            len(h0) > 5
            and
            "equal" in h0.lower()
        ),
        h0
    )

    check(
        "H1 is represented",
        (
            h1.startswith("H1:")
            and
            len(h1) > 5
            and
            (
                "different" in h1.lower()
                or
                "not equal" in h1.lower()
            )
        ),
        h1
    )

    check(
        "Hypothesis investigation is defined",
        len(
            str(
                row["investigation"]
            ).strip()
        ) > 0,
        str(
            row["investigation"]
        )
    )

    check(
        "Correct statistical test used",
        row["test"]
        == "Welch two-sample t-test",
        str(
            row["test"]
        )
    )

    # ========================================================
    # GROUP COUNTS
    # ========================================================

    group_a_count = int(
        row["group_a_count"]
    )

    group_b_count = int(
        row["group_b_count"]
    )

    check(
        "Result group A count matches source",
        group_a_count == len(no_failure),
        (
            f"Result={group_a_count:,}, "
            f"Source={len(no_failure):,}"
        )
    )

    check(
        "Result group B count matches source",
        group_b_count == len(payment_failure),
        (
            f"Result={group_b_count:,}, "
            f"Source={len(payment_failure):,}"
        )
    )

    # ========================================================
    # MEANS
    # ========================================================

    expected_mean_a = no_failure.mean()
    expected_mean_b = payment_failure.mean()

    actual_mean_a = float(
        row["group_a_mean_minutes"]
    )

    actual_mean_b = float(
        row["group_b_mean_minutes"]
    )

    check(
        "Group A mean matches source",
        np.isclose(
            actual_mean_a,
            expected_mean_a,
            atol=0.001
        ),
        (
            f"Expected={expected_mean_a:.4f}, "
            f"Actual={actual_mean_a:.4f}"
        )
    )

    check(
        "Group B mean matches source",
        np.isclose(
            actual_mean_b,
            expected_mean_b,
            atol=0.001
        ),
        (
            f"Expected={expected_mean_b:.4f}, "
            f"Actual={actual_mean_b:.4f}"
        )
    )

    # ========================================================
    # MEDIANS
    # ========================================================

    expected_median_a = no_failure.median()
    expected_median_b = payment_failure.median()

    check(
        "Group A median matches source",
        np.isclose(
            float(
                row["group_a_median_minutes"]
            ),
            expected_median_a,
            atol=0.001
        ),
        (
            f"Expected={expected_median_a:.4f}, "
            f"Actual="
            f"{float(row['group_a_median_minutes']):.4f}"
        )
    )

    check(
        "Group B median matches source",
        np.isclose(
            float(
                row["group_b_median_minutes"]
            ),
            expected_median_b,
            atol=0.001
        ),
        (
            f"Expected={expected_median_b:.4f}, "
            f"Actual="
            f"{float(row['group_b_median_minutes']):.4f}"
        )
    )

    # ========================================================
    # MEAN DIFFERENCE
    # ========================================================

    expected_difference = (
        expected_mean_b
        -
        expected_mean_a
    )

    actual_difference = float(
        row["mean_difference_minutes"]
    )

    check(
        "Mean difference is correct",
        np.isclose(
            actual_difference,
            expected_difference,
            atol=0.001
        ),
        (
            f"Expected={expected_difference:.4f}, "
            f"Actual={actual_difference:.4f}"
        )
    )

    # ========================================================
    # WELCH TEST
    # ========================================================

    expected_test = stats.ttest_ind(
        payment_failure,
        no_failure,
        equal_var=False,
        alternative="two-sided"
    )

    expected_t = float(
        expected_test.statistic
    )

    expected_p = float(
        expected_test.pvalue
    )

    actual_t = float(
        row["t_statistic"]
    )

    actual_p = float(
        row["p_value"]
    )

    check(
        "t-statistic matches independent calculation",
        np.isclose(
            actual_t,
            expected_t,
            rtol=1e-6,
            atol=1e-6
        ),
        (
            f"Expected={expected_t:.8f}, "
            f"Actual={actual_t:.8f}"
        )
    )

    check(
        "p-value matches independent calculation",
        np.isclose(
            actual_p,
            expected_p,
            rtol=1e-6,
            atol=1e-200
        ),
        (
            f"Expected={expected_p:.12g}, "
            f"Actual={actual_p:.12g}"
        )
    )

    # ========================================================
    # WELCH DEGREES OF FREEDOM
    # ========================================================

    var_a = no_failure.var(
        ddof=1
    )

    var_b = payment_failure.var(
        ddof=1
    )

    n_a = len(
        no_failure
    )

    n_b = len(
        payment_failure
    )

    numerator = (
        var_a / n_a
        +
        var_b / n_b
    ) ** 2

    denominator = (
        (
            var_a / n_a
        ) ** 2
        /
        (n_a - 1)

        +

        (
            var_b / n_b
        ) ** 2
        /
        (n_b - 1)
    )

    expected_df = (
        numerator
        /
        denominator
    )

    actual_df = float(
        row["degrees_of_freedom"]
    )

    check(
        "Degrees of freedom match",
        np.isclose(
            actual_df,
            expected_df,
            rtol=1e-6,
            atol=1e-4
        ),
        (
            f"Expected={expected_df:.4f}, "
            f"Actual={actual_df:.4f}"
        )
    )

    # ========================================================
    # CONFIDENCE INTERVAL
    # ========================================================

    standard_error = np.sqrt(
        var_a / n_a
        +
        var_b / n_b
    )

    critical_t = stats.t.ppf(
        1 - (1 - CONFIDENCE_LEVEL) / 2,
        expected_df
    )

    margin = (
        critical_t
        *
        standard_error
    )

    expected_ci_lower = (
        expected_difference
        -
        margin
    )

    expected_ci_upper = (
        expected_difference
        +
        margin
    )

    actual_ci_lower = float(
        row["confidence_interval_lower"]
    )

    actual_ci_upper = float(
        row["confidence_interval_upper"]
    )

    check(
        "Confidence interval lower bound matches",
        np.isclose(
            actual_ci_lower,
            expected_ci_lower,
            atol=0.001
        ),
        (
            f"Expected={expected_ci_lower:.4f}, "
            f"Actual={actual_ci_lower:.4f}"
        )
    )

    check(
        "Confidence interval upper bound matches",
        np.isclose(
            actual_ci_upper,
            expected_ci_upper,
            atol=0.001
        ),
        (
            f"Expected={expected_ci_upper:.4f}, "
            f"Actual={actual_ci_upper:.4f}"
        )
    )

    check(
        "Confidence interval excludes zero",
        (
            expected_ci_lower > 0
            or
            expected_ci_upper < 0
        ),
        (
            f"CI=[{expected_ci_lower:.4f}, "
            f"{expected_ci_upper:.4f}]"
        )
    )

    # ========================================================
    # COHEN'S D
    # ========================================================

    expected_d = calculate_cohens_d(
        no_failure,
        payment_failure
    )

    actual_d = float(
        row["effect_size_cohens_d"]
    )

    check(
        "Cohen's d matches independent calculation",
        np.isclose(
            actual_d,
            expected_d,
            rtol=1e-6,
            atol=1e-6
        ),
        (
            f"Expected={expected_d:.6f}, "
            f"Actual={actual_d:.6f}"
        )
    )

    expected_effect = (
        interpret_effect_size(
            expected_d
        )
    )

    check(
        "Effect size interpretation is correct",
        row[
            "effect_size_interpretation"
        ]
        ==
        expected_effect,
        (
            f"Expected={expected_effect}, "
            f"Actual="
            f"{row['effect_size_interpretation']}"
        )
    )

    # ========================================================
    # SIGNIFICANCE
    # ========================================================

    expected_significance = (
        expected_p < ALPHA
    )

    actual_significance = (
        str(
            row[
                "statistically_significant"
            ]
        ).strip().lower()
        == "true"
    )

    check(
        "Statistical significance decision is correct",
        actual_significance
        ==
        expected_significance,
        (
            f"Expected={expected_significance}, "
            f"Actual={actual_significance}"
        )
    )

    # ========================================================
    # H0 DECISION
    # ========================================================

    expected_decision = (
        "REJECT_H0"
        if expected_significance
        else
        "FAIL_TO_REJECT_H0"
    )

    check(
        "H0 decision is correct",
        row["decision"]
        ==
        expected_decision,
        (
            f"Expected={expected_decision}, "
            f"Actual={row['decision']}"
        )
    )

    # ========================================================
    # ALPHA
    # ========================================================

    check(
        "Alpha is 0.05",
        np.isclose(
            float(row["alpha"]),
            ALPHA
        ),
        f"Alpha={row['alpha']}"
    )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    check(
        "Confidence level is 95%",
        np.isclose(
            float(
                row["confidence_level"]
            ),
            CONFIDENCE_LEVEL
        ),
        (
            f"Confidence="
            f"{row['confidence_level']}"
        )
    )

    # ========================================================
    # GROUP DIRECTION
    # ========================================================

    check(
        "Payment-failure group has longer mean journey",
        actual_mean_b > actual_mean_a,
        (
            f"No failure={actual_mean_a:.2f}, "
            f"Failure={actual_mean_b:.2f}"
        )
    )

    # ========================================================
    # BUSINESS INTERPRETATION
    # ========================================================

    business_text = str(
        row["business_interpretation"]
    ).strip()

    check(
        "Business interpretation exists",
        len(business_text) > 0,
        "Interpretation generated"
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
    # FINAL SUMMARY
    # ========================================================

    total = len(
        validation_df
    )

    passed = int(
        (
            validation_df["status"]
            == "PASS"
        ).sum()
    )

    failed = (
        total
        -
        passed
    )

    pass_rate = round(
        (
            passed
            /
            total
        )
        *
        100,
        2
    )

    print()
    print("=" * 60)
    print(
        "DAY 6 HYPOTHESIS TESTING VALIDATION SUMMARY"
    )
    print("=" * 60)

    print(
        f"Total checks: {total}"
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
            "DAY 6 HYPOTHESIS TESTING: PASSED"
        )
        print("=" * 60)

        print()
        print(
            "H0/H1, group definitions, Welch test, "
            "p-value, confidence interval, effect size, "
            "decision, and business interpretation "
            "are independently validated."
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
        "DAY 6 HYPOTHESIS TESTING: FAILED"
    )
    print("=" * 60)

    print()

    print(
        validation_df[
            validation_df["status"] == "FAIL"
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