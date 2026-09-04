from __future__ import annotations

import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
)

if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# IMPORTS
# ============================================================

from backend.ai.confidence_uncertainty import (
    ConfidenceUncertaintyAnalyzer,
    confidence_uncertainty_to_dict,
)

from backend.ai.schemas import (
    EvidenceContract,
    EvidenceItem,
    EvidenceProvenance,
    EvidenceSupportLevel,
    EvidenceType,
    InvestigationFinding,
    ProvenanceSourceType,
)


# ============================================================
# TEST COUNTERS
# ============================================================

total_checks = 0
passed_checks = 0


def check(
    name: str,
    condition: bool,
    detail: str,
) -> None:

    global total_checks
    global passed_checks

    total_checks += 1

    if condition:

        passed_checks += 1

        print(
            f"{name}: PASS"
        )

        print(
            f"    {detail}"
        )

    else:

        print(
            f"{name}: FAIL"
        )

        print(
            f"    {detail}"
        )


# ============================================================
# COMMON PROVENANCE
# ============================================================

stat_provenance = EvidenceProvenance(
    source_type=(
        ProvenanceSourceType.TOOL
    ),
    source_name="statistical_tool",
    tool_name="StatisticalTool",
    endpoint="/ai/investigate",
    dataset="journeys",
    table="journeys",
    field="journey_duration_minutes",
    retrieval_reference=(
        "statistical_tool.result"
    ),
)


# ============================================================
# HIGH-QUALITY EVIDENCE CONTRACT
# ============================================================

high_quality_contract = EvidenceContract(
    version="1.0",
    evidence=[
        EvidenceItem(
            evidence_id="stat_flagged",
            source="statistical_tool",
            category="statistical",
            evidence_type=(
                EvidenceType.STATISTICAL_RESULT
            ),
            support_level=(
                EvidenceSupportLevel.DIRECT
            ),
            metric="flagged_count",
            value=1015,
            unit="records",
            detail=(
                "1015 journeys exceeded "
                "the 90-minute threshold."
            ),
            available=True,
            source_reference=(
                "statistical_tool.flagged_count"
            ),
            record_count=8000,
            confidence=1.0,
            provenance=stat_provenance,
        ),
        EvidenceItem(
            evidence_id="stat_threshold",
            source="statistical_tool",
            category="statistical",
            evidence_type=(
                EvidenceType.STATISTICAL_RESULT
            ),
            support_level=(
                EvidenceSupportLevel.DIRECT
            ),
            metric="threshold",
            value=90.0,
            unit="minutes",
            detail=(
                "Investigation threshold is "
                "90 minutes."
            ),
            available=True,
            source_reference=(
                "statistical_tool.threshold"
            ),
            record_count=8000,
            confidence=1.0,
            provenance=stat_provenance,
        ),
        EvidenceItem(
            evidence_id="stat_rate",
            source="statistical_tool",
            category="statistical",
            evidence_type=(
                EvidenceType.STATISTICAL_RESULT
            ),
            support_level=(
                EvidenceSupportLevel.DERIVED
            ),
            metric="flagged_rate",
            value="12.69%",
            unit="percent",
            detail=(
                "Flagged journey rate "
                "is 12.69%."
            ),
            available=True,
            source_reference=(
                "statistical_tool.flagged_rate"
            ),
            record_count=8000,
            confidence=0.95,
            provenance=stat_provenance,
        ),
    ],
)


# ============================================================
# ANALYZER
# ============================================================

analyzer = ConfidenceUncertaintyAnalyzer()


# ============================================================
# TEST 1
# HIGH QUALITY EVIDENCE
# ============================================================

finding = InvestigationFinding(
    title=(
        "Journeys above 90 minutes"
    ),
    severity="HIGH",
    metric="flagged_count",
    value=1015,
    threshold=90.0,
    operator=">",
    evidence_sources=[
        "statistical_tool"
    ],
    evidence_ids=[
        "stat_flagged"
    ],
    detail=(
        "1015 journeys exceeded "
        "the threshold."
    ),
)

result = analyzer.analyze(
    high_quality_contract,
    [finding],
)

check(
    "High-quality evidence produces confidence",
    result.confidence.score >= 0.80,
    (
        f"score="
        f"{result.confidence.score}"
    ),
)


# ============================================================
# TEST 2
# HIGH CONFIDENCE LEVEL
# ============================================================

check(
    "High-quality evidence is classified HIGH",
    result.confidence.level == "HIGH",
    (
        f"level="
        f"{result.confidence.level}"
    ),
)


# ============================================================
# TEST 3
# DIRECT EVIDENCE COUNT
# ============================================================

check(
    "Direct evidence count is correct",
    result.confidence.direct_evidence_count == 2,
    (
        f"direct="
        f"{result.confidence.direct_evidence_count}"
    ),
)


# ============================================================
# TEST 4
# DERIVED EVIDENCE COUNT
# ============================================================

check(
    "Derived evidence count is correct",
    result.confidence.derived_evidence_count == 1,
    (
        f"derived="
        f"{result.confidence.derived_evidence_count}"
    ),
)


# ============================================================
# TEST 5
# FINDING IS GROUNDED
# ============================================================

check(
    "Grounded finding is counted",
    result.confidence.grounded_finding_count == 1,
    (
        f"grounded="
        f"{result.confidence.grounded_finding_count}"
    ),
)


# ============================================================
# TEST 6
# NO MATERIAL UNCERTAINTY FROM AVAILABLE EVIDENCE
# ============================================================

available_result = analyzer.analyze(
    EvidenceContract(
        version="1.0",
        evidence=[
            EvidenceItem(
                evidence_id="direct_001",
                source="test_tool",
                category="metric",
                evidence_type=(
                    EvidenceType.METRIC
                ),
                support_level=(
                    EvidenceSupportLevel.DIRECT
                ),
                metric="record_count",
                value=8000,
                detail="8000 records.",
                available=True,
                confidence=1.0,
            )
        ],
    ),
)

check(
    "Strong direct evidence can produce no uncertainty",
    not available_result.uncertainty.has_uncertainty,
    available_result.uncertainty.summary,
)


# ============================================================
# TEST 7
# UNAVAILABLE EVIDENCE CREATES UNCERTAINTY
# ============================================================

unavailable_contract = EvidenceContract(
    version="1.0",
    evidence=[
        EvidenceItem(
            evidence_id="unavailable_001",
            source="complaint_tool",
            category="complaints",
            evidence_type=(
                EvidenceType.UNAVAILABLE
            ),
            support_level=(
                EvidenceSupportLevel.UNAVAILABLE
            ),
            available=False,
            value=None,
        )
    ],
)

result = analyzer.analyze(
    unavailable_contract
)

check(
    "Unavailable evidence creates uncertainty",
    result.uncertainty.has_uncertainty,
    result.uncertainty.summary,
)


# ============================================================
# TEST 8
# UNAVAILABLE COUNT
# ============================================================

check(
    "Unavailable evidence is counted",
    result.confidence.unavailable_evidence_count == 1,
    (
        f"unavailable="
        f"{result.confidence.unavailable_evidence_count}"
    ),
)


# ============================================================
# TEST 9
# LOW CONFIDENCE EVIDENCE
# ============================================================

low_confidence_contract = EvidenceContract(
    version="1.0",
    evidence=[
        EvidenceItem(
            evidence_id="low_001",
            source="test_tool",
            category="metric",
            evidence_type=(
                EvidenceType.METRIC
            ),
            support_level=(
                EvidenceSupportLevel.DIRECT
            ),
            metric="test_metric",
            value=100,
            detail="Observed metric.",
            available=True,
            confidence=0.30,
        ),
    ],
)

result = analyzer.analyze(
    low_confidence_contract
)

low_uncertainty = any(
    item.category
    == "LOW_CONFIDENCE_EVIDENCE"
    for item
    in result.uncertainty.items
)

check(
    "Low-confidence evidence is identified",
    low_uncertainty,
    (
        f"items="
        f"{len(result.uncertainty.items)}"
    ),
)


# ============================================================
# TEST 10
# DERIVED EVIDENCE UNCERTAINTY
# ============================================================

derived_contract = EvidenceContract(
    version="1.0",
    evidence=[
        EvidenceItem(
            evidence_id="derived_001",
            source="analytics_tool",
            category="statistical",
            evidence_type=(
                EvidenceType.STATISTICAL_RESULT
            ),
            support_level=(
                EvidenceSupportLevel.DERIVED
            ),
            metric="flagged_rate",
            value="12.69%",
            detail=(
                "Derived flagged rate."
            ),
            available=True,
            confidence=0.90,
        ),
    ],
)

result = analyzer.analyze(
    derived_contract
)

derived_uncertainty = any(
    item.category
    == "DERIVED_EVIDENCE"
    for item
    in result.uncertainty.items
)

check(
    "Derived evidence creates uncertainty",
    derived_uncertainty,
    (
        f"items="
        f"{len(result.uncertainty.items)}"
    ),
)


# ============================================================
# TEST 11
# UNGROUNDED FINDING
# ============================================================

ungrounded_finding = InvestigationFinding(
    title=(
        "Payment root cause"
    ),
    severity="HIGH",
    metric="payment_failure",
    value=None,
    evidence_sources=[
        "payment_tool"
    ],
    evidence_ids=[],
    detail=(
        "No payment evidence was available."
    ),
)

result = analyzer.analyze(
    high_quality_contract,
    [ungrounded_finding],
)

ungrounded_uncertainty = any(
    item.category
    == "UNGROUNDED_FINDING"
    for item
    in result.uncertainty.items
)

check(
    "Ungrounded finding creates uncertainty",
    ungrounded_uncertainty,
    (
        f"items="
        f"{len(result.uncertainty.items)}"
    ),
)


# ============================================================
# TEST 12
# UNGROUNDED FINDING DOES NOT COUNT
# ============================================================

check(
    "Ungrounded finding is excluded from grounded count",
    result.confidence.grounded_finding_count == 0,
    (
        f"grounded="
        f"{result.confidence.grounded_finding_count}"
    ),
)


# ============================================================
# TEST 13
# EMPTY CONTRACT IS LOW CONFIDENCE
# ============================================================

empty_contract = EvidenceContract(
    version="1.0",
    evidence=[],
)

result = analyzer.analyze(
    empty_contract
)

check(
    "Empty evidence contract is LOW confidence",
    (
        result.confidence.level == "LOW"
        and
        result.confidence.score == 0.0
    ),
    (
        f"level="
        f"{result.confidence.level}; "
        f"score="
        f"{result.confidence.score}"
    ),
)


# ============================================================
# TEST 14
# SERIALIZATION
# ============================================================

serialized = (
    confidence_uncertainty_to_dict(
        result
    )
)

check(
    "Confidence and uncertainty are serializable",
    (
        isinstance(
            serialized,
            dict,
        )
        and
        "confidence"
        in serialized
        and
        "uncertainty"
        in serialized
        and
        "items"
        in serialized["uncertainty"]
    ),
    (
        f"keys="
        f"{list(serialized.keys())}"
    ),
)


# ============================================================
# TEST 15
# REQUIRED UNCERTAINTY CATEGORIES
# ============================================================

combined_contract = EvidenceContract(
    version="1.0",
    evidence=[
        EvidenceItem(
            evidence_id="available_direct",
            source="test_tool",
            category="metric",
            evidence_type=(
                EvidenceType.METRIC
            ),
            support_level=(
                EvidenceSupportLevel.DIRECT
            ),
            metric="metric_a",
            value=100,
            detail="Direct evidence.",
            available=True,
            confidence=1.0,
        ),
        EvidenceItem(
            evidence_id="available_derived",
            source="test_tool",
            category="metric",
            evidence_type=(
                EvidenceType.METRIC
            ),
            support_level=(
                EvidenceSupportLevel.DERIVED
            ),
            metric="metric_b",
            value=50,
            detail="Derived evidence.",
            available=True,
            confidence=0.90,
        ),
        EvidenceItem(
            evidence_id="unavailable_data",
            source="test_tool",
            category="missing",
            evidence_type=(
                EvidenceType.UNAVAILABLE
            ),
            support_level=(
                EvidenceSupportLevel.UNAVAILABLE
            ),
            available=False,
            value=None,
        ),
    ],
)

result = analyzer.analyze(
    combined_contract
)

categories = {
    item.category
    for item in result.uncertainty.items
}

check(
    "Uncertainty categories are classified",
    (
        "UNAVAILABLE_EVIDENCE"
        in categories
        and
        "DERIVED_EVIDENCE"
        in categories
    ),
    (
        f"categories="
        f"{sorted(categories)}"
    ),
)


# ============================================================
# FINAL SUMMARY
# ============================================================

failed_checks = (
    total_checks
    - passed_checks
)

pass_rate = (
    passed_checks
    / total_checks
    * 100
    if total_checks
    else 0.0
)

print()
print("=" * 60)
print(
    "DAY 11.6 — CONFIDENCE + UNCERTAINTY VALIDATION"
)
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

    print(
        "DAY 11.6 — PASSED"
    )

    print(
        "Confidence and uncertainty are "
        "deterministically validated."
    )

    sys.exit(0)

else:

    print(
        "DAY 11.6 — FAILED"
    )

    sys.exit(1)