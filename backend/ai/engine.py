from __future__ import annotations

from .formatter import (
    InvestigationOutputFormatter,
)

from .llm import (
    LLMExplainer,
)

from .planner import (
    InvestigationPlanner,
)

from .schemas import (
    EvidenceContract,
    InvestigationFinding,
    InvestigationRequest,
    InvestigationResponse,
    InvestigationStage,
    StructuredInvestigationContext,
    ToolExecutionStatus,
)

from .tools import (
    ToolExecutor,
)

from .evidence_validator import (
    EvidenceValidator,
)

from .grounded_findings import (
    GroundedFindingValidator,
)

from .grounded_recommendations import (
    GroundedRecommendationValidator,
)

from .grounded_response import (
    EvidenceGroundedResponseBuilder,
    grounded_response_to_dict,
)


# ============================================================
# INVESTIGATION ENGINE
# ============================================================


class InvestigationEngine:

    def __init__(
        self,
        planner: InvestigationPlanner | None = None,
        tool_executor: ToolExecutor | None = None,
        formatter: InvestigationOutputFormatter | None = None,
        llm_explainer: LLMExplainer | None = None,
        evidence_validator: EvidenceValidator | None = None,
        grounded_finding_validator: GroundedFindingValidator | None = None,
        grounded_recommendation_validator: GroundedRecommendationValidator | None = None,
        grounded_response_builder: EvidenceGroundedResponseBuilder | None = None,
    ) -> None:

        # ----------------------------------------------------
        # Existing Day 10 components
        # ----------------------------------------------------

        self.planner = (
            planner
            or InvestigationPlanner()
        )

        self.tool_executor = (
            tool_executor
            or ToolExecutor()
        )

        self.formatter = (
            formatter
            or InvestigationOutputFormatter()
        )

        self.llm_explainer = (
            llm_explainer
            or LLMExplainer()
        )

        # ----------------------------------------------------
        # Day 11 components
        # ----------------------------------------------------

        self.evidence_validator = (
            evidence_validator
            or EvidenceValidator()
        )

        self.grounded_finding_validator = (
            grounded_finding_validator
            or GroundedFindingValidator()
        )

        self.grounded_recommendation_validator = (
            grounded_recommendation_validator
            or GroundedRecommendationValidator()
        )

        self.grounded_response_builder = (
            grounded_response_builder
            or EvidenceGroundedResponseBuilder()
        )


    # ========================================================
    # CREATE PLAN
    # ========================================================

    def create_investigation(
        self,
        request: InvestigationRequest,
    ) -> InvestigationResponse:

        plan = self.planner.create_plan(
            request
        )

        return InvestigationResponse(
            question=request.question,

            stage=InvestigationStage.PLANNED,

            plan=plan,

            results=[],

            tool_results=[],

            structured_context=None,

            explanation=None,

            llm_provider=None,

            llm_model=None,

            llm_error=None,
        )


    # ========================================================
    # EXECUTE INVESTIGATION
    # ========================================================

    def execute_investigation(
        self,
        request: InvestigationRequest,
    ) -> InvestigationResponse:

        response = (
            self.create_investigation(
                request
            )
        )

        # ----------------------------------------------------
        # Execute deterministic tools
        # ----------------------------------------------------

        tool_results = (
            self.tool_executor.execute_plan(
                response.plan.tools
            )
        )

        results = [
            {
                "tool_name": result.tool_name,
                "status": result.status.value,
                "data": result.data,
                "error": result.error,
                "metadata": result.metadata,
            }
            for result
            in tool_results
        ]

        # ----------------------------------------------------
        # Build structured context
        # ----------------------------------------------------

        structured_context = (
            self.formatter.build_context(
                plan=response.plan,
                tool_results=tool_results,
            )
        )

        response.tool_results = (
            tool_results
        )

        response.results = (
            results
        )

        response.structured_context = (
            structured_context
        )

        response.stage = (
            InvestigationStage.RESULTS_READY
        )

        # ----------------------------------------------------
        # Day 11.9 grounded response
        # ----------------------------------------------------

        grounded_result = (
            self.build_grounded_response(
                structured_context
            )
        )

        # ----------------------------------------------------
        # Add grounded response without removing the existing
        # deterministic tool results.
        # ----------------------------------------------------

        response.results.append(
            {
                "type": "grounded_response",
                "status": "SUCCESS",
                "data": grounded_response_to_dict(
                    grounded_result
                ),
                "error": None,
                "metadata": {
                    "day": "11.9",
                    "grounded": (
                        grounded_result.grounded
                    ),
                    "evidence_count": len(
                        grounded_result.evidence_ids
                    ),
                },
            }
        )

        # ----------------------------------------------------
        # Deterministic grounded response remains available.
        # ----------------------------------------------------

        if grounded_result.grounded:

            response.explanation = (
                grounded_result.response
            )

        # ----------------------------------------------------
        # Optional LLM explanation
        # ----------------------------------------------------

        if request.include_explanation:

            self.generate_explanation(
                response
            )

        return response


    # ========================================================
    # DAY 11 — BUILD GROUNDED RESPONSE
    # ========================================================

    def build_grounded_response(
        self,
        context: StructuredInvestigationContext,
    ):

        # ----------------------------------------------------
        # Create immutable-style evidence contract from the
        # current structured context.
        # ----------------------------------------------------

        evidence_contract = EvidenceContract(
            version="1.0",
            evidence=list(
                context.evidence
            ),
        )

        # ----------------------------------------------------
        # Validate evidence.
        #
        # IMPORTANT:
        # Do not discard evidence merely because validation
        # returns a False contract-level status.
        #
        # Grounding operates using the complete evidence set,
        # while the validator explicitly identifies valid IDs.
        # ----------------------------------------------------

        evidence_validation = (
            self.evidence_validator.validate(
                evidence_contract
            )
        )

        # ----------------------------------------------------
        # We intentionally keep the original valid evidence
        # contract intact.
        #
        # Why?
        #
        # Finding evidence_ids reference the original evidence
        # objects generated by formatter.py.
        #
        # The validator already tells us which IDs are valid.
        # We do not need to rebuild the contract and risk
        # changing the identity relationship.
        # ----------------------------------------------------

        if (
            not evidence_validation.valid
            and not evidence_validation.validated_evidence_ids
        ):

            empty_contract = EvidenceContract(
                version="1.0",
                evidence=[],
            )

            return (
                self.grounded_response_builder.build(
                    context=context,
                    evidence_contract=empty_contract,
                    findings=[],
                    recommendations=[],
                )
            )

        # ----------------------------------------------------
        # Findings from formatter.
        # ----------------------------------------------------

        findings = list(
            context.findings
        )

        # ----------------------------------------------------
        # Validate all findings against the SAME evidence
        # contract created from context.
        # ----------------------------------------------------

        finding_validation = (
            self.grounded_finding_validator.validate_all(
                findings,
                evidence_contract,
            )
        )

        # ----------------------------------------------------
        # Keep only grounded findings.
        # ----------------------------------------------------

        grounded_findings: list[
            InvestigationFinding
        ] = []

        for finding, validation in zip(
            findings,
            finding_validation.results,
        ):

            if validation.grounded:

                grounded_findings.append(
                    finding
                )

        # ----------------------------------------------------
        # Generate deterministic recommendations.
        # ----------------------------------------------------

        recommendation_pairs: list[
            tuple[
                InvestigationFinding,
                str,
            ]
        ] = []

        for finding in grounded_findings:

            recommendation = (
                self._recommend_for_finding(
                    finding
                )
            )

            recommendation_pairs.append(
                (
                    finding,
                    recommendation,
                )
            )

        # ----------------------------------------------------
        # Final grounded response.
        #
        # Pass the ORIGINAL evidence contract and ORIGINAL
        # grounded findings, preserving all evidence IDs.
        # ----------------------------------------------------

        return (
            self.grounded_response_builder.build(
                context=context,
                evidence_contract=evidence_contract,
                findings=grounded_findings,
                recommendations=recommendation_pairs,
            )
        )


    # ========================================================
    # SAFE RECOMMENDATION GENERATOR
    # ========================================================

    @staticmethod
    def _recommend_for_finding(
        finding: InvestigationFinding,
    ) -> str:

        title = (
            finding.title.strip()
            if finding.title
            else "the identified finding"
        )

        if finding.metric:

            return (
                f"Review the evidence behind "
                f"'{title}' and analyze the "
                f"{finding.metric} pattern to identify "
                f"relevant drivers before taking "
                f"operational action."
            )

        return (
            f"Review the evidence behind "
            f"'{title}' and investigate relevant "
            f"patterns before taking operational action."
        )


    # ========================================================
    # GENERATE EXPLANATION
    # ========================================================

    def generate_explanation(
        self,
        response: InvestigationResponse,
    ) -> InvestigationResponse:

        if response.structured_context is None:

            response.llm_error = (
                "Structured investigation context "
                "is required before generating an "
                "LLM explanation."
            )

            return response

        deterministic_explanation = (
            response.explanation
        )

        try:

            context_payload = (
                response.structured_context.model_dump(
                    mode="json"
                )
            )

            explanation = (
                self.llm_explainer.generate(
                    context_payload
                )
            )

            if explanation and explanation.strip():

                response.explanation = (
                    explanation.strip()
                )

            else:

                response.explanation = (
                    deterministic_explanation
                )

            response.llm_provider = (
                getattr(
                    self.llm_explainer,
                    "provider",
                    "gemini",
                )
            )

            response.llm_model = (
                getattr(
                    self.llm_explainer,
                    "model",
                    None,
                )
            )

            response.llm_error = None

            response.stage = (
                InvestigationStage.EXPLANATION_READY
            )

        except Exception as exc:

            response.explanation = (
                deterministic_explanation
            )

            response.llm_provider = (
                getattr(
                    self.llm_explainer,
                    "provider",
                    "gemini",
                )
            )

            response.llm_model = (
                getattr(
                    self.llm_explainer,
                    "model",
                    None,
                )
            )

            response.llm_error = str(
                exc
            )

            response.stage = (
                InvestigationStage.RESULTS_READY
            )

        return response


    # ========================================================
    # EXECUTION SUMMARY
    # ========================================================

    @staticmethod
    def execution_summary(
        response: InvestigationResponse,
    ) -> dict[str, int]:

        return {
            "total":
                len(
                    response.tool_results
                ),

            "successful":
                sum(
                    1
                    for result
                    in response.tool_results
                    if (
                        result.status
                        == ToolExecutionStatus.SUCCESS
                    )
                ),

            "failed":
                sum(
                    1
                    for result
                    in response.tool_results
                    if (
                        result.status
                        == ToolExecutionStatus.FAILED
                    )
                ),

            "skipped":
                sum(
                    1
                    for result
                    in response.tool_results
                    if (
                        result.status
                        == ToolExecutionStatus.SKIPPED
                    )
                ),
        }