from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ============================================================
# INVESTIGATION STAGE
# ============================================================

class InvestigationStage(str, Enum):

    RECEIVED = "received"

    PLANNED = "planned"

    TOOLS_EXECUTED = "tools_executed"

    RESULTS_READY = "results_ready"

    EXPLANATION_READY = "explanation_ready"


# ============================================================
# TOOL EXECUTION STATUS
# ============================================================

class ToolExecutionStatus(str, Enum):

    SUCCESS = "SUCCESS"

    FAILED = "FAILED"

    SKIPPED = "SKIPPED"


# ============================================================
# DAY 11 — EVIDENCE TYPE
# ============================================================

class EvidenceType(str, Enum):

    METRIC = "METRIC"

    STATISTICAL_RESULT = "STATISTICAL_RESULT"

    KPI = "KPI"

    RECORD = "RECORD"

    PROFILE = "PROFILE"

    JOURNEY = "JOURNEY"

    QUALITY = "QUALITY"

    CONTEXT = "CONTEXT"

    UNAVAILABLE = "UNAVAILABLE"


# ============================================================
# DAY 11 — EVIDENCE SUPPORT LEVEL
# ============================================================

class EvidenceSupportLevel(str, Enum):

    DIRECT = "DIRECT"

    DERIVED = "DERIVED"

    CONTEXTUAL = "CONTEXTUAL"

    UNAVAILABLE = "UNAVAILABLE"


# ============================================================
# DAY 11.2 — PROVENANCE SOURCE TYPE
# ============================================================

class ProvenanceSourceType(str, Enum):

    TOOL = "TOOL"

    API = "API"

    DATASET = "DATASET"

    TABLE = "TABLE"

    QUERY = "QUERY"

    ENDPOINT = "ENDPOINT"

    CALCULATION = "CALCULATION"

    UNKNOWN = "UNKNOWN"


# ============================================================
# INVESTIGATION REQUEST
# ============================================================

class InvestigationRequest(BaseModel):

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    question: str = Field(
        min_length=3,
        max_length=1000,
        description=(
            "Natural-language business investigation question."
        ),
    )

    include_explanation: bool = Field(
        default=False,
        description=(
            "Generate an LLM explanation from the "
            "deterministic investigation evidence."
        ),
    )


# ============================================================
# PLANNED TOOL
# ============================================================

class PlannedTool(BaseModel):

    name: str = Field(
        min_length=1
    )

    purpose: str = Field(
        min_length=1
    )

    required: bool = True

    parameters: dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# TOOL RESULT
# ============================================================

class ToolExecutionResult(BaseModel):

    tool_name: str

    status: ToolExecutionStatus

    data: dict[str, Any] = Field(
        default_factory=dict
    )

    error: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# INVESTIGATION PLAN
# ============================================================

class InvestigationPlan(BaseModel):

    question: str

    intent: str

    primary_metric: str | None = None

    comparison_dimension: str | None = None

    customer_id: str | None = None

    booking_id: str | None = None

    threshold: float | None = None

    threshold_operator: str | None = None

    detected_entities: dict[str, str] = Field(
        default_factory=dict
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )

    tools: list[PlannedTool] = Field(
        default_factory=list
    )

    reasoning: list[str] = Field(
        default_factory=list
    )


# ============================================================
# DAY 11 — PROVENANCE
# ============================================================

class EvidenceProvenance(BaseModel):

    """
    Identifies where a piece of evidence originated.

    This creates the audit trail:

        Evidence
            ↓
        Provenance
            ↓
        Tool / API / Dataset / Query
    """

    source_type: ProvenanceSourceType = Field(
        default=ProvenanceSourceType.UNKNOWN,
        description="Type of system or analytical source.",
    )

    source_name: str = Field(
        min_length=1,
        description=(
            "Human-readable source name, such as "
            "'statistical_tool' or '/kpis'."
        ),
    )

    tool_name: str | None = Field(
        default=None,
        description=(
            "Name of the deterministic tool that generated "
            "the evidence."
        ),
    )

    endpoint: str | None = Field(
        default=None,
        description=(
            "API endpoint used to obtain the evidence."
        ),
    )

    dataset: str | None = Field(
        default=None,
        description=(
            "Dataset or file associated with the evidence."
        ),
    )

    table: str | None = Field(
        default=None,
        description=(
            "Source table when applicable."
        ),
    )

    query: str | None = Field(
        default=None,
        description=(
            "Analytical query or query identifier when applicable."
        ),
    )

    field: str | None = Field(
        default=None,
        description=(
            "Exact source field/metric represented by the evidence."
        ),
    )

    location: str | None = Field(
        default=None,
        description=(
            "Optional source location or logical path."
        ),
    )

    retrieval_reference: str | None = Field(
        default=None,
        description=(
            "Reference to the exact retrieval result."
        ),
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# DAY 11.2 — EVIDENCE ITEM
# ============================================================

class EvidenceItem(BaseModel):

    """
    Standard contract for one piece of investigation evidence.

    Includes explicit provenance so each evidence item can be
    traced back to the analytical source that produced it.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    # --------------------------------------------------------
    # Stable evidence identity
    # --------------------------------------------------------

    evidence_id: str = Field(
        default_factory=lambda: (
            f"ev_{uuid4().hex[:12]}"
        ),
        min_length=1,
    )

    # --------------------------------------------------------
    # Origin / classification
    # --------------------------------------------------------

    source: str = Field(
        min_length=1
    )

    category: str = Field(
        min_length=1
    )

    evidence_type: EvidenceType = Field(
        default=EvidenceType.CONTEXT
    )

    support_level: EvidenceSupportLevel = Field(
        default=EvidenceSupportLevel.DIRECT
    )

    # --------------------------------------------------------
    # Analytical content
    # --------------------------------------------------------

    metric: str | None = None

    value: Any = None

    unit: str | None = None

    detail: str | None = None

    # --------------------------------------------------------
    # Availability / provenance
    # --------------------------------------------------------

    available: bool = True

    source_reference: str | None = None

    record_count: int | None = Field(
        default=None,
        ge=0,
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    # --------------------------------------------------------
    # DAY 11.2 — STRUCTURED PROVENANCE
    # --------------------------------------------------------

    provenance: EvidenceProvenance | None = Field(
        default=None,
        description=(
            "Structured audit information showing where the "
            "evidence originated."
        ),
    )

    # --------------------------------------------------------
    # Contract validation
    # --------------------------------------------------------

    @model_validator(mode="after")
    def validate_contract(self) -> "EvidenceItem":

        # ----------------------------------------------------
        # Unavailable evidence normalization
        # ----------------------------------------------------

        if not self.available:

            self.support_level = (
                EvidenceSupportLevel.UNAVAILABLE
            )

            self.evidence_type = (
                EvidenceType.UNAVAILABLE
            )

            self.value = None

        # ----------------------------------------------------
        # Provenance consistency
        # ----------------------------------------------------

        if self.provenance is not None:

            if (
                self.provenance.field is None
                and self.metric is not None
            ):
                self.provenance.field = self.metric

            if (
                self.provenance.source_name == ""
            ):
                raise ValueError(
                    "Provenance source_name cannot be empty."
                )

        # ----------------------------------------------------
        # Record count normalization
        # ----------------------------------------------------

        if self.record_count is not None:

            self.record_count = int(
                self.record_count
            )

        return self


# ============================================================
# DAY 11 — EVIDENCE CONTRACT
# ============================================================

class EvidenceContract(BaseModel):

    """
    Collection-level contract for investigation evidence.
    """

    version: str = Field(
        default="1.0",
        min_length=1,
    )

    evidence: list[EvidenceItem] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def validate_evidence_ids(self) -> "EvidenceContract":

        evidence_ids = [
            item.evidence_id
            for item in self.evidence
        ]

        if len(evidence_ids) != len(set(evidence_ids)):

            raise ValueError(
                "EvidenceContract contains duplicate "
                "evidence_id values."
            )

        return self

    @property
    def available_count(self) -> int:

        return sum(
            1
            for item in self.evidence
            if item.available
        )

    @property
    def unavailable_count(self) -> int:

        return sum(
            1
            for item in self.evidence
            if not item.available
        )


# ============================================================
# STATISTICAL EVIDENCE
# ============================================================

class StatisticalEvidenceModel(BaseModel):

    metric: str

    record_count: int | None = None

    threshold: float | None = None

    flagged_count: int | None = None

    flagged_rate: float | None = None

    source: str

    raw_result: dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# KPI EVIDENCE
# ============================================================

class KPIEvidenceModel(BaseModel):

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
# FINDING
# ============================================================

class InvestigationFinding(BaseModel):

    title: str

    severity: str = "INFO"

    metric: str | None = None

    value: Any = None

    threshold: float | None = None

    operator: str | None = None

    evidence_sources: list[str] = Field(
        default_factory=list
    )

    # --------------------------------------------------------
    # DAY 11.2 — PROVENANCE LINKS
    # --------------------------------------------------------

    evidence_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Evidence IDs that directly support this finding."
        ),
    )

    detail: str = ""


# ============================================================
# TOOL EXECUTION SUMMARY
# ============================================================

class ToolExecutionSummary(BaseModel):

    total: int = 0

    successful: int = 0

    failed: int = 0

    skipped: int = 0


# ============================================================
# STRUCTURED INVESTIGATION CONTEXT
# ============================================================

class StructuredInvestigationContext(BaseModel):

    question: str

    intent: str

    primary_metric: str | None = None

    comparison_dimension: str | None = None

    customer_id: str | None = None

    booking_id: str | None = None

    threshold: float | None = None

    threshold_operator: str | None = None

    planner_confidence: float

    entities: dict[str, str] = Field(
        default_factory=dict
    )

    evidence: list[EvidenceItem] = Field(
        default_factory=list
    )

    evidence_contract: EvidenceContract | None = None

    findings: list[InvestigationFinding] = Field(
        default_factory=list
    )

    statistical_evidence: list[
        StatisticalEvidenceModel
    ] = Field(
        default_factory=list
    )

    kpi_evidence: list[
        KPIEvidenceModel
    ] = Field(
        default_factory=list
    )

    tool_summary: ToolExecutionSummary = Field(
        default_factory=ToolExecutionSummary
    )


# ============================================================
# INVESTIGATION RESPONSE
# ============================================================

class InvestigationResponse(BaseModel):

    question: str

    stage: InvestigationStage

    plan: InvestigationPlan

    results: list[dict[str, Any]] = Field(
        default_factory=list
    )

    tool_results: list[ToolExecutionResult] = Field(
        default_factory=list
    )

    structured_context: (
        StructuredInvestigationContext
        | None
    ) = None

    explanation: str | None = None

    llm_provider: str | None = None

    llm_model: str | None = None

    llm_error: str | None = None