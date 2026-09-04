from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from .schemas import (
    PlannedTool,
    ToolExecutionResult,
    ToolExecutionStatus,
)


# ============================================================
# SUPPORTED INVESTIGATION METRICS
# ============================================================

SUPPORTED_INVESTIGATION_METRICS = {
    "booking_amount",
    "failed_payments",
    "friction_score",
    "journey_duration_minutes",
    "payment_attempts",
    "payment_duration_minutes",
    "payment_success_rate",
    "retry_count",
    "successful_payments",
    "total_events",
}


# ============================================================
# DEFAULT THRESHOLDS
# ============================================================

DEFAULT_THRESHOLDS: dict[str, float] = {

    "journey_duration_minutes": 90.0,

    "friction_score": 50.0,

    "payment_attempts": 3.0,

    "failed_payments": 1.0,

    "retry_count": 1.0,

    "payment_duration_minutes": 10.0,

    "payment_success_rate": 0.75,

    "total_events": 50.0,

}


# ============================================================
# KPI ALIASES
# ============================================================

KPI_ALIASES: dict[str, set[str]] = {

    "repeat_customer_rate": {
        "repeat_customer_rate",
        "repeat_customer",
        "repeat_customer_rate_percent",
        "repeat customer rate",
    },

    "revenue": {
        "revenue",
        "total_revenue",
        "total revenue",
    },

    "booking_amount": {
        "booking_amount",
        "booking value",
        "booking amount",
    },

    "payment_success_rate": {
        "payment_success_rate",
        "payment success rate",
    },

    "payment_failure_rate": {
        "payment_failure_rate",
        "payment failure rate",
    },

    "retry_count": {
        "retry_count",
        "retry_rate",
        "retry rate",
        "retries",
    },

    "journey_duration_minutes": {
        "journey_duration_minutes",
        "journey duration",
        "journey duration minutes",
    },

    "payment_duration_minutes": {
        "payment_duration_minutes",
        "payment duration",
        "payment duration minutes",
    },

    "booking_conversion_rate": {
        "booking_conversion_rate",
        "booking conversion rate",
        "conversion rate",
    },

    "friction_score": {
        "friction_score",
        "average friction score",
        "friction",
    },

}


# ============================================================
# TOOL DEFINITIONS
# ============================================================

@dataclass(frozen=True)
class ToolDefinition:
    name: str

    description: str

    required_parameters: tuple[str, ...] = ()


TOOL_DEFINITIONS: dict[str, ToolDefinition] = {

    "get_kpi": ToolDefinition(
        name="get_kpi",
        description=(
            "Retrieve a validated KPI from the KPI catalog."
        ),
        required_parameters=("metric",),
    ),

    "get_customer_profile": ToolDefinition(
        name="get_customer_profile",
        description=(
            "Retrieve the validated profile for a customer."
        ),
        required_parameters=("customer_id",),
    ),

    "get_journey": ToolDefinition(
        name="get_journey",
        description=(
            "Retrieve a validated booking journey."
        ),
        required_parameters=("booking_id",),
    ),

    "run_statistical_analysis": ToolDefinition(
        name="run_statistical_analysis",
        description=(
            "Run deterministic statistical investigation "
            "against a supported metric."
        ),
        required_parameters=("metric",),
    ),

    "find_anomalies": ToolDefinition(
        name="find_anomalies",
        description=(
            "Investigate a supported metric using a threshold "
            "and return flagged evidence."
        ),
        required_parameters=("metric",),
    ),

    "get_data_quality": ToolDefinition(
        name="get_data_quality",
        description=(
            "Retrieve the validated data-quality report."
        ),
    ),
}


# ============================================================
# TRANSPORT PROTOCOL
# ============================================================

class APITransport(Protocol):

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ...


# ============================================================
# HTTP TRANSPORT
# ============================================================

class HTTPTransport:

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 10.0,
    ) -> None:

        self.base_url = (
            base_url
            or os.getenv(
                "JOURNEY_FORENSICS_API_URL",
                "http://127.0.0.1:8000",
            )
        ).rstrip("/")

        self.timeout = timeout


    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        url = (
            f"{self.base_url}"
            f"{path}"
        )


        if params:

            clean_params = {

                key: value

                for key, value
                in params.items()

                if value is not None

            }


            if clean_params:

                url = (
                    f"{url}?"
                    f"{urllib.parse.urlencode(clean_params)}"
                )


        headers = {
            "Accept": "application/json",
        }


        body: bytes | None = None


        if json_body is not None:

            headers[
                "Content-Type"
            ] = "application/json"

            body = json.dumps(
                json_body
            ).encode(
                "utf-8"
            )


        request = urllib.request.Request(
            url=url,
            data=body,
            headers=headers,
            method=method.upper(),
        )


        try:

            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as response:

                payload = (
                    response
                    .read()
                    .decode("utf-8")
                )


                if not payload:
                    return {}


                return json.loads(
                    payload
                )


        except urllib.error.HTTPError as exc:

            payload = (
                exc.read()
                .decode(
                    "utf-8",
                    errors="replace",
                )
            )


            try:

                data = json.loads(
                    payload
                )

            except json.JSONDecodeError:

                data = {
                    "message": payload
                }


            raise RuntimeError(
                data.get(
                    "message",
                    (
                        "API request failed "
                        f"with HTTP {exc.code}."
                    ),
                )
            ) from exc


        except urllib.error.URLError as exc:

            raise RuntimeError(
                (
                    "Unable to connect to "
                    "Journey Forensics API: "
                    f"{exc.reason}"
                )
            ) from exc


# ============================================================
# TOOL SKIPPED
# ============================================================

class ToolSkipped(Exception):
    """
    Indicates that a tool is valid but cannot currently
    execute because optional investigation context is missing.
    """

    pass


# ============================================================
# TOOL EXECUTOR
# ============================================================

class ToolExecutor:

    def __init__(
        self,
        transport: APITransport | None = None,
    ) -> None:

        self.transport = (
            transport
            or HTTPTransport()
        )


    # ========================================================
    # REGISTRY
    # ========================================================

    @staticmethod
    def available_tools() -> list[str]:

        return list(
            TOOL_DEFINITIONS.keys()
        )


    @staticmethod
    def get_definition(
        tool_name: str,
    ) -> ToolDefinition:

        try:

            return TOOL_DEFINITIONS[
                tool_name
            ]

        except KeyError as exc:

            raise ValueError(
                (
                    "Unknown investigation tool "
                    f"'{tool_name}'."
                )
            ) from exc


    # ========================================================
    # EXECUTE
    # ========================================================

    def execute(
        self,
        tool_name: str,
        parameters: dict[str, Any] | None = None,
    ) -> ToolExecutionResult:

        parameters = (
            parameters or {}
        )

        start_time = time.perf_counter()


        # ----------------------------------------------------
        # UNKNOWN TOOL
        # ----------------------------------------------------

        if tool_name not in TOOL_DEFINITIONS:

            return ToolExecutionResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.FAILED,
                error=(
                    "Unknown investigation tool "
                    f"'{tool_name}'."
                ),
                metadata={
                    "duration_ms": 0.0
                },
            )


        definition = TOOL_DEFINITIONS[
            tool_name
        ]


        # ----------------------------------------------------
        # REQUIRED PARAMETERS
        # ----------------------------------------------------

        missing = [

            parameter

            for parameter
            in definition.required_parameters

            if parameters.get(
                parameter
            ) in (
                None,
                "",
            )

        ]


        if missing:

            elapsed = (
                time.perf_counter()
                - start_time
            ) * 1000


            return ToolExecutionResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.FAILED,
                error=(
                    "Missing required tool parameters: "
                    + ", ".join(
                        missing
                    )
                ),
                metadata={
                    "duration_ms": round(
                        elapsed,
                        2,
                    )
                },
            )


        # ----------------------------------------------------
        # DISPATCH
        # ----------------------------------------------------

        try:

            if tool_name == "get_kpi":

                data = self._get_kpi(
                    parameters
                )


            elif tool_name == "get_customer_profile":

                data = self._get_customer_profile(
                    parameters
                )


            elif tool_name == "get_journey":

                data = self._get_journey(
                    parameters
                )


            elif (
                tool_name
                == "run_statistical_analysis"
            ):

                data = (
                    self._run_statistical_analysis(
                        parameters
                    )
                )


            elif tool_name == "find_anomalies":

                data = self._find_anomalies(
                    parameters
                )


            elif tool_name == "get_data_quality":

                data = self._get_data_quality()


            else:

                raise RuntimeError(
                    (
                        "Tool dispatch missing "
                        f"for '{tool_name}'."
                    )
                )


            elapsed = (
                time.perf_counter()
                - start_time
            ) * 1000


            return ToolExecutionResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.SUCCESS,
                data=data,
                metadata={
                    "duration_ms": round(
                        elapsed,
                        2,
                    )
                },
            )


        except ToolSkipped as exc:

            elapsed = (
                time.perf_counter()
                - start_time
            ) * 1000


            return ToolExecutionResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.SKIPPED,
                error=str(exc),
                metadata={
                    "duration_ms": round(
                        elapsed,
                        2,
                    )
                },
            )


        except Exception as exc:

            elapsed = (
                time.perf_counter()
                - start_time
            ) * 1000


            return ToolExecutionResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.FAILED,
                error=str(exc),
                metadata={
                    "duration_ms": round(
                        elapsed,
                        2,
                    )
                },
            )


    # ========================================================
    # EXECUTE PLAN
    # ========================================================

    def execute_plan(
        self,
        tools: list[PlannedTool],
    ) -> list[ToolExecutionResult]:

        results: list[
            ToolExecutionResult
        ] = []


        for planned_tool in tools:

            # ------------------------------------------------
            # Optional tool with missing context
            #
            # Example:
            # get_journey requires booking_id, but a general
            # payment question may not contain one.
            # ------------------------------------------------

            definition = TOOL_DEFINITIONS.get(
                planned_tool.name
            )


            if definition is None:

                results.append(
                    self.execute(
                        planned_tool.name,
                        planned_tool.parameters,
                    )
                )

                continue


            missing = [

                parameter

                for parameter
                in definition.required_parameters

                if planned_tool.parameters.get(
                    parameter
                ) in (
                    None,
                    "",
                )

            ]


            if (
                missing
                and not planned_tool.required
            ):

                results.append(
                    ToolExecutionResult(
                        tool_name=planned_tool.name,
                        status=ToolExecutionStatus.SKIPPED,
                        error=(
                            "Optional tool skipped because "
                            "required context was not available: "
                            + ", ".join(
                                missing
                            )
                        ),
                        metadata={
                            "duration_ms": 0.0
                        },
                    )
                )

                continue


            results.append(
                self.execute(
                    tool_name=planned_tool.name,
                    parameters=planned_tool.parameters,
                )
            )


        return results


    # ========================================================
    # KPI
    # ========================================================

    def _get_kpi(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        requested_metric = str(
            parameters["metric"]
        ).strip()


        response = self.transport.request(
            "GET",
            "/kpis",
        )


        kpis = (
            response.get(
                "kpis"
            )
            or response.get(
                "metrics"
            )
            or response.get(
                "data"
            )
            or []
        )


        if not isinstance(
            kpis,
            list,
        ):

            raise RuntimeError(
                "Unexpected KPI API response structure."
            )


        target_aliases = self._metric_aliases(
            requested_metric
        )


        for item in kpis:

            if not isinstance(
                item,
                dict,
            ):
                continue


            candidate_values = [

                item.get(
                    "kpi_name"
                ),

                item.get(
                    "metric"
                ),

                item.get(
                    "name"
                ),

                item.get(
                    "metric_name"
                ),

                item.get(
                    "key"
                ),

                item.get(
                    "code"
                ),

            ]


            for candidate in candidate_values:

                if candidate is None:
                    continue


                normalized = (
                    self._normalize_name(
                        str(candidate)
                    )
                )


                if normalized in target_aliases:

                    return {
                        "metric": requested_metric,
                        "matched_kpi": item,
                    }


        raise RuntimeError(
            (
                f"KPI '{requested_metric}' "
                "was not found in the validated KPI catalog."
            )
        )


    # ========================================================
    # CUSTOMER PROFILE
    # ========================================================

    def _get_customer_profile(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        customer_id = str(
            parameters["customer_id"]
        ).strip()


        return self.transport.request(
            "GET",
            "/profile",
            params={
                "customer_id": customer_id,
            },
        )


    # ========================================================
    # JOURNEY
    # ========================================================

    def _get_journey(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        booking_id = str(
            parameters["booking_id"]
        ).strip()


        return self.transport.request(
            "GET",
            (
                "/journey/"
                + urllib.parse.quote(
                    booking_id,
                    safe="",
                )
            ),
        )


    # ========================================================
    # STATISTICS
    # ========================================================

    def _run_statistical_analysis(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        metric = str(
            parameters["metric"]
        ).strip()


        metric = (
            self._canonical_investigation_metric(
                metric
            )
        )


        if (
            metric
            not in SUPPORTED_INVESTIGATION_METRICS
        ):

            raise ToolSkipped(
                (
                    f"Metric '{metric}' is not supported "
                    "by the deterministic investigation endpoint."
                )
            )


        body: dict[str, Any] = {
            "metric": metric
        }


        if parameters.get(
            "threshold"
        ) is not None:

            body["threshold"] = float(
                parameters["threshold"]
            )


        return self.transport.request(
            "POST",
            "/investigate",
            json_body=body,
        )


    # ========================================================
    # ANOMALIES
    # ========================================================

    def _find_anomalies(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        metric = str(
            parameters["metric"]
        ).strip()


        metric = (
            self._canonical_investigation_metric(
                metric
            )
        )


        if (
            metric
            not in SUPPORTED_INVESTIGATION_METRICS
        ):

            raise ToolSkipped(
                (
                    f"Metric '{metric}' is not supported "
                    "for deterministic anomaly investigation."
                )
            )


        threshold = parameters.get(
            "threshold"
        )


        if threshold is None:

            threshold = DEFAULT_THRESHOLDS.get(
                metric
            )


        if threshold is None:

            raise ToolSkipped(
                (
                    f"No deterministic default threshold "
                    f"is defined for '{metric}'."
                )
            )


        response = self.transport.request(
            "POST",
            "/investigate",
            json_body={
                "metric": metric,
                "threshold": float(
                    threshold
                ),
            },
        )


        return {
            "metric": metric,
            "threshold": float(
                threshold
            ),
            "investigation": response,
        }


    # ========================================================
    # DATA QUALITY
    # ========================================================

    def _get_data_quality(
        self,
    ) -> dict[str, Any]:

        return self.transport.request(
            "GET",
            "/quality",
        )


    # ========================================================
    # KPI ALIASES
    # ========================================================

    @staticmethod
    def _metric_aliases(
        metric: str,
    ) -> set[str]:

        normalized_metric = (
            ToolExecutor._normalize_name(
                metric
            )
        )


        aliases = {
            normalized_metric,
            metric.strip(),
        }


        configured = KPI_ALIASES.get(
            metric,
            set(),
        )


        for alias in configured:

            aliases.add(
                ToolExecutor._normalize_name(
                    alias
                )
            )


        # Handle canonical metric variants
        for canonical, values in KPI_ALIASES.items():

            normalized_values = {

                ToolExecutor._normalize_name(
                    value
                )

                for value in values
            }


            if (
                normalized_metric
                == ToolExecutor._normalize_name(
                    canonical
                )
                or normalized_metric
                in normalized_values
            ):

                aliases.add(
                    ToolExecutor._normalize_name(
                        canonical
                    )
                )

                aliases.update(
                    normalized_values
                )


        return aliases


    # ========================================================
    # CANONICAL INVESTIGATION METRIC
    # ========================================================

    @staticmethod
    def _canonical_investigation_metric(
        metric: str,
    ) -> str:

        normalized = (
            ToolExecutor._normalize_name(
                metric
            )
        )


        mapping = {

            "PAYMENT_FAILURE_RATE":
                "failed_payments",

            "RETRY_RATE":
                "retry_count",

            "REPEAT_CUSTOMER_RATE":
                "successful_payments",

            "BOOKING_CONVERSION_RATE":
                "successful_payments",

        }


        return mapping.get(
            normalized,
            metric.strip(),
        )


    # ========================================================
    # NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_name(
        value: str,
    ) -> str:

        return (
            value
            .strip()
            .replace("-", "_")
            .replace(" ", "_")
            .replace("%", "percent")
            .upper()
        )