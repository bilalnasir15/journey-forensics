from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field


# ============================================================
# STATISTICAL EVIDENCE
# ============================================================

class StatisticalEvidence(BaseModel):

    metric: str

    record_count: int | None = None

    threshold: float | None = None

    flagged_count: int | None = None

    flagged_rate: float | None = None

    raw_result: dict[str, Any] = Field(
        default_factory=dict
    )

    source: str = "/investigate"


# ============================================================
# STATISTICAL TOOL
# ============================================================

class StatisticalTool:

    def __init__(
        self,
        tool_executor,
    ) -> None:

        self.tool_executor = tool_executor

    # ========================================================
    # RUN
    # ========================================================

    def run(
        self,
        metric: str,
        threshold: float | None = None,
    ) -> StatisticalEvidence:

        parameters: dict[str, Any] = {
            "metric": metric,
        }

        if threshold is not None:
            parameters["threshold"] = threshold

        result = self.tool_executor.execute(
            "run_statistical_analysis",
            parameters,
        )

        if result.status.value != "SUCCESS":

            raise RuntimeError(
                result.error
                or (
                    "Statistical tool did not "
                    "return a successful result."
                )
            )

        return self.normalize_result(
            metric=metric,
            payload=result.data,
            threshold=threshold,
        )

    # ========================================================
    # NORMALIZE RESULT
    # ========================================================

    @classmethod
    def normalize_result(
        cls,
        metric: str,
        payload: dict[str, Any],
        threshold: float | None = None,
    ) -> StatisticalEvidence:

        if not isinstance(
            payload,
            dict,
        ):

            raise TypeError(
                "Statistical payload must be a dictionary."
            )

        # ----------------------------------------------------
        # Metric
        # ----------------------------------------------------

        returned_metric = (
            cls._find_value(
                payload,
                cls.METRIC_KEYS,
            )
            or metric
        )

        # ----------------------------------------------------
        # Record count
        # ----------------------------------------------------

        record_count = cls._find_integer(
            payload,
            cls.RECORD_COUNT_KEYS,
        )

        # ----------------------------------------------------
        # Threshold
        # ----------------------------------------------------

        returned_threshold = cls._find_float(
            payload,
            cls.THRESHOLD_KEYS,
        )

        if returned_threshold is None:

            returned_threshold = threshold

        # ----------------------------------------------------
        # Flagged count
        # ----------------------------------------------------

        flagged_count = cls._find_integer(
            payload,
            cls.FLAGGED_COUNT_KEYS,
        )

        # ----------------------------------------------------
        # Flagged rate
        # ----------------------------------------------------

        flagged_rate = cls._find_float(
            payload,
            cls.FLAGGED_RATE_KEYS,
        )

        # ----------------------------------------------------
        # Handle list-based flagged output
        # ----------------------------------------------------

        if flagged_count is None:

            flagged_items = cls._find_value(
                payload,
                cls.FLAGGED_LIST_KEYS,
            )

            if isinstance(
                flagged_items,
                list,
            ):

                flagged_count = len(
                    flagged_items
                )

        # ----------------------------------------------------
        # Derive rate from counts
        # ----------------------------------------------------

        if (
            flagged_rate is None
            and record_count is not None
            and flagged_count is not None
            and record_count > 0
        ):

            flagged_rate = (
                flagged_count
                / record_count
                * 100.0
            )

        return StatisticalEvidence(
            metric=str(
                returned_metric
            ),
            record_count=record_count,
            threshold=returned_threshold,
            flagged_count=flagged_count,
            flagged_rate=(
                round(
                    flagged_rate,
                    4,
                )
                if flagged_rate is not None
                else None
            ),
            raw_result=dict(
                payload
            ),
            source="/investigate",
        )

    # ========================================================
    # KEY DEFINITIONS
    # ========================================================

    METRIC_KEYS = (
        "metric",
        "metric_name",
        "name",
        "measure",
    )

    RECORD_COUNT_KEYS = (
        "record_count",
        "records_count",
        "total_records",
        "record_total",
        "records",
        "count",
        "population",
        "population_count",
        "source_count",
        "evaluated_count",
        "rows",
        "row_count",
        "total_rows",
        "rows_evaluated",
        "records_evaluated",
    )

    THRESHOLD_KEYS = (
        "threshold",
        "cutoff",
        "cut_off",
        "limit",
        "threshold_value",
    )

    FLAGGED_COUNT_KEYS = (
        "flagged_count",
        "flagged_records",
        "records_flagged",
        "flagged_rows",
        "rows_flagged",
        "anomaly_count",
        "anomalies_count",
        "outlier_count",
        "outliers_count",
        "matched_count",
        "matching_count",
        "violations",
        "violations_count",
    )

    FLAGGED_RATE_KEYS = (
        "flagged_rate",
        "flagged_percentage",
        "flagged_percent",
        "anomaly_rate",
        "anomaly_percentage",
        "outlier_rate",
        "violation_rate",
    )

    FLAGGED_LIST_KEYS = (
        "flagged",
        "flagged_items",
        "flagged_records_list",
        "anomalies",
        "anomaly_records",
        "outliers",
        "violations_list",
    )

    # ========================================================
    # RECURSIVE VALUE FINDER
    # ========================================================

    @classmethod
    def _find_value(
        cls,
        payload: Any,
        target_keys: tuple[str, ...],
    ) -> Any:

        normalized_targets = {
            cls._normalize_key(
                key
            )
            for key
            in target_keys
        }

        return cls._find_value_recursive(
            payload,
            normalized_targets,
        )

    # ========================================================
    # RECURSIVE SEARCH
    # ========================================================

    @classmethod
    def _find_value_recursive(
        cls,
        payload: Any,
        normalized_targets: set[str],
    ) -> Any:

        if isinstance(
            payload,
            dict,
        ):

            # -----------------------------------------------
            # First inspect current level.
            # -----------------------------------------------

            for key, value in payload.items():

                normalized_key = (
                    cls._normalize_key(
                        str(key)
                    )
                )

                if normalized_key in normalized_targets:

                    return value

            # -----------------------------------------------
            # Then recursively inspect children.
            # -----------------------------------------------

            for value in payload.values():

                found = (
                    cls._find_value_recursive(
                        value,
                        normalized_targets,
                    )
                )

                if found is not None:

                    return found

            return None

        if isinstance(
            payload,
            list,
        ):

            for item in payload:

                found = (
                    cls._find_value_recursive(
                        item,
                        normalized_targets,
                    )
                )

                if found is not None:

                    return found

            return None

        return None

    # ========================================================
    # INTEGER SEARCH
    # ========================================================

    @classmethod
    def _find_integer(
        cls,
        payload: Any,
        keys: tuple[str, ...],
    ) -> int | None:

        value = cls._find_value(
            payload,
            keys,
        )

        if value is None:

            return None

        try:

            # Boolean is technically int-like but should
            # never be treated as a record count.
            if isinstance(
                value,
                bool,
            ):

                return None

            return int(
                float(
                    value
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    # ========================================================
    # FLOAT SEARCH
    # ========================================================

    @classmethod
    def _find_float(
        cls,
        payload: Any,
        keys: tuple[str, ...],
    ) -> float | None:

        value = cls._find_value(
            payload,
            keys,
        )

        if value is None:

            return None

        try:

            if isinstance(
                value,
                bool,
            ):

                return None

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    # ========================================================
    # KEY NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_key(
        value: str,
    ) -> str:

        value = value.strip().lower()

        value = re.sub(
            r"[^a-z0-9]+",
            "_",
            value,
        )

        value = re.sub(
            r"_+",
            "_",
            value,
        )

        return value.strip(
            "_"
        )