from __future__ import annotations

from typing import Any

from .schemas import (
    EvidenceItem,
    InvestigationFinding,
    InvestigationPlan,
    KPIEvidenceModel,
    StatisticalEvidenceModel,
    StructuredInvestigationContext,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolExecutionSummary,
)

from .statistics import (
    StatisticalTool,
)


# ============================================================
# STRUCTURED OUTPUT FORMATTER
# ============================================================


class InvestigationOutputFormatter:

    def build_context(
        self,
        plan: InvestigationPlan,
        tool_results: list[ToolExecutionResult],
    ) -> StructuredInvestigationContext:

        context = StructuredInvestigationContext(
            question=plan.question,
            intent=plan.intent,
            primary_metric=plan.primary_metric,
            comparison_dimension=(
                plan.comparison_dimension
            ),
            customer_id=plan.customer_id,
            booking_id=plan.booking_id,
            threshold=plan.threshold,
            threshold_operator=(
                plan.threshold_operator
            ),
            planner_confidence=plan.confidence,
            entities=dict(
                plan.detected_entities
            ),
            evidence=[],
            findings=[],
            statistical_evidence=[],
            kpi_evidence=[],
            tool_summary=self._build_summary(
                tool_results
            ),
        )

        # ====================================================
        # GENERAL EVIDENCE
        # ====================================================

        for result in tool_results:

            if (
                result.status
                != ToolExecutionStatus.SUCCESS
            ):
                continue

            self._append_evidence(
                context=context,
                result=result,
            )

        # ====================================================
        # KPI NORMALIZATION
        # ====================================================

        self._append_kpi_evidence(
            context=context,
            plan=plan,
            tool_results=tool_results,
        )

        # ====================================================
        # STATISTICAL NORMALIZATION
        # ====================================================

        self._append_statistical_evidence(
            context=context,
            plan=plan,
            tool_results=tool_results,
        )

        # ====================================================
        # FINDINGS
        # ====================================================

        self._append_findings(
            context=context,
            plan=plan,
            tool_results=tool_results,
        )

        return context

    # ========================================================
    # TOOL SUMMARY
    # ========================================================

    @staticmethod
    def _build_summary(
        results: list[ToolExecutionResult],
    ) -> ToolExecutionSummary:

        return ToolExecutionSummary(
            total=len(results),

            successful=sum(
                1
                for result in results
                if (
                    result.status
                    == ToolExecutionStatus.SUCCESS
                )
            ),

            failed=sum(
                1
                for result in results
                if (
                    result.status
                    == ToolExecutionStatus.FAILED
                )
            ),

            skipped=sum(
                1
                for result in results
                if (
                    result.status
                    == ToolExecutionStatus.SKIPPED
                )
            ),
        )

    # ========================================================
    # EVIDENCE DISPATCH
    # ========================================================

    def _append_evidence(
        self,
        context: StructuredInvestigationContext,
        result: ToolExecutionResult,
    ) -> None:

        if result.tool_name == "get_kpi":

            self._format_kpi_evidence(
                context,
                result,
            )

        elif result.tool_name == "get_customer_profile":

            self._format_profile_evidence(
                context,
                result,
            )

        elif result.tool_name == "get_journey":

            self._format_journey_evidence(
                context,
                result,
            )

        elif (
            result.tool_name
            == "run_statistical_analysis"
        ):

            self._format_statistical_evidence(
                context,
                result,
            )

        elif result.tool_name == "find_anomalies":

            self._format_anomaly_evidence(
                context,
                result,
            )

        elif result.tool_name == "get_data_quality":

            self._format_quality_evidence(
                context,
                result,
            )

        else:

            context.evidence.append(
                EvidenceItem(
                    source=result.tool_name,
                    category="tool_result",
                    detail=(
                        "Deterministic tool execution "
                        "completed."
                    ),
                )
            )

    # ========================================================
    # KPI RAW EVIDENCE
    # ========================================================

    @staticmethod
    def _format_kpi_evidence(
        context: StructuredInvestigationContext,
        result: ToolExecutionResult,
    ) -> None:

        matched_kpi = (
            result.data.get(
                "matched_kpi"
            )
        )

        if not isinstance(
            matched_kpi,
            dict,
        ):
            return

        metric = (
            matched_kpi.get("kpi_name")
            or matched_kpi.get("metric")
            or matched_kpi.get("metric_name")
            or matched_kpi.get("name")
            or result.data.get("metric")
        )

        value = (
            matched_kpi.get("value")
            if "value" in matched_kpi
            else matched_kpi.get(
                "current_value"
            )
        )

        context.evidence.append(
            EvidenceItem(
                source=result.tool_name,
                category="kpi",
                metric=(
                    str(metric)
                    if metric is not None
                    else None
                ),
                value=value,
                unit=matched_kpi.get("unit"),
                detail=(
                    matched_kpi.get("definition")
                    or matched_kpi.get("description")
                ),
            )
        )

    # ========================================================
    # PROFILE
    # ========================================================

    @staticmethod
    def _format_profile_evidence(
        context: StructuredInvestigationContext,
        result: ToolExecutionResult,
    ) -> None:

        data = result.data

        profile_metrics = [
            "customer_id",
            "total_bookings",
            "total_revenue",
            "average_booking_value",
            "avg_booking_value",
            "recency_days",
            "booking_frequency",
            "repeat_booking_flag",
            "repeat_customer",
            "customer_segment",
            "segment",
        ]

        for field in profile_metrics:

            if field not in data:
                continue

            context.evidence.append(
                EvidenceItem(
                    source=result.tool_name,
                    category="customer_profile",
                    metric=field,
                    value=data[field],
                )
            )

    # ========================================================
    # JOURNEY
    # ========================================================

    @staticmethod
    def _format_journey_evidence(
        context: StructuredInvestigationContext,
        result: ToolExecutionResult,
    ) -> None:

        data = result.data

        journey_metrics = [
            "customer_id",
            "booking_id",
            "trip_id",
            "booking_status",
            "booking_amount",
            "payment_attempts",
            "failed_payments",
            "successful_payments",
            "retry_count",
            "payment_success_rate",
            "payment_failure_rate",
            "total_events",
            "journey_duration_minutes",
            "payment_duration_minutes",
            "friction_score",
            "risk_level",
            "anomaly_summary",
        ]

        for field in journey_metrics:

            if field not in data:
                continue

            context.evidence.append(
                EvidenceItem(
                    source=result.tool_name,
                    category="journey",
                    metric=field,
                    value=data[field],
                )
            )

    # ========================================================
    # STATISTICAL RAW EVIDENCE
    # ========================================================

    @staticmethod
    def _format_statistical_evidence(
        context: StructuredInvestigationContext,
        result: ToolExecutionResult,
    ) -> None:

        InvestigationOutputFormatter._walk_payload(
            evidence=context.evidence,
            source=result.tool_name,
            category="statistics",
            payload=result.data,
        )

    # ========================================================
    # ANOMALY
    # ========================================================

    @staticmethod
    def _format_anomaly_evidence(
        context: StructuredInvestigationContext,
        result: ToolExecutionResult,
    ) -> None:

        InvestigationOutputFormatter._walk_payload(
            evidence=context.evidence,
            source=result.tool_name,
            category="anomaly_analysis",
            payload=result.data,
        )

    # ========================================================
    # QUALITY
    # ========================================================

    @staticmethod
    def _format_quality_evidence(
        context: StructuredInvestigationContext,
        result: ToolExecutionResult,
    ) -> None:

        data = result.data

        for field in [
            "total_datasets",
            "overall_quality_score",
            "excellent_datasets",
            "warning_datasets",
            "failed_datasets",
            "total_rows",
            "total_missing_cells",
            "total_duplicate_rows",
            "total_invalid_values",
        ]:

            if field not in data:
                continue

            context.evidence.append(
                EvidenceItem(
                    source=result.tool_name,
                    category="data_quality",
                    metric=field,
                    value=data[field],
                )
            )

        datasets = data.get(
            "datasets"
        )

        if isinstance(
            datasets,
            list,
        ):

            for dataset in datasets:

                if not isinstance(
                    dataset,
                    dict,
                ):
                    continue

                name = dataset.get(
                    "dataset",
                    "unknown_dataset",
                )

                context.evidence.append(
                    EvidenceItem(
                        source=result.tool_name,
                        category=(
                            "data_quality_dataset"
                        ),
                        metric=name,
                        value=dataset,
                    )
                )

    # ========================================================
    # KPI NORMALIZATION
    # ========================================================

    @staticmethod
    def _append_kpi_evidence(
        context: StructuredInvestigationContext,
        plan: InvestigationPlan,
        tool_results: list[ToolExecutionResult],
    ) -> None:

        for result in tool_results:

            if (
                result.status
                != ToolExecutionStatus.SUCCESS
            ):
                continue

            if result.tool_name != "get_kpi":
                continue

            matched_kpi = (
                result.data.get(
                    "matched_kpi"
                )
            )

            if not isinstance(
                matched_kpi,
                dict,
            ):
                continue

            requested_metric = (
                result.data.get("metric")
                or plan.primary_metric
                or ""
            )

            from .kpi import KPITool

            normalized = (
                KPITool.normalize_result(
                    metric=str(
                        requested_metric
                    ),
                    kpi=matched_kpi,
                )
            )

            context.kpi_evidence.append(
                KPIEvidenceModel(
                    requested_metric=(
                        normalized.requested_metric
                    ),
                    matched_name=(
                        normalized.matched_name
                    ),
                    value=(
                        normalized.value
                    ),
                    status=(
                        normalized.status
                    ),
                    definition=(
                        normalized.definition
                    ),
                    source="get_kpi",
                    raw_kpi=dict(
                        normalized.raw_kpi
                    ),
                )
            )

    # ========================================================
    # STATISTICAL NORMALIZATION
    # ========================================================

    @staticmethod
    def _append_statistical_evidence(
        context: StructuredInvestigationContext,
        plan: InvestigationPlan,
        tool_results: list[ToolExecutionResult],
    ) -> None:

        for result in tool_results:

            if (
                result.status
                != ToolExecutionStatus.SUCCESS
            ):
                continue

            if (
                result.tool_name
                != "run_statistical_analysis"
            ):
                continue

            normalized = (
                StatisticalTool.normalize_result(
                    metric=(
                        plan.primary_metric
                        or result.data.get(
                            "metric",
                            "",
                        )
                    ),
                    payload=result.data,
                    threshold=plan.threshold,
                )
            )

            context.statistical_evidence.append(
                StatisticalEvidenceModel(
                    metric=normalized.metric,
                    record_count=(
                        normalized.record_count
                    ),
                    threshold=(
                        normalized.threshold
                    ),
                    flagged_count=(
                        normalized.flagged_count
                    ),
                    flagged_rate=(
                        normalized.flagged_rate
                    ),
                    source=result.tool_name,
                    raw_result=dict(
                        normalized.raw_result
                    ),
                )
            )

    # ========================================================
    # FINDINGS
    # ========================================================

    def _append_findings(
        self,
        context: StructuredInvestigationContext,
        plan: InvestigationPlan,
        tool_results: list[ToolExecutionResult],
    ) -> None:

        for statistical in (
            context.statistical_evidence
        ):

            if (
                statistical.flagged_count
                is not None
            ):

                if (
                    statistical.flagged_rate
                    is not None
                    and
                    statistical.flagged_rate
                    >= 20
                ):

                    severity = "CRITICAL"

                else:

                    severity = "HIGH"

                detail = (
                    f"{statistical.flagged_count} "
                    "records matched the statistical "
                    "investigation"
                )

                if (
                    statistical.record_count
                    is not None
                ):

                    detail += (
                        " out of "
                        f"{statistical.record_count}"
                    )

                detail += "."

                if (
                    statistical.flagged_rate
                    is not None
                ):

                    detail += (
                        " Flagged rate="
                        f"{statistical.flagged_rate:.2f}%."
                    )

                # ------------------------------------------------
                # DAY 11.9 / 11.10 EVIDENCE LINKING
                # ------------------------------------------------

                evidence_ids = (
                    self._find_statistical_finding_evidence_ids(
                        context=context,
                        source=statistical.source,
                        primary_metric=statistical.metric,
                    )
                )

                context.findings.append(
                    InvestigationFinding(
                        title=(
                            "Statistical threshold matches"
                        ),
                        severity=severity,
                        metric=(
                            statistical.metric
                        ),
                        value=(
                            statistical.flagged_count
                        ),
                        threshold=(
                            statistical.threshold
                        ),
                        operator=(
                            plan.threshold_operator
                        ),
                        evidence_sources=[
                            statistical.source
                        ],
                        evidence_ids=evidence_ids,
                        detail=detail,
                    )
                )

        # ----------------------------------------------------
        # Journey risk
        # ----------------------------------------------------

        for result in tool_results:

            if (
                result.status
                != ToolExecutionStatus.SUCCESS
            ):
                continue

            if (
                result.tool_name
                != "get_journey"
            ):
                continue

            risk = result.data.get(
                "risk_level"
            )

            anomaly_summary = (
                result.data.get(
                    "anomaly_summary"
                )
            )

            if risk or anomaly_summary:

                evidence_ids = (
                    self._find_evidence_ids(
                        context=context,
                        source=result.tool_name,
                        metrics=[
                            "risk_level",
                            "anomaly_summary",
                        ],
                    )
                )

                context.findings.append(
                    InvestigationFinding(
                        title=(
                            "Journey risk assessment"
                        ),
                        severity=str(
                            risk
                            or "INFO"
                        ).upper(),
                        metric="risk_level",
                        value=risk,
                        evidence_sources=[
                            result.tool_name
                        ],
                        evidence_ids=evidence_ids,
                        detail=str(
                            anomaly_summary
                            or
                            "Journey risk signal returned."
                        ),
                    )
                )

    # ========================================================
    # STATISTICAL FINDING EVIDENCE
    # ========================================================

    @classmethod
    def _find_statistical_finding_evidence_ids(
        cls,
        context: StructuredInvestigationContext,
        source: str,
        primary_metric: str | None,
    ) -> list[str]:
        """
        Link a statistical finding to the concrete evidence
        generated by run_statistical_analysis.

        We explicitly search for:

            1. primary metric
            2. flagged_count
            3. threshold
            4. threshold_operator
            5. flagged_rate / flagged_percentage

        Primary metric matching is intentionally flexible
        because the raw statistical payload can represent the
        metric as either:

            metric="metric"
            value="journey_duration_minutes"

        or:

            metric="result.source_column"
            value="journey_duration_minutes"

        rather than using the metric name itself as the
        EvidenceItem.metric.
        """

        evidence_ids: list[str] = []

        # ----------------------------------------------------
        # Primary metric
        # ----------------------------------------------------

        if primary_metric:

            primary_metric_normalized = (
                str(
                    primary_metric
                )
                .strip()
                .lower()
            )

            for item in context.evidence:

                if (
                    item.source
                    != source
                ):
                    continue

                if not item.available:
                    continue

                evidence_metric = (
                    str(
                        item.metric
                    )
                    .strip()
                    .lower()
                    if item.metric is not None
                    else ""
                )

                evidence_value = (
                    str(
                        item.value
                    )
                    .strip()
                    .lower()
                    if item.value is not None
                    else ""
                )

                if (
                    evidence_metric
                    == primary_metric_normalized
                    or
                    primary_metric_normalized
                    in evidence_metric
                    or
                    evidence_metric
                    in primary_metric_normalized
                    or
                    evidence_value
                    == primary_metric_normalized
                ):

                    if (
                        item.evidence_id
                        not in evidence_ids
                    ):

                        evidence_ids.append(
                            item.evidence_id
                        )

        # ----------------------------------------------------
        # Remaining statistical evidence
        # ----------------------------------------------------

        evidence_ids.extend(
            cls._find_evidence_ids(
                context=context,
                source=source,
                metrics=[
                    "flagged_count",
                    "threshold",
                    "threshold_operator",
                    "flagged_rate",
                    "flagged_percentage",
                ],
            )
        )

        # ----------------------------------------------------
        # De-duplicate while preserving order
        # ----------------------------------------------------

        return list(
            dict.fromkeys(
                evidence_ids
            )
        )

    # ========================================================
    # GENERAL EVIDENCE ID FINDER
    # ========================================================

    @staticmethod
    def _find_evidence_ids(
        context: StructuredInvestigationContext,
        source: str,
        metrics: list[str],
    ) -> list[str]:
        """
        Locate evidence IDs by evidence metric path.

        Supports examples such as:

            flagged_count
            result.flagged_count
            result.threshold
            result.flagged_percentage
            risk_level
        """

        normalized_metrics = {
            str(metric)
            .strip()
            .lower()
            for metric in metrics
            if metric is not None
            and str(metric).strip()
        }

        evidence_ids: list[str] = []

        for item in context.evidence:

            if item.source != source:
                continue

            if not item.available:
                continue

            metric = (
                str(
                    item.metric
                )
                .strip()
                .lower()
                if item.metric is not None
                else ""
            )

            if not metric:
                continue

            matched = False

            for requested in normalized_metrics:

                if metric == requested:

                    matched = True
                    break

                if metric.endswith(
                    f".{requested}"
                ):

                    matched = True
                    break

                if requested in metric:

                    matched = True
                    break

            if matched:

                if (
                    item.evidence_id
                    not in evidence_ids
                ):

                    evidence_ids.append(
                        item.evidence_id
                    )

        return evidence_ids

    # ========================================================
    # RECURSIVE PAYLOAD WALKER
    # ========================================================

    @classmethod
    def _walk_payload(
        cls,
        evidence: list[EvidenceItem],
        source: str,
        category: str,
        payload: Any,
        prefix: str = "",
    ) -> None:

        if isinstance(
            payload,
            dict,
        ):

            for key, value in payload.items():

                metric_name = (
                    f"{prefix}.{key}"
                    if prefix
                    else key
                )

                if isinstance(
                    value,
                    (
                        dict,
                        list,
                    ),
                ):

                    cls._walk_payload(
                        evidence=evidence,
                        source=source,
                        category=category,
                        payload=value,
                        prefix=metric_name,
                    )

                else:

                    evidence.append(
                        EvidenceItem(
                            source=source,
                            category=category,
                            metric=metric_name,
                            value=value,
                        )
                    )

        elif isinstance(
            payload,
            list,
        ):

            for index, item in enumerate(
                payload
            ):

                metric_name = (
                    f"{prefix}[{index}]"
                    if prefix
                    else f"[{index}]"
                )

                cls._walk_payload(
                    evidence=evidence,
                    source=source,
                    category=category,
                    payload=item,
                    prefix=metric_name,
                )