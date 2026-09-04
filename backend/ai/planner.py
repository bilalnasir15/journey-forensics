import re

from .schemas import (
    InvestigationPlan,
    InvestigationRequest,
    PlannedTool,
)


# ============================================================
# INVESTIGATION PLANNER
# ============================================================

class InvestigationPlanner:
    """
    Deterministic investigation planner.

    Day 10.3 responsibilities:

        Natural-language question
                    ↓
        Intent detection
                    ↓
        Metric detection
                    ↓
        Context-aware metric inference
                    ↓
        Entity extraction
                    ↓
        Threshold extraction
                    ↓
        Comparison detection
                    ↓
        Tool planning

    This layer intentionally does not call an LLM.
    """

    CUSTOMER_ID_PATTERN = re.compile(
        r"\bC\d{6}\b",
        flags=re.IGNORECASE,
    )

    BOOKING_ID_PATTERN = re.compile(
        r"\bB\d{6}\b",
        flags=re.IGNORECASE,
    )

    def __init__(self) -> None:

        self._patterns = {

            "repeat_purchase": [
                r"repeat\s+purchase",
                r"repeat\s+purchases",
                r"repeat\s+customer",
                r"repurchase",
                r"retention",
                r"returning\s+customer",
            ],

            "payment": [
                r"payment",
                r"failed\s+payment",
                r"payment\s+failure",
                r"payment\s+failures",
                r"retry",
                r"retries",
                r"retrying",
                r"transaction",
            ],

            "journey": [
                r"journey",
                r"journeys",
                r"booking",
                r"bookings",
                r"customer\s+flow",
                r"conversion",
                r"friction",
                r"time\s+spent",
                r"duration",
                r"minutes?",
            ],

            "customer": [
                r"customer",
                r"customers",
                r"segment",
                r"segments",
                r"cohort",
                r"vip",
                r"loyal",
                r"dormant",
                r"at\s+risk",
            ],

            "revenue": [
                r"revenue",
                r"sales",
                r"booking\s+amount",
                r"booking\s+value",
                r"spend",
            ],

            "data_quality": [
                r"data\s+quality",
                r"missing",
                r"duplicate",
                r"invalid",
                r"quality",
                r"completeness",
            ],
        }

    # ========================================================
    # CREATE PLAN
    # ========================================================

    def create_plan(
        self,
        request: InvestigationRequest,
    ) -> InvestigationPlan:

        question = request.question.strip()

        question_lower = question.lower()

        intent = self._detect_intent(
            question_lower
        )

        primary_metric = self._detect_metric(
            question_lower
        )

        comparison_dimension = (
            self._detect_comparison(
                question_lower
            )
        )

        customer_id = (
            self._extract_customer_id(
                question
            )
        )

        booking_id = (
            self._extract_booking_id(
                question
            )
        )

        threshold, threshold_operator = (
            self._extract_threshold(
                question_lower,
                primary_metric,
            )
        )

        # ----------------------------------------------------
        # Context-aware inference
        # ----------------------------------------------------

        primary_metric = (
            self._infer_context_metric(
                question=question_lower,
                intent=intent,
                primary_metric=primary_metric,
                threshold=threshold,
                booking_id=booking_id,
            )
        )

        detected_entities = (
            self._build_entities(
                customer_id=customer_id,
                booking_id=booking_id,
                primary_metric=primary_metric,
                comparison_dimension=comparison_dimension,
                threshold=threshold,
            )
        )

        tools = self._select_tools(
            intent=intent,
            question=question_lower,
            primary_metric=primary_metric,
            comparison_dimension=comparison_dimension,
            customer_id=customer_id,
            booking_id=booking_id,
            threshold=threshold,
        )

        confidence = self._calculate_confidence(
            intent=intent,
            primary_metric=primary_metric,
            customer_id=customer_id,
            booking_id=booking_id,
            threshold=threshold,
        )

        reasoning = self._build_reasoning(
            intent=intent,
            primary_metric=primary_metric,
            comparison_dimension=comparison_dimension,
            customer_id=customer_id,
            booking_id=booking_id,
            threshold=threshold,
            threshold_operator=threshold_operator,
            tools=tools,
            confidence=confidence,
        )

        return InvestigationPlan(
            question=question,
            intent=intent,
            primary_metric=primary_metric,
            comparison_dimension=comparison_dimension,
            customer_id=customer_id,
            booking_id=booking_id,
            threshold=threshold,
            threshold_operator=threshold_operator,
            detected_entities=detected_entities,
            confidence=confidence,
            tools=tools,
            reasoning=reasoning,
        )

    # ========================================================
    # INTENT
    # ========================================================

    def _detect_intent(
        self,
        question: str,
    ) -> str:

        scores: dict[str, int] = {}

        for intent, patterns in self._patterns.items():

            score = 0

            for pattern in patterns:

                if re.search(
                    pattern,
                    question,
                    flags=re.IGNORECASE,
                ):
                    score += 1

            if score > 0:
                scores[intent] = score

        if not scores:
            return "general_business_investigation"

        max_score = max(
            scores.values()
        )

        candidates = [
            intent
            for intent, score
            in scores.items()
            if score == max_score
        ]

        priority = [
            "data_quality",
            "repeat_purchase",
            "payment",
            "revenue",
            "journey",
            "customer",
        ]

        for preferred in priority:

            if preferred in candidates:
                return preferred

        return candidates[0]

    # ========================================================
    # METRIC DETECTION
    # ========================================================

    def _detect_metric(
        self,
        question: str,
    ) -> str | None:

        metric_patterns = [

            (
                r"repeat\s+purchases?|"
                r"repurchase|"
                r"retention|"
                r"repeat\s+customer|"
                r"returning\s+customer",
                "repeat_customer_rate",
            ),

            (
                r"booking\s+amount|"
                r"booking\s+value",
                "booking_amount",
            ),

            (
                r"revenue|"
                r"sales|"
                r"spend",
                "revenue",
            ),

            (
                r"payment\s+success|"
                r"successful\s+payment",
                "payment_success_rate",
            ),

            (
                r"payment\s+failure|"
                r"failed\s+payment|"
                r"payment\s+failures",
                "payment_failure_rate",
            ),

            (
                r"retry|"
                r"retries|"
                r"retrying",
                "retry_count",
            ),

            (
                r"payment\s+duration|"
                r"payment\s+time|"
                r"payment\s+processing\s+time",
                "payment_duration_minutes",
            ),

            (
                r"journey\s+duration|"
                r"journey\s+time|"
                r"time\s+spent|"
                r"journeys?\s+above|"
                r"journeys?\s+over|"
                r"journeys?\s+below|"
                r"journeys?\s+under|"
                r"duration",
                "journey_duration_minutes",
            ),

            (
                r"friction",
                "friction_score",
            ),

            (
                r"conversion|"
                r"booking\s+conversion",
                "booking_conversion_rate",
            ),

            (
                r"data\s+quality|"
                r"completeness|"
                r"quality",
                "quality_score",
            ),
        ]

        for pattern, metric in metric_patterns:

            if re.search(
                pattern,
                question,
                flags=re.IGNORECASE,
            ):
                return metric

        return None

    # ========================================================
    # CONTEXT-AWARE METRIC INFERENCE
    # ========================================================

    @staticmethod
    def _infer_context_metric(
        question: str,
        intent: str,
        primary_metric: str | None,
        threshold: float | None,
        booking_id: str | None,
    ) -> str | None:

        # Explicit metric always wins.
        if primary_metric is not None:
            return primary_metric

        # ----------------------------------------------------
        # Booking + payment journey
        # ----------------------------------------------------

        if booking_id and re.search(
            r"\bpayment\b",
            question,
            flags=re.IGNORECASE,
        ):

            return "payment_duration_minutes"

        # ----------------------------------------------------
        # Booking-specific journey
        # ----------------------------------------------------

        if (
            booking_id
            and intent == "journey"
        ):

            return "journey_duration_minutes"

        # ----------------------------------------------------
        # Generic journey + threshold
        # ----------------------------------------------------

        if (
            intent == "journey"
            and threshold is not None
            and re.search(
                r"\bjourneys?\b",
                question,
                flags=re.IGNORECASE,
            )
        ):

            return "journey_duration_minutes"

        # ----------------------------------------------------
        # Generic journey wording
        # ----------------------------------------------------

        if intent == "journey" and re.search(
            r"\bjourneys?\b",
            question,
            flags=re.IGNORECASE,
        ):

            return "journey_duration_minutes"

        return None

    # ========================================================
    # COMPARISON
    # ========================================================

    def _detect_comparison(
        self,
        question: str,
    ) -> str | None:

        comparisons = [

            (
                r"by\s+segment|"
                r"across\s+segments|"
                r"segment|"
                r"segments|"
                r"vip|"
                r"loyal|"
                r"dormant|"
                r"at\s+risk",
                "customer_segment",
            ),

            (
                r"cohort|"
                r"month|"
                r"monthly|"
                r"over\s+time",
                "cohort_month",
            ),

            (
                r"country|"
                r"countries|"
                r"market",
                "country",
            ),

            (
                r"failed|"
                r"failure|"
                r"successful|"
                r"success",
                "payment_outcome",
            ),
        ]

        for pattern, dimension in comparisons:

            if re.search(
                pattern,
                question,
                flags=re.IGNORECASE,
            ):
                return dimension

        return None

    # ========================================================
    # CUSTOMER ID
    # ========================================================

    def _extract_customer_id(
        self,
        question: str,
    ) -> str | None:

        match = (
            self.CUSTOMER_ID_PATTERN.search(
                question
            )
        )

        if not match:
            return None

        return match.group(0).upper()

    # ========================================================
    # BOOKING ID
    # ========================================================

    def _extract_booking_id(
        self,
        question: str,
    ) -> str | None:

        match = (
            self.BOOKING_ID_PATTERN.search(
                question
            )
        )

        if not match:
            return None

        return match.group(0).upper()

    # ========================================================
    # THRESHOLD
    # ========================================================

    def _extract_threshold(
        self,
        question: str,
        metric: str | None,
    ) -> tuple[float | None, str | None]:

        patterns = [

            (
                r"(?:above|over|greater\s+than|"
                r"more\s+than|at\s+least|"
                r"minimum\s+of)\s+"
                r"(-?\d+(?:\.\d+)?)",
                ">=",
            ),

            (
                r"(?:below|under|less\s+than|"
                r"no\s+more\s+than|"
                r"maximum\s+of)\s+"
                r"(-?\d+(?:\.\d+)?)",
                "<=",
            ),

            (
                r"(?:threshold|cutoff|cut-off)\s*"
                r"(?:is|=)?\s*"
                r"(-?\d+(?:\.\d+)?)",
                ">=",
            ),
        ]

        for pattern, operator in patterns:

            match = re.search(
                pattern,
                question,
                flags=re.IGNORECASE,
            )

            if match:

                return (
                    float(
                        match.group(1)
                    ),
                    operator,
                )

        if metric == "journey_duration_minutes":

            match = re.search(
                r"(?:above|over|exceeding)\s+"
                r"(-?\d+(?:\.\d+)?)"
                r"\s*(?:minutes?|mins?|m)?",
                question,
                flags=re.IGNORECASE,
            )

            if match:

                return (
                    float(
                        match.group(1)
                    ),
                    ">=",
                )

        return None, None

    # ========================================================
    # ENTITIES
    # ========================================================

    @staticmethod
    def _build_entities(
        customer_id: str | None,
        booking_id: str | None,
        primary_metric: str | None,
        comparison_dimension: str | None,
        threshold: float | None,
    ) -> dict[str, str]:

        entities: dict[str, str] = {}

        if customer_id:
            entities[
                "customer_id"
            ] = customer_id

        if booking_id:
            entities[
                "booking_id"
            ] = booking_id

        if primary_metric:
            entities[
                "metric"
            ] = primary_metric

        if comparison_dimension:
            entities[
                "comparison_dimension"
            ] = comparison_dimension

        if threshold is not None:
            entities[
                "threshold"
            ] = str(threshold)

        return entities

    # ========================================================
    # TOOL SELECTION
    # ========================================================

    def _select_tools(
        self,
        intent: str,
        question: str,
        primary_metric: str | None,
        comparison_dimension: str | None,
        customer_id: str | None,
        booking_id: str | None,
        threshold: float | None,
    ) -> list[PlannedTool]:

        tools: list[PlannedTool] = []

        # ----------------------------------------------------
        # CUSTOMER PROFILE
        # ----------------------------------------------------

        if customer_id:

            tools.append(
                PlannedTool(
                    name="get_customer_profile",
                    purpose=(
                        "Retrieve the validated customer "
                        "profile for the identified customer."
                    ),
                    required=True,
                    parameters={
                        "customer_id": customer_id,
                    },
                )
            )

        elif (
            intent == "customer"
            or comparison_dimension
            == "customer_segment"
        ):

            tools.append(
                PlannedTool(
                    name="get_customer_profile",
                    purpose=(
                        "Retrieve customer-level behavioral "
                        "and segmentation information."
                    ),
                    required=False,
                    parameters={
                        "customer_id": None,
                    },
                )
            )

        # ----------------------------------------------------
        # JOURNEY
        # ----------------------------------------------------

        if booking_id:

            tools.append(
                PlannedTool(
                    name="get_journey",
                    purpose=(
                        "Retrieve the validated journey "
                        "for the identified booking."
                    ),
                    required=True,
                    parameters={
                        "booking_id": booking_id,
                    },
                )
            )

        elif intent in {
            "journey",
            "payment",
        }:

            tools.append(
                PlannedTool(
                    name="get_journey",
                    purpose=(
                        "Retrieve a validated booking journey "
                        "when a booking ID is available."
                    ),
                    required=False,
                    parameters={
                        "booking_id": None,
                    },
                )
            )

        # ----------------------------------------------------
        # KPI
        # ----------------------------------------------------

        if (
            primary_metric
            or intent in {
                "revenue",
                "journey",
                "payment",
                "repeat_purchase",
            }
        ):

            tools.append(
                PlannedTool(
                    name="get_kpi",
                    purpose=(
                        "Retrieve a validated KPI value "
                        "relevant to the investigation."
                    ),
                    required=True,
                    parameters={
                        "metric": primary_metric,
                    },
                )
            )

        # ----------------------------------------------------
        # STATISTICS
        # ----------------------------------------------------

        if (
            primary_metric
            or intent in {
                "repeat_purchase",
                "payment",
                "journey",
                "revenue",
            }
            or comparison_dimension
            is not None
        ):

            tools.append(
                PlannedTool(
                    name="run_statistical_analysis",
                    purpose=(
                        "Calculate deterministic statistical "
                        "evidence relevant to the question."
                    ),
                    required=True,
                    parameters={
                        "metric": primary_metric,
                        "comparison_dimension":
                            comparison_dimension,
                        "threshold":
                            threshold,
                    },
                )
            )

        # ----------------------------------------------------
        # ANOMALIES
        # ----------------------------------------------------

        asks_for_problem = re.search(
            r"why|problem|issue|"
            r"anomal|risk|suspicious|"
            r"cause|causing|driving",
            question,
            flags=re.IGNORECASE,
        )

        if (
            intent in {
                "payment",
                "journey",
            }
            or asks_for_problem
        ):

            tools.append(
                PlannedTool(
                    name="find_anomalies",
                    purpose=(
                        "Identify deterministic anomaly "
                        "signals that may explain the finding."
                    ),
                    required=False,
                    parameters={
                        "metric": primary_metric,
                        "threshold": threshold,
                    },
                )
            )

        # ----------------------------------------------------
        # DATA QUALITY
        # ----------------------------------------------------

        if intent == "data_quality":

            tools.append(
                PlannedTool(
                    name="get_data_quality",
                    purpose=(
                        "Retrieve validated dataset quality "
                        "and completeness evidence."
                    ),
                    required=True,
                    parameters={},
                )
            )

        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------

        if not tools:

            tools.append(
                PlannedTool(
                    name="get_kpi",
                    purpose=(
                        "Start with validated KPI context "
                        "for the investigation."
                    ),
                    required=True,
                    parameters={
                        "metric":
                            primary_metric,
                    },
                )
            )

        return self._deduplicate_tools(
            tools
        )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    @staticmethod
    def _calculate_confidence(
        intent: str,
        primary_metric: str | None,
        customer_id: str | None,
        booking_id: str | None,
        threshold: float | None,
    ) -> float:

        score = 0.50

        if (
            intent
            != "general_business_investigation"
        ):
            score += 0.15

        if primary_metric:
            score += 0.15

        if customer_id or booking_id:
            score += 0.10

        if threshold is not None:
            score += 0.05

        return round(
            min(
                1.0,
                score,
            ),
            2,
        )

    # ========================================================
    # REASONING
    # ========================================================

    def _build_reasoning(
        self,
        intent: str,
        primary_metric: str | None,
        comparison_dimension: str | None,
        customer_id: str | None,
        booking_id: str | None,
        threshold: float | None,
        threshold_operator: str | None,
        tools: list[PlannedTool],
        confidence: float,
    ) -> list[str]:

        reasoning: list[str] = []

        reasoning.append(
            f"Detected investigation intent: {intent}."
        )

        if primary_metric:

            reasoning.append(
                (
                    "Primary analytical metric identified: "
                    f"{primary_metric}."
                )
            )

        else:

            reasoning.append(
                "No single primary analytical metric was identified."
            )

        if customer_id:

            reasoning.append(
                (
                    "Customer entity identified: "
                    f"{customer_id}."
                )
            )

        if booking_id:

            reasoning.append(
                (
                    "Booking entity identified: "
                    f"{booking_id}."
                )
            )

        if comparison_dimension:

            reasoning.append(
                (
                    "Comparison dimension identified: "
                    f"{comparison_dimension}."
                )
            )

        if threshold is not None:

            reasoning.append(
                (
                    "Threshold identified: "
                    f"{threshold:g} "
                    f"using operator "
                    f"{threshold_operator}."
                )
            )

        reasoning.append(
            (
                "Planning confidence: "
                f"{confidence:.2f}."
            )
        )

        reasoning.append(
            (
                "Deterministic analytical evidence will "
                "be gathered before any LLM explanation."
            )
        )

        reasoning.append(
            (
                "Selected tools: "
                + ", ".join(
                    tool.name
                    for tool in tools
                )
                + "."
            )
        )

        return reasoning

    # ========================================================
    # DEDUPLICATION
    # ========================================================

    @staticmethod
    def _deduplicate_tools(
        tools: list[PlannedTool],
    ) -> list[PlannedTool]:

        seen: set[str] = set()

        result: list[PlannedTool] = []

        for tool in tools:

            if tool.name in seen:
                continue

            seen.add(
                tool.name
            )

            result.append(
                tool
            )

        return result