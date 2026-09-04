from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from .schemas import (
    EvidenceContract,
    EvidenceItem,
    EvidenceProvenance,
    EvidenceSupportLevel,
    EvidenceType,
    InvestigationFinding,
)


# ============================================================
# REGEX
# ============================================================

NUMBER_RE = re.compile(
    r"""
    (?<![A-Za-z0-9_])
    [-+]?
    (?:
        \d{1,3}(?:,\d{3})+
        |
        \d+(?:\.\d+)?
        |
        \.\d+
    )
    %?
    (?![A-Za-z0-9_])
    """,
    re.VERBOSE,
)

IDENTIFIER_RE = re.compile(
    r"\b(?:C|B)\d{3,}\b",
    re.IGNORECASE,
)


# ============================================================
# DAY 11.3 — CLAIM RESULT
# ============================================================

@dataclass
class ClaimValidationResult:
    """
    Result of validating one generated claim
    against deterministic evidence.
    """

    claim: str

    supported: bool

    matched_evidence_ids: list[str] = field(
        default_factory=list
    )

    matched_values: list[Any] = field(
        default_factory=list
    )

    unsupported_values: list[str] = field(
        default_factory=list
    )

    reason: str = ""


# ============================================================
# DAY 11.3 — GUARD RESULT
# ============================================================

@dataclass
class HallucinationGuardResult:
    """
    Collection-level hallucination validation result.
    """

    text: str

    supported: bool

    claims: list[ClaimValidationResult] = field(
        default_factory=list
    )

    unsupported_claims: list[str] = field(
        default_factory=list
    )

    evidence_ids_used: list[str] = field(
        default_factory=list
    )

    reason: str = ""


# ============================================================
# EVIDENCE GUARD
# ============================================================

class EvidenceGuard:
    """
    Evidence preparation and compatibility layer.

    This version is intentionally aligned with the CURRENT
    schemas.py from the project.

    It only uses fields/classes that actually exist in the
    current schema.
    """

    CONTRACT_VERSION = "1.0"

    # ========================================================
    # PREPARE EVIDENCE
    # ========================================================

    def prepare_evidence(
        self,
        evidence: list[EvidenceItem],
    ) -> EvidenceContract:
        """
        Build and validate the collection-level evidence
        contract.
        """

        self.assign_evidence_ids(
            evidence
        )

        self.attach_provenance(
            evidence
        )

        return EvidenceContract(
            version=self.CONTRACT_VERSION,
            evidence=evidence,
        )

    # ========================================================
    # ASSIGN EVIDENCE IDS
    # ========================================================

    @staticmethod
    def assign_evidence_ids(
        evidence: list[EvidenceItem],
    ) -> None:

        used_ids = {
            item.evidence_id
            for item in evidence
            if item.evidence_id
        }

        for index, item in enumerate(
            evidence,
            start=1,
        ):

            # Current schema already auto-generates
            # evidence_id, so preserve it.
            if item.evidence_id:
                continue

            basis = json.dumps(
                {
                    "source": item.source,
                    "category": item.category,
                    "metric": item.metric,
                    "value": item.value,
                    "detail": item.detail,
                },
                sort_keys=True,
                default=str,
            )

            digest = (
                __import__("hashlib")
                .sha1(
                    basis.encode("utf-8")
                )
                .hexdigest()[:10]
            )

            candidate = (
                f"EV{index:03d}_{digest}"
            )

            counter = index

            while candidate in used_ids:

                counter += 1

                candidate = (
                    f"EV{counter:03d}_{digest}"
                )

            # This branch normally won't execute because
            # EvidenceItem generates an ID itself.
            try:

                item.evidence_id = candidate

            except Exception:
                pass

            used_ids.add(
                item.evidence_id
            )

    # ========================================================
    # ATTACH PROVENANCE
    # ========================================================

    @staticmethod
    def attach_provenance(
        evidence: list[EvidenceItem],
    ) -> None:

        for item in evidence:

            if item.provenance is not None:
                continue

            item.provenance = EvidenceProvenance(
                source_type=(
                    EvidenceGuard.infer_source_type(
                        item.source
                    )
                ),
                source_name=item.source,
                field=item.metric,
                retrieval_reference=(
                    item.source_reference
                ),
                metadata={
                    "evidence_id": item.evidence_id,
                    "deterministic": True,
                    "contract_version": (
                        EvidenceGuard.CONTRACT_VERSION
                    ),
                },
            )

    # ========================================================
    # SOURCE TYPE INFERENCE
    # ========================================================

    @staticmethod
    def infer_source_type(
        source: str,
    ):
        """
        Infer ProvenanceSourceType without requiring
        additional schema changes.
        """

        from .schemas import ProvenanceSourceType

        normalized = (
            source.lower().strip()
        )

        if normalized.startswith("/"):
            return ProvenanceSourceType.API

        if (
            "tool" in normalized
            or "statistical" in normalized
            or "kpi" in normalized
            or "profile" in normalized
            or "journey" in normalized
        ):
            return ProvenanceSourceType.TOOL

        if (
            "table" in normalized
            or "sql" in normalized
        ):
            return ProvenanceSourceType.TABLE

        if (
            "dataset" in normalized
            or "csv" in normalized
            or "parquet" in normalized
        ):
            return ProvenanceSourceType.DATASET

        return ProvenanceSourceType.UNKNOWN

    # ========================================================
    # FINDING → EVIDENCE LINKS
    # ========================================================

    @staticmethod
    def link_finding_to_evidence(
        finding: InvestigationFinding,
        evidence: Iterable[EvidenceItem],
    ) -> list[str]:

        evidence_list = list(
            evidence
        )

        matching_ids: list[str] = []

        finding_metric = (
            str(
                finding.metric
            ).strip().lower()
            if finding.metric is not None
            else ""
        )

        for item in evidence_list:

            item_metric = (
                str(
                    item.metric
                ).strip().lower()
                if item.metric is not None
                else ""
            )

            metric_match = (
                not finding_metric
                or not item_metric
                or finding_metric == item_metric
                or finding_metric in item_metric
                or item_metric in finding_metric
            )

            source_match = (
                not finding.evidence_sources
                or item.source
                in finding.evidence_sources
            )

            if (
                metric_match
                and source_match
            ):

                matching_ids.append(
                    item.evidence_id
                )

        # Respect the current schema field.
        finding.evidence_ids = list(
            dict.fromkeys(
                matching_ids[:8]
            )
        )

        return finding.evidence_ids

    # ========================================================
    # CREATE CONTRACT
    # ========================================================

    @staticmethod
    def create_contract(
        evidence: list[EvidenceItem],
    ) -> EvidenceContract:

        return EvidenceContract(
            version=EvidenceGuard.CONTRACT_VERSION,
            evidence=evidence,
        )


# ============================================================
# DAY 11.3 — HALLUCINATION GUARD
# ============================================================

class HallucinationGuard:
    """
    Deterministic hallucination guard.

    Validates:
        - numbers
        - percentages
        - customer IDs
        - booking IDs
        - evidence IDs
        - source references
        - evidence text

    It never asks another LLM to validate an LLM.
    """

    def __init__(
        self,
        *,
        numeric_tolerance: float = 0.01,
        require_numeric_support: bool = True,
    ) -> None:

        if numeric_tolerance < 0:

            raise ValueError(
                "numeric_tolerance cannot be negative."
            )

        self.numeric_tolerance = (
            numeric_tolerance
        )

        self.require_numeric_support = (
            require_numeric_support
        )

    # ========================================================
    # MAIN VALIDATION
    # ========================================================

    def validate(
        self,
        text: str,
        evidence_contract: EvidenceContract,
    ) -> HallucinationGuardResult:

        if not text or not text.strip():

            return HallucinationGuardResult(
                text=text,
                supported=False,
                reason="LLM response is empty.",
            )

        available_evidence = [
            item
            for item in evidence_contract.evidence
            if item.available
        ]

        if not available_evidence:

            return HallucinationGuardResult(
                text=text,
                supported=False,
                reason=(
                    "No available evidence exists to "
                    "support the generated explanation."
                ),
            )

        claims = self._split_claims(
            text
        )

        results: list[
            ClaimValidationResult
        ] = []

        for claim in claims:

            results.append(
                self.validate_claim(
                    claim,
                    available_evidence,
                )
            )

        unsupported_claims = [
            result.claim
            for result in results
            if not result.supported
        ]

        evidence_ids_used = sorted(
            {
                evidence_id
                for result in results
                for evidence_id
                in result.matched_evidence_ids
            }
        )

        supported = (
            len(unsupported_claims)
            == 0
        )

        if supported:

            reason = (
                "All validated claims are supported "
                "by available investigation evidence."
            )

        else:

            reason = (
                f"{len(unsupported_claims)} claim(s) "
                "could not be deterministically "
                "grounded in available evidence."
            )

        return HallucinationGuardResult(
            text=text,
            supported=supported,
            claims=results,
            unsupported_claims=(
                unsupported_claims
            ),
            evidence_ids_used=(
                evidence_ids_used
            ),
            reason=reason,
        )

    # ========================================================
    # CLAIM VALIDATION
    # ========================================================

    def validate_claim(
        self,
        claim: str,
        evidence_items: Iterable[EvidenceItem],
    ) -> ClaimValidationResult:

        if not claim or not claim.strip():

            return ClaimValidationResult(
                claim=claim,
                supported=False,
                reason="Claim is empty.",
            )

        evidence_list = list(
            evidence_items
        )

        matched_evidence_ids: list[str] = []

        matched_values: list[Any] = []

        unsupported_values: list[str] = []

        # ----------------------------------------------------
        # NUMBERS
        # ----------------------------------------------------

        claim_numbers = (
            self._extract_numbers(
                claim
            )
        )

        evidence_numbers = (
            self._build_evidence_numbers(
                evidence_list
            )
        )

        if (
            self.require_numeric_support
            and claim_numbers
        ):

            for (
                token,
                number,
                is_percentage,
            ) in claim_numbers:

                matches = (
                    self._find_numeric_matches(
                        number=number,
                        is_percentage=is_percentage,
                        evidence_numbers=(
                            evidence_numbers
                        ),
                    )
                )

                if not matches:

                    unsupported_values.append(
                        token
                    )

                else:

                    for (
                        evidence_id,
                        original_value,
                    ) in matches:

                        if (
                            evidence_id
                            not in matched_evidence_ids
                        ):

                            matched_evidence_ids.append(
                                evidence_id
                            )

                        if (
                            original_value
                            not in matched_values
                        ):

                            matched_values.append(
                                original_value
                            )

        # ----------------------------------------------------
        # IDENTIFIERS
        # ----------------------------------------------------

        claim_identifiers = (
            self._extract_identifiers(
                claim
            )
        )

        identifier_index = (
            self._build_identifier_index(
                evidence_list
            )
        )

        unsupported_identifiers: list[str] = []

        for identifier in (
            claim_identifiers
        ):

            normalized_identifier = (
                identifier.lower()
            )

            matching_evidence = [
                evidence_id
                for (
                    evidence_id,
                    values,
                ) in identifier_index.items()
                if normalized_identifier
                in values
            ]

            if matching_evidence:

                for evidence_id in (
                    matching_evidence
                ):

                    if (
                        evidence_id
                        not in matched_evidence_ids
                    ):

                        matched_evidence_ids.append(
                            evidence_id
                        )

            else:

                unsupported_identifiers.append(
                    identifier
                )

        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        text_matches = (
            self._find_text_matches(
                self._normalize_text(
                    claim
                ),
                evidence_list,
            )
        )

        for evidence_id in (
            text_matches
        ):

            if (
                evidence_id
                not in matched_evidence_ids
            ):

                matched_evidence_ids.append(
                    evidence_id
                )

        # ----------------------------------------------------
        # UNSUPPORTED NUMBER
        # ----------------------------------------------------

        if unsupported_values:

            return ClaimValidationResult(
                claim=claim,
                supported=False,
                matched_evidence_ids=(
                    matched_evidence_ids
                ),
                matched_values=(
                    matched_values
                ),
                unsupported_values=(
                    unsupported_values
                ),
                reason=(
                    "Claim contains numeric value(s) "
                    "that cannot be matched to "
                    "available evidence."
                ),
            )

        # ----------------------------------------------------
        # UNSUPPORTED ID
        # ----------------------------------------------------

        if unsupported_identifiers:

            return ClaimValidationResult(
                claim=claim,
                supported=False,
                matched_evidence_ids=(
                    matched_evidence_ids
                ),
                matched_values=(
                    matched_values
                ),
                unsupported_values=(
                    unsupported_identifiers
                ),
                reason=(
                    "Claim contains identifier(s) "
                    "that are not present in "
                    "available evidence."
                ),
            )

        # ----------------------------------------------------
        # QUALITATIVE CLAIM
        # ----------------------------------------------------

        if (
            not claim_numbers
            and not claim_identifiers
        ):

            if text_matches:

                return ClaimValidationResult(
                    claim=claim,
                    supported=True,
                    matched_evidence_ids=(
                        matched_evidence_ids
                    ),
                    matched_values=(
                        matched_values
                    ),
                    reason=(
                        "Claim contains text grounded "
                        "in available evidence."
                    ),
                )

            return ClaimValidationResult(
                claim=claim,
                supported=False,
                matched_evidence_ids=(
                    matched_evidence_ids
                ),
                matched_values=(
                    matched_values
                ),
                reason=(
                    "Qualitative claim could not be "
                    "deterministically linked to "
                    "an evidence item."
                ),
            )

        # ----------------------------------------------------
        # SUPPORTED
        # ----------------------------------------------------

        return ClaimValidationResult(
            claim=claim,
            supported=True,
            matched_evidence_ids=(
                matched_evidence_ids
            ),
            matched_values=(
                matched_values
            ),
            reason=(
                "Claim values and identifiers are "
                "supported by available evidence."
            ),
        )

    # ========================================================
    # CLAIM SPLITTING
    # ========================================================

    @staticmethod
    def _split_claims(
        text: str,
    ) -> list[str]:

        parts = re.split(
            r"(?<=[.!?])\s+|\n+",
            text.strip(),
        )

        return [
            part.strip(
                " -•\t"
            )
            for part in parts
            if part.strip(
                " -•\t"
            )
        ]

    # ========================================================
    # NUMBER EXTRACTION
    # ========================================================

    def _extract_numbers(
        self,
        text: str,
    ) -> list[
        tuple[str, float, bool]
    ]:

        results: list[
            tuple[str, float, bool]
        ] = []

        for match in (
            NUMBER_RE.finditer(
                text
            )
        ):

            token = match.group(0)

            cleaned = token.replace(
                ",",
                "",
            )

            is_percentage = (
                cleaned.endswith("%")
            )

            numeric_text = (
                cleaned.rstrip("%")
            )

            try:

                number = float(
                    numeric_text
                )

            except ValueError:

                continue

            if not math.isfinite(
                number
            ):

                continue

            results.append(
                (
                    token,
                    number,
                    is_percentage,
                )
            )

        return results

    # ========================================================
    # BUILD EVIDENCE NUMBERS
    # ========================================================

    def _build_evidence_numbers(
        self,
        evidence_items: Iterable[EvidenceItem],
    ) -> list[
        tuple[str, float, bool, Any]
    ]:

        results: list[
            tuple[str, float, bool, Any]
        ] = []

        for item in evidence_items:

            self._collect_numbers(
                value=item.value,
                evidence_id=item.evidence_id,
                target=results,
            )

            if item.record_count is not None:

                self._collect_numbers(
                    value=item.record_count,
                    evidence_id=item.evidence_id,
                    target=results,
                )

            if item.detail:

                self._collect_numbers(
                    value=item.detail,
                    evidence_id=item.evidence_id,
                    target=results,
                )

            if item.metadata:

                self._collect_numbers(
                    value=item.metadata,
                    evidence_id=item.evidence_id,
                    target=results,
                )

            if item.provenance is not None:

                provenance = item.provenance

                if hasattr(
                    provenance,
                    "model_dump",
                ):

                    provenance = (
                        provenance.model_dump(
                            mode="json"
                        )
                    )

                self._collect_numbers(
                    value=provenance,
                    evidence_id=item.evidence_id,
                    target=results,
                )

        return results

    # ========================================================
    # RECURSIVE NUMBER COLLECTION
    # ========================================================

    def _collect_numbers(
        self,
        *,
        value: Any,
        evidence_id: str,
        target: list[
            tuple[str, float, bool, Any]
        ],
    ) -> None:

        if value is None:

            return

        if isinstance(
            value,
            bool,
        ):

            return

        if isinstance(
            value,
            int,
        ):

            target.append(
                (
                    evidence_id,
                    float(value),
                    False,
                    value,
                )
            )

            return

        if isinstance(
            value,
            float,
        ):

            if math.isfinite(
                value
            ):

                target.append(
                    (
                        evidence_id,
                        value,
                        False,
                        value,
                    )
                )

            return

        if isinstance(
            value,
            str,
        ):

            for (
                token,
                number,
                is_percentage,
            ) in self._extract_numbers(
                value
            ):

                target.append(
                    (
                        evidence_id,
                        number,
                        is_percentage,
                        value,
                    )
                )

            return

        if isinstance(
            value,
            dict,
        ):

            for nested_value in (
                value.values()
            ):

                self._collect_numbers(
                    value=nested_value,
                    evidence_id=evidence_id,
                    target=target,
                )

            return

        if isinstance(
            value,
            (list, tuple, set),
        ):

            for nested_value in value:

                self._collect_numbers(
                    value=nested_value,
                    evidence_id=evidence_id,
                    target=target,
                )

    # ========================================================
    # NUMERIC MATCHING
    # ========================================================

    def _find_numeric_matches(
        self,
        *,
        number: float,
        is_percentage: bool,
        evidence_numbers: list[
            tuple[str, float, bool, Any]
        ],
    ) -> list[
        tuple[str, Any]
    ]:

        matches: list[
            tuple[str, Any]
        ] = []

        for (
            evidence_id,
            evidence_number,
            evidence_is_percentage,
            original_value,
        ) in evidence_numbers:

            # ----------------------------------------------
            # PERCENTAGE CLAIM
            # ----------------------------------------------

            if is_percentage:

                # 12.69% ↔ "12.69%"
                direct_match = (
                    evidence_is_percentage
                    and self._numbers_equal(
                        number,
                        evidence_number,
                    )
                )

                # 12.69% ↔ 0.1269
                decimal_match = (
                    not evidence_is_percentage
                    and self._numbers_equal(
                        number / 100.0,
                        evidence_number,
                    )
                )

                if (
                    direct_match
                    or decimal_match
                ):

                    matches.append(
                        (
                            evidence_id,
                            original_value,
                        )
                    )

                continue

            # ----------------------------------------------
            # NORMAL NUMBER CLAIM
            # ----------------------------------------------

            # Don't match 12.69 with 12.69%.
            if evidence_is_percentage:

                continue

            if self._numbers_equal(
                number,
                evidence_number,
            ):

                matches.append(
                    (
                        evidence_id,
                        original_value,
                    )
                )

        return matches

    # ========================================================
    # NUMBER COMPARISON
    # ========================================================

    def _numbers_equal(
        self,
        left: float,
        right: float,
    ) -> bool:

        absolute_difference = abs(
            left - right
        )

        if (
            absolute_difference
            <= self.numeric_tolerance
        ):

            return True

        scale = max(
            abs(left),
            abs(right),
            1.0,
        )

        relative_difference = (
            absolute_difference
            /
            scale
        )

        return (
            relative_difference
            <= self.numeric_tolerance
        )

    # ========================================================
    # IDENTIFIER EXTRACTION
    # ========================================================

    @staticmethod
    def _extract_identifiers(
        text: str,
    ) -> list[str]:

        return list(
            dict.fromkeys(
                IDENTIFIER_RE.findall(
                    text
                )
            )
        )

    # ========================================================
    # IDENTIFIER INDEX
    # ========================================================

    def _build_identifier_index(
        self,
        evidence_items: Iterable[EvidenceItem],
    ) -> dict[
        str,
        set[str],
    ]:

        result: dict[
            str,
            set[str],
        ] = {}

        for item in evidence_items:

            values: set[str] = set()

            values.add(
                item.evidence_id.lower()
            )

            if item.source:

                values.add(
                    item.source.lower()
                )

            if item.metric:

                values.add(
                    item.metric.lower()
                )

            if item.source_reference:

                values.add(
                    item.source_reference.lower()
                )

            if item.detail:

                for identifier in (
                    self._extract_identifiers(
                        item.detail
                    )
                ):

                    values.add(
                        identifier.lower()
                    )

            self._collect_identifiers(
                item.value,
                values,
            )

            if item.metadata:

                self._collect_identifiers(
                    item.metadata,
                    values,
                )

            if item.provenance is not None:

                provenance = item.provenance

                if hasattr(
                    provenance,
                    "model_dump",
                ):

                    provenance = (
                        provenance.model_dump(
                            mode="json"
                        )
                    )

                self._collect_identifiers(
                    provenance,
                    values,
                )

            result[
                item.evidence_id
            ] = values

        return result

    # ========================================================
    # IDENTIFIER COLLECTION
    # ========================================================

    def _collect_identifiers(
        self,
        value: Any,
        target: set[str],
    ) -> None:

        if value is None:

            return

        if isinstance(
            value,
            str,
        ):

            for identifier in (
                self._extract_identifiers(
                    value
                )
            ):

                target.add(
                    identifier.lower()
                )

            return

        if isinstance(
            value,
            dict,
        ):

            for nested in (
                value.values()
            ):

                self._collect_identifiers(
                    nested,
                    target,
                )

            return

        if isinstance(
            value,
            (list, tuple, set),
        ):

            for nested in value:

                self._collect_identifiers(
                    nested,
                    target,
                )

    # ========================================================
    # TEXT MATCHING
    # ========================================================

    def _find_text_matches(
        self,
        normalized_claim: str,
        evidence_items: Iterable[EvidenceItem],
    ) -> list[str]:

        matches: list[str] = []

        for item in evidence_items:

            candidates: list[str] = []

            if item.detail:

                candidates.append(
                    item.detail
                )

            if item.metric:

                candidates.append(
                    item.metric
                )

            if item.source:

                candidates.append(
                    item.source
                )

            if item.source_reference:

                candidates.append(
                    str(
                        item.source_reference
                    )
                )

            if item.provenance is not None:

                provenance = item.provenance

                if hasattr(
                    provenance,
                    "model_dump",
                ):

                    provenance = (
                        provenance.model_dump(
                            mode="json"
                        )
                    )

                if isinstance(
                    provenance,
                    dict,
                ):

                    for key in (
                        "source",
                        "category",
                        "metric",
                        "tool",
                        "tool_name",
                        "field",
                    ):

                        value = provenance.get(
                            key
                        )

                        if value:

                            candidates.append(
                                str(value)
                            )

            for candidate in candidates:

                normalized_candidate = (
                    self._normalize_text(
                        candidate
                    )
                )

                if not normalized_candidate:

                    continue

                if (
                    normalized_candidate
                    in normalized_claim
                    or
                    normalized_claim
                    in normalized_candidate
                ):

                    matches.append(
                        item.evidence_id
                    )

                    break

        return matches

    # ========================================================
    # TEXT NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:

        return re.sub(
            r"\s+",
            " ",
            text.strip().lower(),
        )

    # ========================================================
    # SERIALIZATION
    # ========================================================

    @staticmethod
    def to_dict(
        result: HallucinationGuardResult,
    ) -> dict[str, Any]:

        return {
            "text": result.text,
            "supported": result.supported,
            "unsupported_claims": (
                result.unsupported_claims
            ),
            "evidence_ids_used": (
                result.evidence_ids_used
            ),
            "reason": result.reason,
            "claims": [
                {
                    "claim": claim.claim,
                    "supported": claim.supported,
                    "matched_evidence_ids": (
                        claim.matched_evidence_ids
                    ),
                    "matched_values": (
                        claim.matched_values
                    ),
                    "unsupported_values": (
                        claim.unsupported_values
                    ),
                    "reason": claim.reason,
                }
                for claim in result.claims
            ],
        }

    @staticmethod
    def to_json(
        result: HallucinationGuardResult,
    ) -> str:

        return json.dumps(
            HallucinationGuard.to_dict(
                result
            ),
            indent=2,
            default=str,
        )