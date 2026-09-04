from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ============================================================
# KPI EVIDENCE
# ============================================================

class KPIEvidence(BaseModel):
    """
    Normalized KPI evidence returned by the validated KPI
    catalog.

    The model preserves the distinction between:
    AVAILABLE,
    PROXY,
    and UNSUPPORTED KPIs.
    """

    requested_metric: str

    matched_name: str | None = None

    value: Any = None

    status: str | None = None

    definition: str | None = None

    source: str = "/kpis"

    raw_kpi: dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# KPI TOOL
# ============================================================

class KPITool:
    """
    Converts the existing /kpis response into a normalized
    KPI evidence object.

    No KPI value is invented or calculated here.
    """

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
    ) -> KPIEvidence:

        result = self.tool_executor.execute(
            "get_kpi",
            {
                "metric": metric,
            },
        )

        if result.status.value != "SUCCESS":

            raise RuntimeError(
                result.error
                or (
                    "KPI tool did not return "
                    "a successful result."
                )
            )

        matched_kpi = result.data.get(
            "matched_kpi"
        )

        if not isinstance(
            matched_kpi,
            dict,
        ):

            raise RuntimeError(
                (
                    f"KPI '{metric}' returned "
                    "an invalid KPI payload."
                )
            )

        return self.normalize_result(
            metric=metric,
            kpi=matched_kpi,
        )

    # ========================================================
    # NORMALIZE
    # ========================================================

    @staticmethod
    def normalize_result(
        metric: str,
        kpi: dict[str, Any],
    ) -> KPIEvidence:

        matched_name = (
            kpi.get("kpi_name")
            or kpi.get("metric")
            or kpi.get("metric_name")
            or kpi.get("name")
            or kpi.get("key")
        )

        value = (
            kpi.get("value")
            if "value" in kpi
            else kpi.get("current_value")
        )

        status = (
            kpi.get("status")
            or kpi.get("availability")
            or kpi.get("kpi_status")
        )

        definition = (
            kpi.get("definition")
            or kpi.get("description")
            or kpi.get("business_definition")
        )

        return KPIEvidence(
            requested_metric=metric,
            matched_name=(
                str(matched_name)
                if matched_name is not None
                else None
            ),
            value=value,
            status=(
                str(status)
                if status is not None
                else None
            ),
            definition=(
                str(definition)
                if definition is not None
                else None
            ),
            source="/kpis",
            raw_kpi=dict(kpi),
        )