import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

JOURNEY_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "customer_journey_features.csv"
)

RISK_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "customer_risk_model.csv"
)

EXPLANATION_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "customer_risk_explanations.csv"
)

SEGMENT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "customer_risk_segments.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "day5_validation_report.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("=" * 60)
    print("DAY 5 END-TO-END VALIDATION")
    print("=" * 60)

    print("\nLoading analytical datasets...")

    journey = pd.read_csv(
        JOURNEY_FILE
    )

    risk = pd.read_csv(
        RISK_FILE
    )

    explanation = pd.read_csv(
        EXPLANATION_FILE
    )

    segment = pd.read_csv(
        SEGMENT_FILE
    )

    print(
        f"Journey features: {len(journey):,}"
    )

    print(
        f"Risk model: {len(risk):,}"
    )

    print(
        f"Explanations: {len(explanation):,}"
    )

    print(
        f"Segments: {len(segment):,}"
    )

    return (
        journey,
        risk,
        explanation,
        segment
    )


# ============================================================
# VALIDATION FRAMEWORK
# ============================================================

class ValidationReport:

    def __init__(self):

        self.results = []

    def add(
        self,
        category,
        check,
        passed,
        details=""
    ):

        self.results.append(
            {
                "category": category,
                "check": check,
                "status":
                    "PASS"
                    if passed
                    else "FAIL",
                "details": details
            }
        )

    def dataframe(self):

        return pd.DataFrame(
            self.results
        )

    def passed(self):

        return all(
            row["status"] == "PASS"
            for row in self.results
        )


# ============================================================
# BASIC DATASET VALIDATION
# ============================================================

def validate_dataset_sizes(
    journey,
    risk,
    explanation,
    segment,
    report
):

    print(
        "\nValidating dataset sizes..."
    )

    # Journey should contain 8,000 bookings
    report.add(
        "Dataset",
        "Journey records exist",
        len(journey) > 0,
        f"{len(journey):,} records"
    )

    # Customer-level datasets should have same number
    # of customer records
    customer_counts = [
        len(risk),
        len(explanation),
        len(segment)
    ]

    report.add(
        "Dataset",
        "Customer datasets have equal record counts",
        len(set(customer_counts)) == 1,
        str(customer_counts)
    )

    # Current project has one customer-level record per
    # unique customer in the risk model
    report.add(
        "Dataset",
        "Risk model has one row per customer",
        risk["customer_id"].is_unique,
        f"{risk['customer_id'].nunique():,} unique customers"
    )


# ============================================================
# CUSTOMER ID CONSISTENCY
# ============================================================

def validate_customer_ids(
    risk,
    explanation,
    segment,
    report
):

    print(
        "Validating customer identity consistency..."
    )

    risk_ids = set(
        risk["customer_id"]
    )

    explanation_ids = set(
        explanation["customer_id"]
    )

    segment_ids = set(
        segment["customer_id"]
    )

    # --------------------------------------------------------
    # Risk vs explanation
    # --------------------------------------------------------

    report.add(
        "Identity",
        "Risk and explanation customers match",
        risk_ids == explanation_ids,
        f"Difference: {len(risk_ids ^ explanation_ids)}"
    )

    # --------------------------------------------------------
    # Risk vs segmentation
    # --------------------------------------------------------

    report.add(
        "Identity",
        "Risk and segmentation customers match",
        risk_ids == segment_ids,
        f"Difference: {len(risk_ids ^ segment_ids)}"
    )


# ============================================================
# RISK SCORE VALIDATION
# ============================================================

def validate_risk_scores(
    risk,
    report
):

    print(
        "Validating risk scores..."
    )

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required = [
        "severity_score",
        "frequency_score",
        "persistence_score",
        "customer_risk_score"
    ]

    for column in required:

        exists = column in risk.columns

        report.add(
            "Risk Model",
            f"{column} exists",
            exists
        )

    # --------------------------------------------------------
    # Score ranges
    # --------------------------------------------------------

    score_columns = [
        "severity_score",
        "frequency_score",
        "persistence_score",
        "customer_risk_score"
    ]

    for column in score_columns:

        if column not in risk.columns:
            continue

        valid = (
            risk[column]
            .between(
                0,
                100
            )
            .all()
        )

        report.add(
            "Risk Model",
            f"{column} range 0-100",
            valid,
            (
                f"min={risk[column].min():.2f}, "
                f"max={risk[column].max():.2f}"
            )
        )

    # --------------------------------------------------------
    # Missing scores
    # --------------------------------------------------------

    for column in score_columns:

        if column not in risk.columns:
            continue

        missing = (
            risk[column]
            .isna()
            .sum()
        )

        report.add(
            "Risk Model",
            f"No missing {column}",
            missing == 0,
            f"Missing: {missing}"
        )


# ============================================================
# RISK LEVEL VALIDATION
# ============================================================

def validate_risk_levels(
    risk,
    explanation,
    report
):

    print(
        "Validating risk levels..."
    )

    valid_levels = {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    }

    # --------------------------------------------------------
    # Risk model
    # --------------------------------------------------------

    risk_levels = set(
        risk[
            "customer_risk_level"
        ]
        .dropna()
        .unique()
    )

    report.add(
        "Risk Level",
        "Risk model contains valid levels",
        risk_levels.issubset(
            valid_levels
        ),
        str(risk_levels)
    )

    # --------------------------------------------------------
    # Explanation consistency
    # --------------------------------------------------------

    risk_lookup = (
        risk[
            [
                "customer_id",
                "customer_risk_level"
            ]
        ]
        .set_index(
            "customer_id"
        )
    )

    explanation_lookup = (
        explanation[
            [
                "customer_id",
                "customer_risk_level"
            ]
        ]
        .set_index(
            "customer_id"
        )
    )

    common_ids = (
        risk_lookup.index
        .intersection(
            explanation_lookup.index
        )
    )

    matching = (
        risk_lookup
        .loc[
            common_ids,
            "customer_risk_level"
        ]
        ==
        explanation_lookup
        .loc[
            common_ids,
            "customer_risk_level"
        ]
    )

    report.add(
        "Risk Level",
        "Explanation risk levels match model",
        matching.all(),
        f"Mismatches: {(~matching).sum()}"
    )


# ============================================================
# EXPLAINABILITY VALIDATION
# ============================================================

def validate_explainability(
    explanation,
    report
):

    print(
        "Validating explainability..."
    )

    required_columns = [

        "primary_risk_driver",

        "dimension_explanation",

        "behavioral_signals",

        "risk_explanation"
    ]

    for column in required_columns:

        exists = (
            column
            in explanation.columns
        )

        report.add(
            "Explainability",
            f"{column} exists",
            exists
        )

        if exists:

            missing = (
                explanation[column]
                .isna()
                .sum()
            )

            report.add(
                "Explainability",
                f"No missing {column}",
                missing == 0,
                f"Missing: {missing}"
            )

    # --------------------------------------------------------
    # Primary driver
    # --------------------------------------------------------

    if (
        "primary_risk_driver"
        in explanation.columns
    ):

        valid_drivers = {
            "SEVERITY",
            "FREQUENCY",
            "PERSISTENCE"
        }

        actual = set(
            explanation[
                "primary_risk_driver"
            ]
            .dropna()
            .unique()
        )

        report.add(
            "Explainability",
            "Primary drivers are valid",
            actual.issubset(
                valid_drivers
            ),
            str(actual)
        )


# ============================================================
# SEGMENTATION VALIDATION
# ============================================================

def validate_segmentation(
    risk,
    segment,
    report
):

    print(
        "Validating customer segmentation..."
    )

    # --------------------------------------------------------
    # Segment column
    # --------------------------------------------------------

    report.add(
        "Segmentation",
        "Risk segment column exists",
        "risk_segment"
        in segment.columns
    )

    report.add(
        "Segmentation",
        "Segment reason column exists",
        "segment_reason"
        in segment.columns
    )

    if (
        "risk_segment"
        not in segment.columns
    ):

        return

    # --------------------------------------------------------
    # No missing segments
    # --------------------------------------------------------

    missing_segments = (
        segment[
            "risk_segment"
        ]
        .isna()
        .sum()
    )

    report.add(
        "Segmentation",
        "No missing risk segments",
        missing_segments == 0,
        f"Missing: {missing_segments}"
    )

    # --------------------------------------------------------
    # Customer conservation
    # --------------------------------------------------------

    report.add(
        "Segmentation",
        "Segment customers conserved",
        len(segment) == len(risk),
        (
            f"Risk={len(risk):,}, "
            f"Segments={len(segment):,}"
        )
    )

    # --------------------------------------------------------
    # Segment percentages
    # --------------------------------------------------------

    counts = (
        segment[
            "risk_segment"
        ]
        .value_counts()
    )

    percentage_total = (
        counts.sum()
        /
        len(segment)
        *
        100
    )

    report.add(
        "Segmentation",
        "All customers assigned to segments",
        np.isclose(
            percentage_total,
            100,
            atol=0.01
        ),
        f"Total percentage: {percentage_total:.2f}%"
    )


# ============================================================
# JOURNEY → CUSTOMER RECONCILIATION
# ============================================================

def validate_journey_customer_reconciliation(
    journey,
    risk,
    report
):

    print(
        "Reconciling journey and customer levels..."
    )

    # --------------------------------------------------------
    # Unique journey customers
    # --------------------------------------------------------

    journey_customers = (
        journey[
            "customer_id"
        ]
        .nunique()
    )

    risk_customers = (
        risk[
            "customer_id"
        ]
        .nunique()
    )

    report.add(
        "Reconciliation",
        "Journey customers represented in risk model",
        journey_customers
        <=
        risk_customers,
        (
            f"Journey={journey_customers:,}, "
            f"Risk={risk_customers:,}"
        )
    )

    # --------------------------------------------------------
    # Missing customers
    # --------------------------------------------------------

    journey_ids = set(
        journey[
            "customer_id"
        ]
    )

    risk_ids = set(
        risk[
            "customer_id"
        ]
    )

    missing = (
        journey_ids
        -
        risk_ids
    )

    report.add(
        "Reconciliation",
        "No journey customers missing from risk model",
        len(missing) == 0,
        f"Missing: {len(missing)}"
    )


# ============================================================
# BEHAVIOR PROFILE VALIDATION
# ============================================================

def validate_behavior_profiles(
    risk,
    report
):

    print(
        "Validating behavior profiles..."
    )

    if (
        "behavior_profile"
        not in risk.columns
    ):

        report.add(
            "Behavior",
            "Behavior profile exists",
            False
        )

        return

    missing = (
        risk[
            "behavior_profile"
        ]
        .isna()
        .sum()
    )

    report.add(
        "Behavior",
        "No missing behavior profiles",
        missing == 0,
        f"Missing: {missing}"
    )

    report.add(
        "Behavior",
        "Behavior profile count valid",
        risk[
            "behavior_profile"
        ]
        .nunique()
        > 0
    )


# ============================================================
# FINAL REPORT
# ============================================================

def print_report(report):

    results = report.dataframe()

    print("\n")
    print("=" * 60)
    print("DAY 5 VALIDATION REPORT")
    print("=" * 60)

    print("\nVALIDATION RESULTS")
    print("-" * 60)

    for _, row in results.iterrows():

        print(
            f"{row['category']} | "
            f"{row['check']}: "
            f"{row['status']}"
        )

        if row["details"]:

            print(
                f"    {row['details']}"
            )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total = len(results)

    passed = (
        results[
            "status"
        ]
        == "PASS"
    ).sum()

    failed = total - passed

    print("\n")
    print("=" * 60)
    print("VALIDATION SUMMARY")
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
        f"Pass rate: "
        f"{(passed / total * 100):.2f}%"
    )

    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    (
        journey,
        risk,
        explanation,
        segment
    ) = load_data()

    # --------------------------------------------------------
    # Validation object
    # --------------------------------------------------------

    report = ValidationReport()

    # --------------------------------------------------------
    # Dataset checks
    # --------------------------------------------------------

    validate_dataset_sizes(
        journey,
        risk,
        explanation,
        segment,
        report
    )

    # --------------------------------------------------------
    # Identity checks
    # --------------------------------------------------------

    validate_customer_ids(
        risk,
        explanation,
        segment,
        report
    )

    # --------------------------------------------------------
    # Risk model
    # --------------------------------------------------------

    validate_risk_scores(
        risk,
        report
    )

    validate_risk_levels(
        risk,
        explanation,
        report
    )

    # --------------------------------------------------------
    # Explainability
    # --------------------------------------------------------

    validate_explainability(
        explanation,
        report
    )

    # --------------------------------------------------------
    # Segmentation
    # --------------------------------------------------------

    validate_segmentation(
        risk,
        segment,
        report
    )

    # --------------------------------------------------------
    # Reconciliation
    # --------------------------------------------------------

    validate_journey_customer_reconciliation(
        journey,
        risk,
        report
    )

    # --------------------------------------------------------
    # Behavior
    # --------------------------------------------------------

    validate_behavior_profiles(
        risk,
        report
    )

    # --------------------------------------------------------
    # Print
    # --------------------------------------------------------

    results = print_report(
        report
    )

    # --------------------------------------------------------
    # Save report
    # --------------------------------------------------------

    results.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    overall = report.passed()

    print("\n")
    print("=" * 60)

    if overall:

        print(
            "DAY 5 END-TO-END VALIDATION: PASSED"
        )

    else:

        print(
            "DAY 5 END-TO-END VALIDATION: FAILED"
        )

    print("=" * 60)

    print(
        "\nValidation report:"
    )

    print(
        OUTPUT_FILE
    )