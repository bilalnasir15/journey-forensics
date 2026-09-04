from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from .schemas import EvidenceContract, EvidenceItem


# ============================================================
# RESULT MODELS
# ============================================================


@dataclass
class ClaimValidationResult:
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


@dataclass
class HallucinationGuardResult:
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
# HALLUCINATION GUARD
# ============================================================


class HallucinationGuard:
    """
    Deterministic guard for validating factual claims
    against the available evidence contract.

    Supported checks:
        - numeric values
        - percentages
        - customer IDs
        - booking IDs
        - source references
        - evidence IDs
        - evidence text
    """

    NUMBER_PATTERN = re.compile(
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

    IDENTIFIER_PATTERN = re.compile(
        r"\b(?:C|B|T|P|E|EV|ev)[A-Za-z0-9_-]+\b"
    )

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

        self.numeric_tolerance = numeric_tolerance

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

        claims = self._split_claims(text)

        claim_results: list[
            ClaimValidationResult
        ] = []

        for claim in claims:

            claim_result = self.validate_claim(
                claim,
                available_evidence,
            )

            claim_results.append(
                claim_result
            )

        unsupported_claims = [
            result.claim
            for result in claim_results
            if not result.supported
        ]

        evidence_ids_used = sorted(
            {
                evidence_id
                for result in claim_results
                for evidence_id
                in result.matched_evidence_ids
            }
        )

        supported = (
            len(unsupported_claims) == 0
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
            claims=claim_results,
            unsupported_claims=unsupported_claims,
            evidence_ids_used=evidence_ids_used,
            reason=reason,
        )

    # ========================================================
    # SINGLE CLAIM
    # ========================================================

    def validate_claim(
        self,
        claim: str,
        evidence_items: Iterable[EvidenceItem],
    ) -> ClaimValidationResult:

        evidence_list = list(
            evidence_items
        )

        if not claim or not claim.strip():

            return ClaimValidationResult(
                claim=claim,
                supported=False,
                reason="Claim is empty.",
            )

        matched_evidence_ids: list[str] = []

        matched_values: list[Any] = []

        unsupported_values: list[str] = []

        # ----------------------------------------------------
        # NUMBERS
        # ----------------------------------------------------

        claim_numbers = self._extract_numbers(
            claim
        )

        if (
            self.require_numeric_support
            and claim_numbers
        ):

            evidence_numbers = (
                self._build_evidence_numbers(
                    evidence_list
                )
            )

            for (
                token,
                number,
                is_percentage,
            ) in claim_numbers:

                matches = (
                    self._find_numeric_matches(
                        number=number,
                        is_percentage=is_percentage,
                        evidence_numbers=evidence_numbers,
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

        evidence_identifier_index = (
            self._build_identifier_index(
                evidence_list
            )
        )

        unsupported_identifiers: list[str] = []

        for identifier in claim_identifiers:

            normalized = (
                identifier.lower()
            )

            matched_ids = [
                evidence_id
                for evidence_id, values
                in evidence_identifier_index.items()
                if normalized in values
            ]

            if matched_ids:

                for evidence_id in matched_ids:

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
        # TEXT MATCH
        # ----------------------------------------------------

        text_matches = (
            self._find_text_matches(
                self._normalize_text(claim),
                evidence_list,
            )
        )

        for evidence_id in text_matches:

            if (
                evidence_id
                not in matched_evidence_ids
            ):

                matched_evidence_ids.append(
                    evidence_id
                )

        # ----------------------------------------------------
        # FAIL: UNSUPPORTED NUMBER
        # ----------------------------------------------------

        if unsupported_values:

            return ClaimValidationResult(
                claim=claim,
                supported=False,
                matched_evidence_ids=(
                    matched_evidence_ids
                ),
                matched_values=matched_values,
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
        # FAIL: UNSUPPORTED ID
        # ----------------------------------------------------

        if unsupported_identifiers:

            return ClaimValidationResult(
                claim=claim,
                supported=False,
                matched_evidence_ids=(
                    matched_evidence_ids
                ),
                matched_values=matched_values,
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
                    matched_values=matched_values,
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
                matched_values=matched_values,
                reason=(
                    "Qualitative claim could not be "
                    "deterministically linked to "
                    "available evidence."
                ),
            )

        # ----------------------------------------------------
        # PASS
        # ----------------------------------------------------

        return ClaimValidationResult(
            claim=claim,
            supported=True,
            matched_evidence_ids=(
                matched_evidence_ids
            ),
            matched_values=matched_values,
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
            part.strip(" -•\t")
            for part in parts
            if part.strip(" -•\t")
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

        for match in self.NUMBER_PATTERN.finditer(
            text
        ):

            token = match.group(0)

            clean = token.replace(
                ",",
                "",
            )

            is_percentage = (
                clean.endswith("%")
            )

            number_text = (
                clean.rstrip("%")
            )

            try:

                number = float(
                    number_text
                )

            except ValueError:

                continue

            if not math.isfinite(number):

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

                self._collect_numbers(
                    value=item.provenance.model_dump(
                        mode="json"
                    ),
                    evidence_id=item.evidence_id,
                    target=results,
                )

        return results

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

        if isinstance(value, bool):

            return

        if isinstance(value, int):

            target.append(
                (
                    evidence_id,
                    float(value),
                    False,
                    value,
                )
            )

            return

        if isinstance(value, float):

            if math.isfinite(value):

                target.append(
                    (
                        evidence_id,
                        value,
                        False,
                        value,
                    )
                )

            return

        if isinstance(value, str):

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

        if isinstance(value, dict):

            for nested in value.values():

                self._collect_numbers(
                    value=nested,
                    evidence_id=evidence_id,
                    target=target,
                )

            return

        if isinstance(
            value,
            (list, tuple, set),
        ):

            for nested in value:

                self._collect_numbers(
                    value=nested,
                    evidence_id=evidence_id,
                    target=target,
                )

    # ========================================================
    # NUMERIC MATCH
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

            # ------------------------------------------------
            # CLAIM IS PERCENTAGE
            # ------------------------------------------------

            if is_percentage:

                # 12.69% ↔ evidence "12.69%"
                direct_match = (
                    evidence_is_percentage
                    and self._numbers_equal(
                        number,
                        evidence_number,
                    )
                )

                # 12.69% ↔ evidence 0.1269
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

            # ------------------------------------------------
            # CLAIM IS NORMAL NUMBER
            # ------------------------------------------------

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
    # NUMERIC EQUALITY
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

        denominator = max(
            abs(left),
            abs(right),
            1.0,
        )

        relative_difference = (
            absolute_difference
            / denominator
        )

        return (
            relative_difference
            <= self.numeric_tolerance
        )

    # ========================================================
    # IDENTIFIERS
    # ========================================================

    def _extract_identifiers(
        self,
        text: str,
    ) -> list[str]:

        return list(
            dict.fromkeys(
                self.IDENTIFIER_PATTERN.findall(
                    text
                )
            )
        )

    def _build_identifier_index(
        self,
        evidence_items: Iterable[EvidenceItem],
    ) -> dict[str, set[str]]:

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

            self._collect_identifiers(
                item.metadata,
                values,
            )

            if item.provenance:

                self._collect_identifiers(
                    item.provenance.model_dump(
                        mode="json"
                    ),
                    values,
                )

            result[
                item.evidence_id
            ] = values

        return result

    def _collect_identifiers(
        self,
        value: Any,
        target: set[str],
    ) -> None:

        if value is None:

            return

        if isinstance(value, str):

            for identifier in (
                self._extract_identifiers(
                    value
                )
            ):

                target.add(
                    identifier.lower()
                )

            return

        if isinstance(value, dict):

            for nested in value.values():

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

            if item.source_reference:

                candidates.append(
                    item.source_reference
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