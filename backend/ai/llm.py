from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


# ============================================================
# PROJECT ENVIRONMENT
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


load_dotenv(
    PROJECT_ROOT / ".env"
)


# ============================================================
# DEFAULT GEMINI MODELS
# ============================================================

DEFAULT_PRIMARY_MODEL = (
    "gemini-3.7-flash"
)


DEFAULT_FALLBACK_MODEL = (
    "gemini-2.5-flash-lite"
)


# ============================================================
# RETRY CONFIGURATION
# ============================================================

DEFAULT_MAX_RETRIES = 2

DEFAULT_RETRY_DELAYS = (
    1.5,
    3.0,
)


# ============================================================
# LLM EXPLAINER
# ============================================================

class LLMExplainer:
    """
    Gemini-backed explanation layer.

    Deterministic analytics are completed before this class
    is called. Gemini only explains the already validated
    investigation evidence.

    Reliability behavior:

        Primary model
              |
              +-- 503 --> retry
              |
              +-- 429 --> quota error
              |
              +-- other transient error --> retry
              |
              +-- final failure --> fallback model
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        fallback_model: str | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:

        self.api_key = (
            api_key
            or os.getenv(
                "GEMINI_API_KEY"
            )
        )


        self.model = (
            model
            or os.getenv(
                "GEMINI_MODEL",
                DEFAULT_PRIMARY_MODEL,
            )
        )


        self.fallback_model = (
            fallback_model
            or os.getenv(
                "GEMINI_FALLBACK_MODEL",
                DEFAULT_FALLBACK_MODEL,
            )
        )


        self.provider = "gemini"


        self.max_retries = max(
            0,
            int(
                max_retries
            ),
        )


        self.client = None


        # ----------------------------------------------------
        # Create Gemini client
        # ----------------------------------------------------

        if self.api_key:

            try:

                from google import genai

                self.client = (
                    genai.Client(
                        api_key=self.api_key
                    )
                )

            except ImportError as exc:

                raise RuntimeError(
                    (
                        "google-genai is not installed. "
                        "Run: pip install -U google-genai"
                    )
                ) from exc


    # ========================================================
    # CONFIGURED
    # ========================================================

    @property
    def configured(self) -> bool:

        return bool(
            self.api_key
            and self.client
        )


    # ========================================================
    # GENERATE
    # ========================================================

    def generate(
        self,
        context: dict[str, Any],
    ) -> str:

        if not self.api_key:

            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )


        if self.client is None:

            raise RuntimeError(
                (
                    "Gemini client is unavailable. "
                    "Install google-genai with: "
                    "pip install -U google-genai"
                )
            )


        system_instruction = """
You are the explanation layer of Journey Forensics.

Your job is to explain validated deterministic
investigation evidence to a business analyst.

STRICT RULES:

1. Use ONLY the evidence supplied in the context.
2. Never invent values, causes, customers, events,
   metrics, or business facts.
3. Do not perform new analytics.
4. Do not contradict deterministic evidence.
5. Clearly distinguish facts from interpretation.
6. Mention important unavailable or failed evidence.
7. Keep the explanation concise and professional.
8. Explain what happened and what evidence supports it.
9. Recommend the next investigation using only the
   available evidence.
10. Never claim unsupported metrics are available.

Use exactly these sections:

Finding:
Evidence:
Interpretation:
Next investigation:
""".strip()


        context_json = json.dumps(
            context,
            ensure_ascii=False,
            default=str,
        )


        prompt = (
            f"{system_instruction}\n\n"
            "STRUCTURED INVESTIGATION CONTEXT:\n"
            f"{context_json}"
        )


        # ----------------------------------------------------
        # Primary model
        # ----------------------------------------------------

        primary_error: Exception | None = None


        try:

            return self._generate_with_retries(
                model=self.model,
                prompt=prompt,
            )

        except Exception as exc:

            primary_error = exc


        # ----------------------------------------------------
        # Fallback model
        # ----------------------------------------------------

        if (
            self.fallback_model
            and self.fallback_model
            != self.model
        ):

            try:

                return self._generate_with_retries(
                    model=self.fallback_model,
                    prompt=prompt,
                )

            except Exception as fallback_error:

                raise RuntimeError(
                    (
                        "Gemini explanation failed on both "
                        "primary and fallback models.\n"
                        f"Primary ({self.model}): "
                        f"{primary_error}\n"
                        f"Fallback ({self.fallback_model}): "
                        f"{fallback_error}"
                    )
                ) from fallback_error


        raise RuntimeError(
            (
                "Gemini explanation failed using "
                f"model '{self.model}': "
                f"{primary_error}"
            )
        )


    # ========================================================
    # RETRY WRAPPER
    # ========================================================

    def _generate_with_retries(
        self,
        model: str,
        prompt: str,
    ) -> str:

        last_error: Exception | None = None


        # total attempts = initial + retries
        attempts = (
            self.max_retries
            + 1
        )


        for attempt in range(
            attempts
        ):

            try:

                return self._generate_once(
                    model=model,
                    prompt=prompt,
                )


            except Exception as exc:

                last_error = exc


                # --------------------------------------------
                # Do not retry quota errors
                # --------------------------------------------

                if self._is_quota_error(
                    exc
                ):

                    raise RuntimeError(
                        (
                            f"Gemini quota unavailable for "
                            f"model '{model}': {exc}"
                        )
                    ) from exc


                # --------------------------------------------
                # Last attempt
                # --------------------------------------------

                if (
                    attempt
                    >=
                    attempts - 1
                ):

                    break


                # --------------------------------------------
                # Retry transient errors
                # --------------------------------------------

                delay_index = min(
                    attempt,
                    len(
                        DEFAULT_RETRY_DELAYS
                    ) - 1,
                )


                delay = (
                    DEFAULT_RETRY_DELAYS[
                        delay_index
                    ]
                )


                time.sleep(
                    delay
                )


        raise RuntimeError(
            (
                f"Gemini model '{model}' "
                f"failed after {attempts} attempts: "
                f"{last_error}"
            )
        ) from last_error


    # ========================================================
    # SINGLE GEMINI REQUEST
    # ========================================================

    def _generate_once(
        self,
        model: str,
        prompt: str,
    ) -> str:

        try:

            response = (
                self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
            )

        except Exception as exc:

            raise RuntimeError(
                (
                    f"Gemini request failed for "
                    f"model '{model}': {exc}"
                )
            ) from exc


        text = getattr(
            response,
            "text",
            None,
        )


        if (
            not isinstance(
                text,
                str,
            )
            or not text.strip()
        ):

            raise RuntimeError(
                (
                    f"Gemini model '{model}' "
                    "returned no text explanation."
                )
            )


        return text.strip()


    # ========================================================
    # ERROR CLASSIFICATION
    # ========================================================

    @staticmethod
    def _is_quota_error(
        exc: Exception,
    ) -> bool:

        message = str(
            exc
        ).lower()


        quota_signals = (
            "429",
            "resource exhausted",
            "quota",
            "rate limit",
            "too many requests",
            "credit_balance_exhausted",
            "insufficient_quota",
        )


        return any(
            signal in message
            for signal in quota_signals
        )


# ============================================================
# DETERMINISTIC TEST EXPLAINER
# ============================================================

class DeterministicTestExplainer:
    """
    Offline explanation implementation.

    This is intentionally kept separate from Gemini so that
    Day 10 validation never requires a paid API call.
    """

    configured = True

    model = (
        "deterministic-test-model"
    )

    provider = (
        "deterministic-test"
    )


    def generate(
        self,
        context: dict[str, Any],
    ) -> str:

        question = str(
            context.get(
                "question",
                "the investigation",
            )
        )


        statistical = context.get(
            "statistical_evidence",
            [],
        )


        findings = context.get(
            "findings",
            [],
        )


        lines = [

            "Finding:",

            (
                f"The investigation addressed: "
                f"{question}"
            ),

            "",

            "Evidence:",
        ]


        if statistical:

            first = statistical[0]


            metric = first.get(
                "metric",
                "the selected metric",
            )


            records = first.get(
                "record_count"
            )


            flagged = first.get(
                "flagged_count"
            )


            threshold = first.get(
                "threshold"
            )


            lines.append(
                (
                    f"{metric} was evaluated across "
                    f"{records} records."
                )
            )


            if (
                flagged is not None
                and threshold is not None
            ):

                lines.append(
                    (
                        f"{flagged} records met or exceeded "
                        f"the threshold of {threshold}."
                    )
                )


        elif findings:

            lines.append(
                str(
                    findings[0]
                )
            )

        else:

            lines.append(
                "No statistical evidence was available."
            )


        lines.extend(
            [

                "",

                "Interpretation:",

                (
                    "The explanation is grounded only "
                    "in deterministic investigation "
                    "evidence."
                ),

                "",

                "Next investigation:",

                (
                    "Review the highest-priority evidence "
                    "and associated source records."
                ),
            ]
        )


        return "\n".join(
            lines
        )