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
    / "customer_risk_model.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "customer_risk_explanations.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("=" * 60)
    print("CUSTOMER RISK EXPLAINABILITY")
    print("=" * 60)

    print("\nLoading customer risk model...")

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print(
        f"Customers: {len(df):,}"
    )

    return df


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(df):

    numeric_columns = [
        "severity_score",
        "frequency_score",
        "persistence_score",
        "customer_risk_score",
        "total_bookings",
        "total_failed_payments",
        "total_retries",
        "total_anomalies",
        "problematic_journeys",
        "high_risk_journeys",
        "critical_journeys",
        "average_friction_score",
        "maximum_friction_score"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            ).fillna(0)

    return df


# ============================================================
# DIMENSION LABELS
# ============================================================

def severity_label(score):

    if score >= 75:
        return "VERY_HIGH"

    elif score >= 50:
        return "HIGH"

    elif score >= 25:
        return "MODERATE"

    return "LOW"


def frequency_label(score):

    if score >= 30:
        return "HIGH"

    elif score >= 15:
        return "MODERATE"

    elif score > 0:
        return "LOW"

    return "NONE"


def persistence_label(score):

    if score >= 75:
        return "VERY_HIGH"

    elif score >= 50:
        return "HIGH"

    elif score >= 25:
        return "MODERATE"

    elif score > 0:
        return "LOW"

    return "NONE"


# ============================================================
# DIMENSION EXPLANATION
# ============================================================

def build_dimension_explanation(row):

    explanations = []

    severity = float(
        row["severity_score"]
    )

    frequency = float(
        row["frequency_score"]
    )

    persistence = float(
        row["persistence_score"]
    )

    # --------------------------------------------------------
    # Severity
    # --------------------------------------------------------

    if severity >= 75:

        explanations.append(
            f"Very high journey severity "
            f"(score {severity:.2f})"
        )

    elif severity >= 50:

        explanations.append(
            f"High journey severity "
            f"(score {severity:.2f})"
        )

    elif severity >= 25:

        explanations.append(
            f"Moderate journey severity "
            f"(score {severity:.2f})"
        )

    else:

        explanations.append(
            f"Low journey severity "
            f"(score {severity:.2f})"
        )

    # --------------------------------------------------------
    # Frequency
    # --------------------------------------------------------

    if frequency >= 30:

        explanations.append(
            f"High problematic activity frequency "
            f"(score {frequency:.2f})"
        )

    elif frequency >= 15:

        explanations.append(
            f"Moderate problematic activity frequency "
            f"(score {frequency:.2f})"
        )

    elif frequency > 0:

        explanations.append(
            f"Low problematic activity frequency "
            f"(score {frequency:.2f})"
        )

    else:

        explanations.append(
            "No problematic activity frequency"
        )

    # --------------------------------------------------------
    # Persistence
    # --------------------------------------------------------

    if persistence >= 75:

        explanations.append(
            f"Very persistent problematic behavior "
            f"(score {persistence:.2f})"
        )

    elif persistence >= 50:

        explanations.append(
            f"Persistent problematic behavior "
            f"(score {persistence:.2f})"
        )

    elif persistence >= 25:

        explanations.append(
            f"Moderate persistence of problematic behavior "
            f"(score {persistence:.2f})"
        )

    elif persistence > 0:

        explanations.append(
            f"Limited persistence of problematic behavior "
            f"(score {persistence:.2f})"
        )

    else:

        explanations.append(
            "No persistent problematic behavior"
        )

    # --------------------------------------------------------
    # Safety fallback
    # --------------------------------------------------------

    if not explanations:

        explanations.append(
            "No major risk dimension signals identified"
        )

    return explanations


# ============================================================
# BEHAVIORAL SIGNALS
# ============================================================

def build_behavioral_signals(row):

    signals = []

    failed = int(
        row["total_failed_payments"]
    )

    retries = int(
        row["total_retries"]
    )

    anomalies = int(
        row["total_anomalies"]
    )

    problematic = int(
        row["problematic_journeys"]
    )

    critical = int(
        row["critical_journeys"]
    )

    # --------------------------------------------------------
    # Failed payments
    # --------------------------------------------------------

    if failed > 0:

        signals.append(
            f"{failed} failed payment attempts"
        )

    # --------------------------------------------------------
    # Retries
    # --------------------------------------------------------

    if retries > 0:

        signals.append(
            f"{retries} payment retries"
        )

    # --------------------------------------------------------
    # Anomalies
    # --------------------------------------------------------

    if anomalies > 0:

        if anomalies == 1:

            signals.append(
                "1 detected journey anomaly"
            )

        else:

            signals.append(
                f"{anomalies} detected journey anomalies"
            )

    # --------------------------------------------------------
    # Problematic journeys
    # --------------------------------------------------------

    if problematic > 0:

        if problematic == 1:

            signals.append(
                "1 problematic journey"
            )

        else:

            signals.append(
                f"{problematic} problematic journeys"
            )

    # --------------------------------------------------------
    # Critical journeys
    # --------------------------------------------------------

    if critical > 0:

        signals.append(
            f"{critical} critical journey(s)"
        )

    # --------------------------------------------------------
    # No signals
    # --------------------------------------------------------

    if not signals:

        return ["No major behavioral risk signals"]

    return signals


# ============================================================
# PRIMARY RISK DRIVER
# ============================================================

def identify_primary_driver(row):

    dimensions = {

        "SEVERITY": float(
            row["severity_score"]
        ),

        "FREQUENCY": float(
            row["frequency_score"]
        ),

        "PERSISTENCE": float(
            row["persistence_score"]
        )
    }

    primary = max(
        dimensions,
        key=dimensions.get
    )

    return primary


# ============================================================
# FINAL RISK EXPLANATION
# ============================================================

def build_explanation_summary(row):

    risk_level = row[
        "customer_risk_level"
    ]

    score = float(
        row["customer_risk_score"]
    )

    primary = row[
        "primary_risk_driver"
    ]

    severity = float(
        row["severity_score"]
    )

    frequency = float(
        row["frequency_score"]
    )

    persistence = float(
        row["persistence_score"]
    )

    behavioral_signals = row[
        "behavioral_signals"
    ]

    if pd.isna(
        behavioral_signals
    ):

        behavioral_signals = (
            "No major behavioral risk signals"
        )

    return (
        f"Customer classified as {risk_level} "
        f"with a risk score of {score:.2f}. "
        f"Primary risk dimension: {primary}. "
        f"Severity={severity:.2f}, "
        f"Frequency={frequency:.2f}, "
        f"Persistence={persistence:.2f}. "
        f"{behavioral_signals}"
    )


# ============================================================
# BUILD EXPLANATIONS
# ============================================================

def build_explanations(df):

    print(
        "\nBuilding risk explanations..."
    )

    # --------------------------------------------------------
    # Dimension levels
    # --------------------------------------------------------

    df["severity_level"] = (
        df["severity_score"]
        .apply(
            severity_label
        )
    )

    df["frequency_level"] = (
        df["frequency_score"]
        .apply(
            frequency_label
        )
    )

    df["persistence_level"] = (
        df["persistence_score"]
        .apply(
            persistence_label
        )
    )

    # --------------------------------------------------------
    # Primary driver
    # --------------------------------------------------------

    df["primary_risk_driver"] = (
        df.apply(
            identify_primary_driver,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Dimension explanation
    # --------------------------------------------------------

    df["dimension_explanation"] = (
        df.apply(
            lambda row:
            " | ".join(
                build_dimension_explanation(
                    row
                )
            ),
            axis=1
        )
    )

    # --------------------------------------------------------
    # Behavioral signals
    # --------------------------------------------------------

    df["behavioral_signals"] = (
        df.apply(
            lambda row:
            " | ".join(
                build_behavioral_signals(
                    row
                )
            ),
            axis=1
        )
    )

    # --------------------------------------------------------
    # Final explanation
    # --------------------------------------------------------

    df["risk_explanation"] = (
        df.apply(
            build_explanation_summary,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Final safety cleanup
    # --------------------------------------------------------

    df["dimension_explanation"] = (
        df["dimension_explanation"]
        .fillna(
            "No major risk dimension signals identified"
        )
    )

    df["behavioral_signals"] = (
        df["behavioral_signals"]
        .fillna(
            "No major behavioral risk signals"
        )
    )

    df["risk_explanation"] = (
        df["risk_explanation"]
        .fillna(
            "Risk explanation unavailable"
        )
    )

    return df


# ============================================================
# PRIMARY DRIVER ANALYSIS
# ============================================================

def analyze_primary_drivers(df):

    print(
        "\nPRIMARY RISK DRIVER DISTRIBUTION"
    )

    print("-" * 40)

    print(
        df[
            "primary_risk_driver"
        ]
        .value_counts()
    )

    print(
        "\nPRIMARY DRIVER BY RISK LEVEL"
    )

    print("-" * 40)

    table = pd.crosstab(

        df[
            "customer_risk_level"
        ],

        df[
            "primary_risk_driver"
        ]
    )

    print(
        table.to_string()
    )


# ============================================================
# EXAMPLE EXPLANATIONS
# ============================================================

def print_examples(df):

    print(
        "\n"
    )

    print(
        "=" * 60
    )

    print(
        "EXAMPLE CUSTOMER EXPLANATIONS"
    )

    print(
        "=" * 60
    )

    top = (
        df
        .sort_values(
            "customer_risk_score",
            ascending=False
        )
        .head(3)
    )

    for _, row in top.iterrows():

        print(
            "\n"
            + "-" * 60
        )

        print(
            f"Customer: "
            f"{row['customer_id']}"
        )

        print(
            f"Name: "
            f"{row['first_name']} "
            f"{row['last_name']}"
        )

        print(
            f"Risk Score: "
            f"{row['customer_risk_score']:.2f}"
        )

        print(
            f"Risk Level: "
            f"{row['customer_risk_level']}"
        )

        print(
            f"Primary Driver: "
            f"{row['primary_risk_driver']}"
        )

        print(
            f"Severity: "
            f"{row['severity_score']:.2f} "
            f"({row['severity_level']})"
        )

        print(
            f"Frequency: "
            f"{row['frequency_score']:.2f} "
            f"({row['frequency_level']})"
        )

        print(
            f"Persistence: "
            f"{row['persistence_score']:.2f} "
            f"({row['persistence_level']})"
        )

        print(
            "Signals:"
        )

        print(
            f"  {row['behavioral_signals']}"
        )

        print(
            "Dimension Explanation:"
        )

        print(
            f"  {row['dimension_explanation']}"
        )

        print(
            "Risk Explanation:"
        )

        print(
            f"  {row['risk_explanation']}"
        )


# ============================================================
# VALIDATION
# ============================================================

def validate_explainability(df):

    print(
        "\n"
    )

    print(
        "=" * 60
    )

    print(
        "RISK EXPLAINABILITY VALIDATION"
    )

    print(
        "=" * 60
    )

    checks = {}

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = [

        "severity_level",

        "frequency_level",

        "persistence_level",

        "primary_risk_driver",

        "dimension_explanation",

        "behavioral_signals",

        "risk_explanation"
    ]

    for column in required_columns:

        checks[
            f"{column} exists"
        ] = (
            column in df.columns
        )

    # --------------------------------------------------------
    # No missing explanations
    # --------------------------------------------------------

    checks[
        "No missing dimension explanations"
    ] = (
        df[
            "dimension_explanation"
        ]
        .notna()
        .all()
    )

    checks[
        "No missing behavioral signals"
    ] = (
        df[
            "behavioral_signals"
        ]
        .notna()
        .all()
    )

    checks[
        "No missing risk explanations"
    ] = (
        df[
            "risk_explanation"
        ]
        .notna()
        .all()
    )

    # --------------------------------------------------------
    # No empty strings
    # --------------------------------------------------------

    checks[
        "No empty dimension explanations"
    ] = (
        df[
            "dimension_explanation"
        ]
        .astype(str)
        .str.strip()
        .ne("")
        .all()
    )

    checks[
        "No empty risk explanations"
    ] = (
        df[
            "risk_explanation"
        ]
        .astype(str)
        .str.strip()
        .ne("")
        .all()
    )

    # --------------------------------------------------------
    # Primary driver
    # --------------------------------------------------------

    valid_drivers = {
        "SEVERITY",
        "FREQUENCY",
        "PERSISTENCE"
    }

    checks[
        "Valid primary drivers"
    ] = (
        df[
            "primary_risk_driver"
        ]
        .isin(
            valid_drivers
        )
        .all()
    )

    # --------------------------------------------------------
    # Risk levels
    # --------------------------------------------------------

    valid_risk_levels = {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    }

    checks[
        "Valid customer risk levels"
    ] = (
        df[
            "customer_risk_level"
        ]
        .isin(
            valid_risk_levels
        )
        .all()
    )

    # --------------------------------------------------------
    # Score ranges
    # --------------------------------------------------------

    checks[
        "Severity scores valid"
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
        "Frequency scores valid"
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
        "Persistence scores valid"
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

    overall = all(
        checks.values()
    )

    print(
        "\nOverall validation:",
        "PASSED"
        if overall
        else "FAILED"
    )

    return overall


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = load_data()

    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    df = prepare_data(
        df
    )

    # --------------------------------------------------------
    # Build explanations
    # --------------------------------------------------------

    df = build_explanations(
        df
    )

    # --------------------------------------------------------
    # Driver analysis
    # --------------------------------------------------------

    analyze_primary_drivers(
        df
    )

    # --------------------------------------------------------
    # Examples
    # --------------------------------------------------------

    print_examples(
        df
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    validation_passed = (
        validate_explainability(
            df
        )
    )

    # --------------------------------------------------------
    # Output columns
    # --------------------------------------------------------

    output_columns = [

        "customer_id",

        "first_name",

        "last_name",

        "country",

        "customer_segment",

        "total_bookings",

        "total_failed_payments",

        "total_retries",

        "total_anomalies",

        "problematic_journeys",

        "severity_score",

        "severity_level",

        "frequency_score",

        "frequency_level",

        "persistence_score",

        "persistence_level",

        "customer_risk_score",

        "customer_risk_level",

        "behavior_profile",

        "primary_risk_driver",

        "dimension_explanation",

        "behavioral_signals",

        "research_risk_signals",

        "risk_explanation"
    ]

    output_columns = [
        column
        for column in output_columns
        if column in df.columns
    ]

    output_df = df[
        output_columns
    ].copy()

    # --------------------------------------------------------
    # Final output safety checks
    # --------------------------------------------------------

    for column in [
        "dimension_explanation",
        "behavioral_signals",
        "risk_explanation"
    ]:

        if column in output_df.columns:

            output_df[column] = (
                output_df[column]
                .fillna("")
                .astype(str)
            )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    print(
        "\n"
    )

    print(
        "=" * 60
    )

    if validation_passed:

        print(
            "RISK EXPLAINABILITY SUCCESS"
        )

    else:

        print(
            "RISK EXPLAINABILITY FAILED"
        )

    print(
        "=" * 60
    )

    print(
        "\nOutput file:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nRecords:",
        f"{len(output_df):,}"
    )

    print(
        "Features:",
        f"{len(output_df.columns):,}"
    )