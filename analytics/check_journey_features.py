import os
import sys
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

FEATURE_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "customer_journey_features.csv"
)

RAW_DIR = os.path.join(
    BASE_DIR,
    "data",
    "raw"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "day3_validation_report.csv"
)


# ============================================================
# EXPECTED VALUES
# ============================================================

EXPECTED_JOURNEY_RECORDS = 8000


# ============================================================
# VALIDATION STORAGE
# ============================================================

results = []


def check(name, condition, detail=""):
    """
    Record and print a validation check.
    """

    status = "PASS" if condition else "FAIL"

    results.append(
        {
            "check": name,
            "status": status,
            "detail": detail
        }
    )

    print(f"{name}: {status}")

    if detail:
        print(f"    {detail}")


# ============================================================
# HELPER
# ============================================================

def load_csv(path):
    """
    Safely load CSV.
    """

    if not os.path.isfile(path):
        return None

    try:
        return pd.read_csv(path)
    except Exception:
        return None


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 3 JOURNEY FEATURE ENGINEERING VALIDATION")
    print("=" * 60)

    print()
    print("Loading journey feature dataset...")
    print()

    # ========================================================
    # CHECK 1 — FEATURE FILE EXISTS
    # ========================================================

    check(
        "Journey feature dataset exists",
        os.path.isfile(FEATURE_FILE),
        FEATURE_FILE
    )

    if not os.path.isfile(FEATURE_FILE):

        print()
        print("=" * 60)
        print("DAY 3 VALIDATION FAILED")
        print("=" * 60)

        return 1

    # ========================================================
    # LOAD FEATURE DATA
    # ========================================================

    try:

        features = pd.read_csv(
            FEATURE_FILE
        )

    except Exception as exc:

        check(
            "Journey feature dataset can be loaded",
            False,
            str(exc)
        )

        return 1

    check(
        "Journey feature dataset can be loaded",
        True,
        f"{len(features):,} records"
    )

    # ========================================================
    # BASIC DATASET CHECKS
    # ========================================================

    print()
    print("Validating dataset structure...")

    # --------------------------------------------------------
    # CHECK 2 — ROW COUNT
    # --------------------------------------------------------

    check(
        "Journey record count",
        len(features) == EXPECTED_JOURNEY_RECORDS,
        (
            f"Expected {EXPECTED_JOURNEY_RECORDS:,}, "
            f"found {len(features):,}"
        )
    )

    # --------------------------------------------------------
    # CHECK 3 — BOOKING ID
    # --------------------------------------------------------

    check(
        "booking_id column exists",
        "booking_id" in features.columns
    )

    if "booking_id" in features.columns:

        unique_bookings = (
            features["booking_id"]
            .nunique(dropna=True)
        )

        duplicate_bookings = (
            features["booking_id"]
            .duplicated()
            .sum()
        )

        check(
            "One row per booking",
            (
                unique_bookings == len(features)
                and duplicate_bookings == 0
            ),
            (
                f"Rows={len(features):,}, "
                f"unique bookings={unique_bookings:,}, "
                f"duplicates={duplicate_bookings}"
            )
        )

        check(
            "No missing booking IDs",
            features["booking_id"].notna().all(),
            f"Missing={features['booking_id'].isna().sum()}"
        )

    # --------------------------------------------------------
    # CHECK 4 — CUSTOMER ID
    # --------------------------------------------------------

    check(
        "customer_id column exists",
        "customer_id" in features.columns
    )

    if "customer_id" in features.columns:

        check(
            "No missing customer IDs",
            features["customer_id"].notna().all(),
            f"Missing={features['customer_id'].isna().sum()}"
        )

    # ========================================================
    # REQUIRED PAYMENT FEATURES
    # ========================================================

    print()
    print("Validating payment features...")

    required_payment_features = [
        "payment_attempts",
        "failed_payments",
        "successful_payments",
        "retry_count",
        "payment_success_rate",
        "payment_duration_minutes",
    ]

    for column in required_payment_features:

        check(
            f"Payment feature | {column}",
            column in features.columns
        )

    # ========================================================
    # REQUIRED EVENT FEATURES
    # ========================================================

    print()
    print("Validating event features...")

    required_event_features = [
        "total_events",
        "search_events",
        "view_trip_events",
        "booking_started_events",
        "booking_created_events",
        "payment_started_events",
        "payment_failed_events",
        "payment_retry_events",
        "payment_completed_events",
        "booking_confirmed_events",
        "journey_duration_minutes",
    ]

    for column in required_event_features:

        check(
            f"Event feature | {column}",
            column in features.columns
        )

    # ========================================================
    # BOOKING FEATURES
    # ========================================================

    print()
    print("Validating booking features...")

    required_booking_features = [
        "booking_status",
        "booking_amount",
        "trip_id",
    ]

    for column in required_booking_features:

        check(
            f"Booking feature | {column}",
            column in features.columns
        )

    # ========================================================
    # PAYMENT METRIC VALIDATION
    # ========================================================

    print()
    print("Validating payment metrics...")

    payment_columns_present = all(
        column in features.columns
        for column in required_payment_features
    )

    if payment_columns_present:

        # ----------------------------------------------------
        # PAYMENT ATTEMPTS
        # ----------------------------------------------------

        attempts_valid = (
            pd.to_numeric(
                features["payment_attempts"],
                errors="coerce"
            )
            .fillna(-1)
            .ge(0)
            .all()
        )

        check(
            "Payment attempts are non-negative",
            attempts_valid
        )

        # ----------------------------------------------------
        # FAILED PAYMENTS
        # ----------------------------------------------------

        failed_valid = (
            pd.to_numeric(
                features["failed_payments"],
                errors="coerce"
            )
            .fillna(-1)
            .ge(0)
            .all()
        )

        check(
            "Failed payments are non-negative",
            failed_valid
        )

        # ----------------------------------------------------
        # SUCCESSFUL PAYMENTS
        # ----------------------------------------------------

        success_valid = (
            pd.to_numeric(
                features["successful_payments"],
                errors="coerce"
            )
            .fillna(-1)
            .ge(0)
            .all()
        )

        check(
            "Successful payments are non-negative",
            success_valid
        )

        # ----------------------------------------------------
        # RETRIES
        # ----------------------------------------------------

        retry_valid = (
            pd.to_numeric(
                features["retry_count"],
                errors="coerce"
            )
            .fillna(-1)
            .ge(0)
            .all()
        )

        check(
            "Retry counts are non-negative",
            retry_valid
        )

        # ----------------------------------------------------
        # ATTEMPT RECONCILIATION
        # ----------------------------------------------------

        attempts = pd.to_numeric(
            features["payment_attempts"],
            errors="coerce"
        )

        failed = pd.to_numeric(
            features["failed_payments"],
            errors="coerce"
        )

        successful = pd.to_numeric(
            features["successful_payments"],
            errors="coerce"
        )

        reconciliation = (
            attempts == (
                failed + successful
            )
        )

        check(
            "Payment attempts reconcile",
            bool(reconciliation.all()),
            f"Invalid rows={int((~reconciliation).sum())}"
        )

        # ----------------------------------------------------
        # RETRY RECONCILIATION
        # ----------------------------------------------------

        retry_reconciliation = (
            pd.to_numeric(
                features["retry_count"],
                errors="coerce"
            )
            == (attempts - 1).clip(lower=0)
        )

        check(
            "Retry counts reconcile with attempts",
            bool(retry_reconciliation.all()),
            (
                f"Invalid rows="
                f"{int((~retry_reconciliation).sum())}"
            )
        )

        # ----------------------------------------------------
        # SUCCESS RATE
        # ----------------------------------------------------

        success_rate = pd.to_numeric(
            features["payment_success_rate"],
            errors="coerce"
        )

        success_rate_valid = (
            success_rate.notna()
            & success_rate.between(0, 1)
        )

        # Some implementations store the rate as
        # percentage rather than decimal.
        # Detect both safely.

        if success_rate.max() > 1:

            success_rate_valid = (
                success_rate.notna()
                & success_rate.between(0, 100)
            )

        check(
            "Payment success rate is valid",
            bool(success_rate_valid.all()),
            (
                f"min={success_rate.min():.3f}, "
                f"max={success_rate.max():.3f}"
            )
        )

        # ----------------------------------------------------
        # PAYMENT DURATION
        # ----------------------------------------------------

        payment_duration = pd.to_numeric(
            features["payment_duration_minutes"],
            errors="coerce"
        )

        payment_duration_valid = (
            payment_duration.notna()
            & payment_duration.ge(0)
        )

        check(
            "Payment duration is non-negative",
            bool(payment_duration_valid.all()),
            (
                f"min={payment_duration.min():.2f}, "
                f"max={payment_duration.max():.2f}"
            )
        )

    # ========================================================
    # EVENT METRIC VALIDATION
    # ========================================================

    print()
    print("Validating event metrics...")

    event_columns_present = all(
        column in features.columns
        for column in required_event_features
    )

    if event_columns_present:

        event_columns = [
            "search_events",
            "view_trip_events",
            "booking_started_events",
            "booking_created_events",
            "payment_started_events",
            "payment_failed_events",
            "payment_retry_events",
            "payment_completed_events",
            "booking_confirmed_events",
        ]

        event_values_valid = True

        invalid_total = 0

        for column in event_columns:

            values = pd.to_numeric(
                features[column],
                errors="coerce"
            )

            invalid = (
                values.isna()
                | values.lt(0)
            )

            invalid_total += int(
                invalid.sum()
            )

            if invalid.any():
                event_values_valid = False

        check(
            "Event counts are non-negative",
            event_values_valid,
            f"Invalid values={invalid_total}"
        )

        total_events = pd.to_numeric(
            features["total_events"],
            errors="coerce"
        )

        total_event_components = (
            sum(
                pd.to_numeric(
                    features[column],
                    errors="coerce"
                )
                for column in event_columns
            )
        )

        event_reconciliation = (
            total_events
            == total_event_components
        )

        check(
            "Total events reconcile",
            bool(event_reconciliation.all()),
            (
                f"Invalid rows="
                f"{int((~event_reconciliation).sum())}"
            )
        )

        # ----------------------------------------------------
        # JOURNEY DURATION
        # ----------------------------------------------------

        journey_duration = pd.to_numeric(
            features["journey_duration_minutes"],
            errors="coerce"
        )

        journey_duration_valid = (
            journey_duration.notna()
            & journey_duration.ge(0)
        )

        check(
            "Journey duration is non-negative",
            bool(journey_duration_valid.all()),
            (
                f"min={journey_duration.min():.2f}, "
                f"max={journey_duration.max():.2f}"
            )
        )

    # ========================================================
    # FRICTION SCORE
    # ========================================================

    print()
    print("Validating friction scoring...")

    friction_column = "friction_score"

    check(
        "friction_score column exists",
        friction_column in features.columns
    )

    if friction_column in features.columns:

        friction = pd.to_numeric(
            features[friction_column],
            errors="coerce"
        )

        friction_valid = (
            friction.notna()
            & friction.between(0, 100)
        )

        check(
            "Friction score range 0-100",
            bool(friction_valid.all()),
            (
                f"min={friction.min():.2f}, "
                f"max={friction.max():.2f}"
            )
        )

        check(
            "No missing friction scores",
            friction.notna().all(),
            f"Missing={friction.isna().sum()}"
        )

    # ========================================================
    # RISK LEVEL
    # ========================================================

    print()
    print("Validating risk levels...")

    risk_column = "risk_level"

    check(
        "risk_level column exists",
        risk_column in features.columns
    )

    if risk_column in features.columns:

        valid_risk_levels = {
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        }

        actual_levels = set(
            features[risk_column]
            .dropna()
            .astype(str)
            .str.upper()
        )

        invalid_levels = (
            actual_levels
            - valid_risk_levels
        )

        check(
            "Risk levels are valid",
            len(invalid_levels) == 0,
            (
                f"Levels={sorted(actual_levels)}"
                if not invalid_levels
                else f"Invalid={sorted(invalid_levels)}"
            )
        )

        check(
            "No missing risk levels",
            features[risk_column].notna().all(),
            f"Missing={features[risk_column].isna().sum()}"
        )

    # ========================================================
    # ANOMALY FEATURES
    # ========================================================

    print()
    print("Validating anomaly detection...")

    anomaly_columns = [
        "anomaly_summary",
    ]

    for column in anomaly_columns:

        check(
            f"Anomaly feature | {column}",
            column in features.columns
        )

    if "anomaly_summary" in features.columns:

        check(
            "No missing anomaly summaries",
            features["anomaly_summary"].notna().all(),
            f"Missing={features['anomaly_summary'].isna().sum()}"
        )

    # ========================================================
    # REQUIRED DATA COMPLETENESS
    # ========================================================

    print()
    print("Validating critical fields...")

    critical_columns = [
        "customer_id",
        "booking_id",
        "trip_id",
        "booking_status",
        "booking_amount",
        "payment_attempts",
        "failed_payments",
        "successful_payments",
        "retry_count",
        "total_events",
        "friction_score",
        "risk_level",
        "anomaly_summary",
    ]

    existing_critical_columns = [
        column
        for column in critical_columns
        if column in features.columns
    ]

    missing_critical_values = (
        features[
            existing_critical_columns
        ]
        .isna()
        .sum()
        .sum()
    )

    check(
        "No missing critical feature values",
        missing_critical_values == 0,
        f"Missing={missing_critical_values}"
    )

    # ========================================================
    # RAW DATA RECONCILIATION
    # ========================================================

    print()
    print("Reconciling against raw datasets...")

    raw_bookings_file = os.path.join(
        RAW_DIR,
        "bookings.csv"
    )

    raw_events_file = os.path.join(
        RAW_DIR,
        "events.csv"
    )

    raw_payments_file = os.path.join(
        RAW_DIR,
        "payments.csv"
    )

    raw_bookings = load_csv(
        raw_bookings_file
    )

    raw_events = load_csv(
        raw_events_file
    )

    raw_payments = load_csv(
        raw_payments_file
    )

    # --------------------------------------------------------
    # BOOKING RECONCILIATION
    # --------------------------------------------------------

    if raw_bookings is not None:

        check(
            "Raw booking count matches feature records",
            len(raw_bookings) == len(features),
            (
                f"Raw bookings={len(raw_bookings):,}, "
                f"Features={len(features):,}"
            )
        )

        if (
            "booking_id" in raw_bookings.columns
            and "booking_id" in features.columns
        ):

            raw_booking_ids = set(
                raw_bookings["booking_id"]
                .dropna()
                .astype(str)
            )

            feature_booking_ids = set(
                features["booking_id"]
                .dropna()
                .astype(str)
            )

            check(
                "All raw bookings represented",
                raw_booking_ids == feature_booking_ids,
                (
                    f"Missing="
                    f"{len(raw_booking_ids - feature_booking_ids)}, "
                    f"Extra="
                    f"{len(feature_booking_ids - raw_booking_ids)}"
                )
            )

    # --------------------------------------------------------
    # EVENT RECONCILIATION
    # --------------------------------------------------------

    if raw_events is not None:

        raw_event_count = len(
            raw_events
        )

        feature_event_count = pd.to_numeric(
            features["total_events"],
            errors="coerce"
        ).sum()

        check(
            "Total events reconcile with raw events",
            int(feature_event_count)
            == raw_event_count,
            (
                f"Raw events={raw_event_count:,}, "
                f"Feature events={int(feature_event_count):,}"
            )
        )

    # --------------------------------------------------------
    # PAYMENT RECONCILIATION
    # --------------------------------------------------------

    if raw_payments is not None:

        raw_payment_count = len(
            raw_payments
        )

        feature_payment_count = pd.to_numeric(
            features["payment_attempts"],
            errors="coerce"
        ).sum()

        check(
            "Total payment attempts reconcile with raw payments",
            int(feature_payment_count)
            == raw_payment_count,
            (
                f"Raw payments={raw_payment_count:,}, "
                f"Feature attempts={int(feature_payment_count):,}"
            )
        )

    # ========================================================
    # DUPLICATE CHECK
    # ========================================================

    print()
    print("Validating uniqueness...")

    if "booking_id" in features.columns:

        duplicate_count = int(
            features["booking_id"]
            .duplicated()
            .sum()
        )

        check(
            "No duplicate journey records",
            duplicate_count == 0,
            f"Duplicates={duplicate_count}"
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

    total_checks = len(
        validation_df
    )

    passed_checks = int(
        (
            validation_df["status"]
            == "PASS"
        ).sum()
    )

    failed_checks = int(
        (
            validation_df["status"]
            == "FAIL"
        ).sum()
    )

    pass_rate = round(
        (
            passed_checks
            / total_checks
        ) * 100,
        2
    ) if total_checks else 0

    print()
    print()
    print("=" * 60)
    print("DAY 3 VALIDATION SUMMARY")
    print("=" * 60)

    print(
        f"Total checks: {total_checks}"
    )

    print(
        f"Passed: {passed_checks}"
    )

    print(
        f"Failed: {failed_checks}"
    )

    print(
        f"Pass rate: {pass_rate:.2f}%"
    )

    print()

    if failed_checks == 0:

        print("=" * 60)
        print("DAY 3 JOURNEY FEATURE ENGINEERING: PASSED")
        print("=" * 60)

        print()
        print(
            "Journey-level feature engineering "
            "is validated successfully."
        )

        print()
        print("Validation report:")
        print(OUTPUT_FILE)

        return 0

    else:

        print("=" * 60)
        print("DAY 3 JOURNEY FEATURE ENGINEERING: FAILED")
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
        print("Validation report:")
        print(OUTPUT_FILE)

        return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )