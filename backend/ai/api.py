from __future__ import annotations

from typing import Any
from urllib.parse import unquote

from fastapi import (
    APIRouter,
    HTTPException,
)

from .engine import (
    InvestigationEngine,
)

from .llm import (
    LLMExplainer,
)

from .schemas import (
    InvestigationRequest,
    InvestigationResponse,
)

from .tools import (
    ToolExecutor,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/ai",
    tags=["AI Investigation"],
)


# ============================================================
# APPLICATION TRANSPORT
# ============================================================

class ApplicationTransport:

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        from backend import main as backend_main

        method = method.upper()

        params = params or {}

        json_body = json_body or {}


        # ====================================================
        # PROFILE
        # ====================================================

        if (
            method == "GET"
            and path == "/profile"
        ):

            customer_id = params.get(
                "customer_id"
            )


            if not customer_id:

                raise RuntimeError(
                    "customer_id is required."
                )


            result = backend_main.get_profile(
                customer_id=str(
                    customer_id
                )
            )


            return self._serialize(
                result
            )


        # ====================================================
        # JOURNEY
        # ====================================================

        if (
            method == "GET"
            and path.startswith(
                "/journey/"
            )
        ):

            booking_id = path.rsplit(
                "/",
                1,
            )[-1]


            booking_id = unquote(
                booking_id
            )


            result = backend_main.get_journey(
                booking_id=booking_id
            )


            return self._serialize(
                result
            )


        # ====================================================
        # KPI
        # ====================================================

        if (
            method == "GET"
            and path == "/kpis"
        ):

            result = backend_main.get_kpis()


            return self._serialize(
                result
            )


        # ====================================================
        # QUALITY
        # ====================================================

        if (
            method == "GET"
            and path == "/quality"
        ):

            result = backend_main.get_quality()


            return self._serialize(
                result
            )


        # ====================================================
        # DETERMINISTIC INVESTIGATION
        # ====================================================

        if (
            method == "POST"
            and path == "/investigate"
        ):

            request_model = (
                backend_main.InvestigationRequest(
                    **json_body
                )
            )


            result = backend_main.investigate(
                request=request_model
            )


            return self._serialize(
                result
            )


        # ====================================================
        # UNKNOWN
        # ====================================================

        raise RuntimeError(
            (
                "Application transport does not support "
                f"{method} {path}."
            )
        )


    # ========================================================
    # SERIALIZATION
    # ========================================================

    @staticmethod
    def _serialize(
        value: Any,
    ) -> dict[str, Any]:

        if hasattr(
            value,
            "model_dump",
        ):

            return value.model_dump(
                mode="json"
            )


        if isinstance(
            value,
            dict,
        ):

            return value


        raise RuntimeError(
            (
                "Backend endpoint returned an "
                "unsupported response type."
            )
        )


# ============================================================
# DETERMINISTIC TOOL EXECUTOR
# ============================================================

tool_executor = ToolExecutor(
    transport=ApplicationTransport()
)


# ============================================================
# LLM
# ============================================================

llm_explainer = LLMExplainer()


# ============================================================
# ENGINE
# ============================================================

engine = InvestigationEngine(
    tool_executor=tool_executor,

    llm_explainer=llm_explainer,
)


# ============================================================
# HEALTH
# ============================================================

@router.get(
    "/health"
)
def ai_health() -> dict[str, str]:

    return {

        "status":
            "ok",

        "service":
            "ai-investigation",
    }


# ============================================================
# INVESTIGATE
# ============================================================

@router.post(
    "/investigate",
    response_model=InvestigationResponse,
)
def ai_investigate(
    request: InvestigationRequest,
) -> InvestigationResponse:
    """
    Execute a deterministic investigation.

    include_explanation=false:
        Returns RESULTS_READY.

    include_explanation=true:
        Attempts LLM explanation and returns
        EXPLANATION_READY when successful.
    """

    try:

        return engine.execute_investigation(
            request
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "AI investigation failed."
            ),
        ) from exc