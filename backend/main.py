import math
import os
import uuid
from io import BytesIO

import pandas as pd

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
)

from fastapi.exceptions import RequestValidationError

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse

from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.models import (
    CustomerListResponse,
    CustomerResponse,
    ErrorResponse,
    InvestigationRequest,
    InvestigationResponse,
    JourneyResponse,
    KPIListResponse,
    KPIResponse,
    ProfileResponse,
    QualityDatasetResponse,
    QualityResponse,
    UploadResponse,
)


# ============================================================
# BASE DIRECTORIES
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed",
)


UPLOAD_DIR = os.path.join(
    BASE_DIR,
    "data",
    "uploads",
)


# ============================================================
# DATA FILES
# ============================================================

PROFILE_FILE = os.path.join(
    PROCESSED_DIR,
    "day7_customer_segmentation_final.csv",
)


JOURNEY_FILE = os.path.join(
    PROCESSED_DIR,
    "customer_journey_features.csv",
)


KPI_FILE = os.path.join(
    PROCESSED_DIR,
    "day5_kpi_report.csv",
)


QUALITY_FILE = os.path.join(
    PROCESSED_DIR,
    "data_quality_report.csv",
)


# ============================================================
# CONFIGURATION
# ============================================================

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024


# ============================================================
# INVESTIGATION METRICS
# ============================================================

INVESTIGATION_METRICS = {
    "booking_amount": "booking_amount",
    "payment_attempts": "payment_attempts",
    "failed_payments": "failed_payments",
    "successful_payments": "successful_payments",
    "retry_count": "retry_count",
    "payment_success_rate": "payment_success_rate",
    "total_events": "total_events",
    "journey_duration_minutes": "journey_duration_minutes",
    "payment_duration_minutes": "payment_duration_minutes",
    "friction_score": "friction_score",
}


# ============================================================
# KPI DEFINITIONS
# ============================================================

KPI_DEFINITIONS = {

    "TOTAL_CUSTOMERS":
        "Total number of customers in the dataset.",

    "TOTAL_BOOKINGS":
        "Total number of bookings.",

    "TOTAL_PAYMENT_ATTEMPTS":
        "Total number of payment attempts.",

    "TOTAL_EVENTS":
        "Total number of recorded journey events.",

    "BOOKING_CONVERSION_RATE":
        "Share of bookings relative to the defined booking population.",

    "BOOKING_CONFIRMATION_RATE":
        "Share of bookings that reached confirmed status.",

    "CANCELLATION_RATE":
        "Share of bookings that were cancelled.",

    "PAYMENT_SUCCESS_RATE":
        "Share of payment attempts that completed successfully.",

    "PAYMENT_FAILURE_RATE":
        "Share of payment attempts that failed.",

    "RETRY_RATE":
        "Share of payment attempts associated with retries.",

    "BOOKING_RETRY_RATE":
        "Share of bookings requiring payment retries.",

    "REPEAT_CUSTOMER_RATE":
        "Share of customers with at least two bookings.",

    "RETENTION_PROXY_RATE":
        "Proxy retention metric based on repeat-customer behavior.",

    "TOTAL_REVENUE":
        "Total booking revenue.",

    "REVENUE_PER_CUSTOMER":
        "Average booking revenue per customer.",

    "AVERAGE_BOOKING_VALUE":
        "Average monetary value of a booking.",

    "ANOMALY_RATE":
        "Share of journeys containing a detected anomaly.",

    "AVERAGE_JOURNEY_DURATION":
        "Average journey duration in minutes.",

    "AVERAGE_PAYMENT_DURATION":
        "Average payment duration in minutes.",

    "AVERAGE_FRICTION_SCORE":
        "Average journey friction score.",

    "COMPLAINT_RATE":
        "Complaint rate; unavailable because complaint data is not present.",

    "COMPLAINT_RESOLUTION_TIME":
        "Complaint resolution time; unavailable because complaint data is not present.",
}


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Journey Forensics API",
    description="Backend API for the Journey Forensics project",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DIRECTORY INITIALIZATION
# ============================================================

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True,
)


# ============================================================
# ERROR RESPONSE BUILDER
# ============================================================

def build_error_response(
    error: str,
    message: str,
    status_code: int,
    path: str,
):
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error,
            "message": message,
            "status_code": status_code,
            "path": path,
        },
    )


# ============================================================
# HTTP ERROR HANDLER
# ============================================================

@app.exception_handler(
    StarletteHTTPException
)
async def starlette_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):

    message = (
        exc.detail
        if isinstance(
            exc.detail,
            str,
        )
        else str(
            exc.detail,
        )
    )

    return build_error_response(
        error="HTTP_ERROR",
        message=message,
        status_code=exc.status_code,
        path=request.url.path,
    )


# ============================================================
# VALIDATION ERROR HANDLER
# ============================================================

@app.exception_handler(
    RequestValidationError
)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):

    return build_error_response(
        error="VALIDATION_ERROR",
        message="Request validation failed.",
        status_code=422,
        path=request.url.path,
    )


# ============================================================
# GENERAL ERROR HANDLER
# ============================================================

@app.exception_handler(
    Exception
)
async def general_exception_handler(
    request: Request,
    exc: Exception,
):

    return build_error_response(
        error="INTERNAL_SERVER_ERROR",
        message="An unexpected internal error occurred.",
        status_code=500,
        path=request.url.path,
    )


# ============================================================
# PROFILE LOADER
# ============================================================

def load_profile_data():

    if not os.path.isfile(
        PROFILE_FILE
    ):
        raise FileNotFoundError(
            "Customer profile dataset not found."
        )


    df = pd.read_csv(
        PROFILE_FILE
    )


    if "customer_id" not in df.columns:

        raise ValueError(
            "customer_id column is missing from customer profile dataset."
        )


    return df


# ============================================================
# JOURNEY LOADER
# ============================================================

def load_journey_data():

    if not os.path.isfile(
        JOURNEY_FILE
    ):
        raise FileNotFoundError(
            "Journey dataset not found."
        )


    df = pd.read_csv(
        JOURNEY_FILE
    )


    required_columns = [
        "booking_id",
        "customer_id",
    ]


    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]


    if missing:

        raise ValueError(
            f"Missing journey columns: {missing}"
        )


    return df


# ============================================================
# KPI LOADER
# ============================================================

def load_kpi_data():

    if not os.path.isfile(
        KPI_FILE
    ):
        raise FileNotFoundError(
            "KPI dataset not found."
        )


    df = pd.read_csv(
        KPI_FILE
    )


    required_columns = [
        "kpi_name",
        "value",
        "unit",
        "status",
    ]


    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]


    if missing:

        raise ValueError(
            f"Missing KPI columns: {missing}"
        )


    return df


# ============================================================
# QUALITY LOADER
# ============================================================

def load_quality_data():

    if not os.path.isfile(
        QUALITY_FILE
    ):
        raise FileNotFoundError(
            "Data quality report not found."
        )


    df = pd.read_csv(
        QUALITY_FILE
    )


    required_columns = [
        "dataset",
        "rows",
        "expected_rows",
        "row_count_status",
        "columns",
        "missing_cells",
        "missing_percentage",
        "columns_with_missing",
        "duplicate_rows",
        "duplicate_percentage",
        "unique_values",
        "cardinality_percentage",
        "numeric_columns",
        "object_columns",
        "string_columns",
        "datetime_like_columns",
        "invalid_values",
        "invalid_percentage",
        "quality_score",
        "quality_status",
    ]


    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]


    if missing:

        raise ValueError(
            f"Missing quality columns: {missing}"
        )


    return df


# ============================================================
# SAFE VALUE HELPERS
# ============================================================

def safe_float(
    row,
    column,
    default=None,
):

    value = row.get(
        column,
        default,
    )


    if pd.isna(
        value
    ):
        return default


    return float(
        value
    )


def safe_int(
    row,
    column,
    default=0,
):

    value = row.get(
        column,
        default,
    )


    if pd.isna(
        value
    ):
        return default


    return int(
        float(
            value
        )
    )


def safe_string(
    row,
    column,
    default=None,
):

    value = row.get(
        column,
        default,
    )


    if pd.isna(
        value
    ):
        return default


    return str(
        value
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "project": "Journey Forensics",
        "service": "FastAPI Backend",
        "status": "running",
        "version": "1.0.0",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# PROFILE
# ============================================================

@app.get(
    "/profile",
    response_model=ProfileResponse,
)
def get_profile(
    customer_id: str,
):

    try:

        df = load_profile_data()

    except (
        FileNotFoundError,
        ValueError,
    ) as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


    customer = df[
        df["customer_id"].astype(str)
        ==
        str(customer_id)
    ]


    if customer.empty:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Customer '{customer_id}' "
                f"was not found."
            ),
        )


    row = customer.iloc[0]


    cluster_value = row.get(
        "cluster_id"
    )


    cluster_id = (
        None
        if pd.isna(cluster_value)
        else int(
            float(
                cluster_value
            )
        )
    )


    cohort_value = row.get(
        "cohort_month"
    )


    cohort_month = (
        None
        if pd.isna(cohort_value)
        else str(
            cohort_value
        )
    )


    return ProfileResponse(

        customer_id=str(
            row[
                "customer_id"
            ]
        ),

        total_bookings=safe_float(
            row,
            "total_bookings",
            0.0,
        ),

        total_revenue=safe_float(
            row,
            "total_revenue",
            0.0,
        ),

        average_booking_value=safe_float(
            row,
            "average_booking_value",
            0.0,
        ),

        recency_days=safe_float(
            row,
            "recency_days",
            0.0,
        ),

        booking_frequency=safe_float(
            row,
            "booking_frequency",
            0.0,
        ),

        repeat_booking_flag=safe_int(
            row,
            "repeat_booking_flag",
            0,
        ),

        customer_segment=safe_string(
            row,
            "customer_segment",
            "OTHER",
        ),

        segment_reason=safe_string(
            row,
            "segment_reason",
            "",
        ),

        cohort_month=cohort_month,

        cluster_id=cluster_id,

        complaint_segment_status=safe_string(
            row,
            "complaint_segment_status",
            "NOT_SUPPORTED",
        ),

        segmentation_status=safe_string(
            row,
            "segmentation_status",
            "READY",
        ),

        segmentation_method=safe_string(
            row,
            "segmentation_method",
            "",
        ),
    )


# ============================================================
# CUSTOMERS
# ============================================================

@app.get(
    "/customers",
    response_model=CustomerListResponse,
)
def get_customers(

    page: int = Query(
        1,
        ge=1,
    ),

    page_size: int = Query(
        50,
        ge=1,
        le=500,
    ),
):

    try:

        df = load_profile_data()

    except (
        FileNotFoundError,
        ValueError,
    ) as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


    df = (
        df
        .copy()
        .sort_values(
            "customer_id"
        )
        .reset_index(
            drop=True
        )
    )


    total = len(
        df
    )


    total_pages = (
        math.ceil(
            total /
            page_size
        )
        if total > 0
        else 1
    )


    if page > total_pages:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Page {page} does not exist. "
                f"Total pages: {total_pages}."
            ),
        )


    start = (
        page - 1
    ) * page_size


    end = (
        start +
        page_size
    )


    page_df = df.iloc[
        start:end
    ]


    customers = []


    for _, row in page_df.iterrows():

        customers.append(
            CustomerResponse(

                customer_id=str(
                    row[
                        "customer_id"
                    ]
                ),

                first_name=safe_string(
                    row,
                    "first_name",
                ),

                last_name=safe_string(
                    row,
                    "last_name",
                ),

                country=safe_string(
                    row,
                    "country",
                ),

                customer_segment=safe_string(
                    row,
                    "customer_segment",
                ),
            )
        )


    return CustomerListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        customers=customers,
    )


# ============================================================
# JOURNEY
# ============================================================

@app.get(
    "/journey/{booking_id}",
    response_model=JourneyResponse,
)
def get_journey(
    booking_id: str,
):

    try:

        df = load_journey_data()

    except (
        FileNotFoundError,
        ValueError,
    ) as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


    journey = df[
        df["booking_id"].astype(str)
        ==
        str(booking_id)
    ]


    if journey.empty:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Journey '{booking_id}' "
                f"was not found."
            ),
        )


    if len(journey) > 1:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Multiple journey records found "
                f"for booking '{booking_id}'."
            ),
        )


    row = journey.iloc[0]


    return JourneyResponse(

        customer_id=safe_string(
            row,
            "customer_id",
            "",
        ),

        booking_id=safe_string(
            row,
            "booking_id",
            booking_id,
        ),

        trip_id=safe_string(
            row,
            "trip_id",
        ),

        booking_status=safe_string(
            row,
            "booking_status",
        ),

        booking_amount=safe_float(
            row,
            "booking_amount",
        ),

        payment_attempts=safe_int(
            row,
            "payment_attempts",
        ),

        failed_payments=safe_int(
            row,
            "failed_payments",
        ),

        successful_payments=safe_int(
            row,
            "successful_payments",
        ),

        retry_count=safe_int(
            row,
            "retry_count",
        ),

        payment_success_rate=safe_float(
            row,
            "payment_success_rate",
        ),

        total_events=safe_int(
            row,
            "total_events",
        ),

        search_events=safe_int(
            row,
            "search_events",
        ),

        view_trip_events=safe_int(
            row,
            "view_trip_events",
        ),

        booking_started_events=safe_int(
            row,
            "booking_started_events",
        ),

        booking_created_events=safe_int(
            row,
            "booking_created_events",
        ),

        payment_started_events=safe_int(
            row,
            "payment_started_events",
        ),

        payment_failed_events=safe_int(
            row,
            "payment_failed_events",
        ),

        payment_retry_events=safe_int(
            row,
            "payment_retry_events",
        ),

        payment_completed_events=safe_int(
            row,
            "payment_completed_events",
        ),

        booking_confirmed_events=safe_int(
            row,
            "booking_confirmed_events",
        ),

        journey_duration_minutes=safe_float(
            row,
            "journey_duration_minutes",
        ),

        payment_duration_minutes=safe_float(
            row,
            "payment_duration_minutes",
        ),

        friction_score=safe_float(
            row,
            "friction_score",
        ),

        risk_level=safe_string(
            row,
            "risk_level",
        ),

        anomaly_summary=safe_string(
            row,
            "anomaly_summary",
        ),
    )


# ============================================================
# KPIs
# ============================================================

@app.get(
    "/kpis",
    response_model=KPIListResponse,
)
def get_kpis():

    try:

        df = load_kpi_data()

    except (
        FileNotFoundError,
        ValueError,
    ) as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


    kpis = []


    for _, row in df.iterrows():

        raw_value = row[
            "value"
        ]


        value = (
            None
            if pd.isna(
                raw_value
            )
            else float(
                raw_value
            )
        )


        kpi_name = str(
            row[
                "kpi_name"
            ]
        )


        kpis.append(
            KPIResponse(

                kpi_name=kpi_name,

                value=value,

                unit=str(
                    row[
                        "unit"
                    ]
                ),

                status=str(
                    row[
                        "status"
                    ]
                ),

                definition=KPI_DEFINITIONS.get(
                    kpi_name,
                    f"KPI: {kpi_name}",
                ),
            )
        )


    available_count = sum(
        kpi.status == "AVAILABLE"
        for kpi in kpis
    )


    proxy_count = sum(
        kpi.status == "PROXY"
        for kpi in kpis
    )


    unsupported_count = sum(
        kpi.status == "NOT_SUPPORTED"
        for kpi in kpis
    )


    return KPIListResponse(
        total_kpis=len(kpis),
        available_kpis=available_count,
        proxy_kpis=proxy_count,
        unsupported_kpis=unsupported_count,
        kpis=kpis,
    )


# ============================================================
# QUALITY
# ============================================================

@app.get(
    "/quality",
    response_model=QualityResponse,
)
def get_quality():

    try:

        df = load_quality_data()

    except (
        FileNotFoundError,
        ValueError,
    ) as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


    datasets = []


    for _, row in df.iterrows():

        datasets.append(
            QualityDatasetResponse(

                dataset=safe_string(
                    row,
                    "dataset",
                    "",
                ),

                rows=safe_int(
                    row,
                    "rows",
                ),

                expected_rows=safe_int(
                    row,
                    "expected_rows",
                ),

                row_count_status=safe_string(
                    row,
                    "row_count_status",
                    "",
                ),

                columns=safe_int(
                    row,
                    "columns",
                ),

                missing_cells=safe_int(
                    row,
                    "missing_cells",
                ),

                missing_percentage=safe_float(
                    row,
                    "missing_percentage",
                    0.0,
                ),

                columns_with_missing=safe_int(
                    row,
                    "columns_with_missing",
                ),

                duplicate_rows=safe_int(
                    row,
                    "duplicate_rows",
                ),

                duplicate_percentage=safe_float(
                    row,
                    "duplicate_percentage",
                    0.0,
                ),

                unique_values=safe_int(
                    row,
                    "unique_values",
                ),

                cardinality_percentage=safe_float(
                    row,
                    "cardinality_percentage",
                    0.0,
                ),

                numeric_columns=safe_int(
                    row,
                    "numeric_columns",
                ),

                object_columns=safe_int(
                    row,
                    "object_columns",
                ),

                string_columns=safe_int(
                    row,
                    "string_columns",
                ),

                datetime_like_columns=safe_int(
                    row,
                    "datetime_like_columns",
                ),

                invalid_values=safe_int(
                    row,
                    "invalid_values",
                ),

                invalid_percentage=safe_float(
                    row,
                    "invalid_percentage",
                    0.0,
                ),

                quality_score=safe_float(
                    row,
                    "quality_score",
                    0.0,
                ),

                quality_status=safe_string(
                    row,
                    "quality_status",
                    "UNKNOWN",
                ),
            )
        )


    overall_quality_score = round(
        sum(
            dataset.quality_score
            for dataset in datasets
        )
        /
        len(datasets)
        if datasets
        else 0.0,
        2,
    )


    excellent_datasets = sum(
        dataset.quality_status == "EXCELLENT"
        for dataset in datasets
    )


    warning_datasets = sum(
        dataset.quality_status in {
            "WARNING",
            "WARN",
        }
        for dataset in datasets
    )


    failed_datasets = sum(
        dataset.quality_status in {
            "FAILED",
            "FAIL",
        }
        for dataset in datasets
    )


    return QualityResponse(

        total_datasets=len(
            datasets
        ),

        overall_quality_score=overall_quality_score,

        excellent_datasets=excellent_datasets,

        warning_datasets=warning_datasets,

        failed_datasets=failed_datasets,

        total_rows=sum(
            dataset.rows
            for dataset in datasets
        ),

        total_missing_cells=sum(
            dataset.missing_cells
            for dataset in datasets
        ),

        total_duplicate_rows=sum(
            dataset.duplicate_rows
            for dataset in datasets
        ),

        total_invalid_values=sum(
            dataset.invalid_values
            for dataset in datasets
        ),

        datasets=datasets,
    )


# ============================================================
# UPLOAD
# ============================================================

@app.post(
    "/upload",
    response_model=UploadResponse,
)
async def upload_csv(
    file: UploadFile = File(...),
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No filename was provided.",
        )


    original_filename = os.path.basename(
        file.filename
    )


    if not original_filename.lower().endswith(
        ".csv"
    ):

        raise HTTPException(
            status_code=415,
            detail="Only CSV files are supported.",
        )


    try:

        contents = await file.read()

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Could not read uploaded file: "
                f"{exc}"
            ),
        )


    if len(contents) == 0:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )


    if len(contents) > MAX_UPLOAD_SIZE_BYTES:

        raise HTTPException(
            status_code=413,
            detail=(
                "Uploaded file exceeds the "
                "10 MB limit."
            ),
        )


    try:

        df = pd.read_csv(
            BytesIO(contents)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=(
                "Uploaded file is not a valid CSV: "
                f"{exc}"
            ),
        )


    if df.empty:

        raise HTTPException(
            status_code=400,
            detail=(
                "CSV contains headers but no data rows."
            ),
        )


    unique_id = uuid.uuid4().hex[:12]


    stored_filename = (
        f"{unique_id}_{original_filename}"
    )


    destination = os.path.join(
        UPLOAD_DIR,
        stored_filename,
    )


    try:

        with open(
            destination,
            "wb",
        ) as output_file:

            output_file.write(
                contents
            )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not save uploaded file: "
                f"{exc}"
            ),
        )


    return UploadResponse(

        filename=original_filename,

        stored_filename=stored_filename,

        rows=len(df),

        columns=len(df.columns),

        status="UPLOADED",
    )


# ============================================================
# INVESTIGATE
# ============================================================

@app.post(
    "/investigate",
    response_model=InvestigationResponse,
)
def investigate(
    request: InvestigationRequest,
):

    metric_name = request.metric.strip().lower()


    if metric_name not in INVESTIGATION_METRICS:

        supported_metrics = sorted(
            INVESTIGATION_METRICS.keys()
        )


        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported investigation metric "
                f"'{request.metric}'. "
                f"Supported metrics: "
                f"{', '.join(supported_metrics)}"
            ),
        )


    try:

        df = load_journey_data()

    except (
        FileNotFoundError,
        ValueError,
    ) as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


    source_column = INVESTIGATION_METRICS[
        metric_name
    ]


    if source_column not in df.columns:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Investigation source column "
                f"'{source_column}' is missing."
            ),
        )


    values = pd.to_numeric(
        df[source_column],
        errors="coerce",
    )


    valid_values = values.dropna()


    if valid_values.empty:

        raise HTTPException(
            status_code=500,
            detail=(
                f"No valid numeric values found "
                f"for metric '{metric_name}'."
            ),
        )


    count = int(
        valid_values.count()
    )


    mean_value = float(
        valid_values.mean()
    )


    median_value = float(
        valid_values.median()
    )


    minimum_value = float(
        valid_values.min()
    )


    maximum_value = float(
        valid_values.max()
    )


    standard_deviation = (
        float(
            valid_values.std(
                ddof=1
            )
        )
        if count > 1
        else 0.0
    )


    result = {

        "metric": metric_name,

        "source_column": source_column,

        "record_count": count,

        "mean": round(
            mean_value,
            4,
        ),

        "median": round(
            median_value,
            4,
        ),

        "standard_deviation": round(
            standard_deviation,
            4,
        ),

        "minimum": round(
            minimum_value,
            4,
        ),

        "maximum": round(
            maximum_value,
            4,
        ),
    }


    if request.threshold is not None:

        threshold = float(
            request.threshold
        )


        flagged_mask = (
            values >= threshold
        )


        flagged_count = int(
            flagged_mask.sum()
        )


        flagged_percentage = (
            flagged_count
            /
            count
            *
            100
        )


        result[
            "threshold"
        ] = round(
            threshold,
            4,
        )


        result[
            "threshold_operator"
        ] = ">="


        result[
            "flagged_count"
        ] = flagged_count


        result[
            "flagged_percentage"
        ] = round(
            flagged_percentage,
            2,
        )


        flagged = df.loc[
            flagged_mask,
            [
                "booking_id",
                "customer_id",
                source_column,
            ],
        ].copy()


        flagged = (
            flagged
            .sort_values(
                source_column,
                ascending=False,
            )
            .head(10)
        )


        top_records = []


        for _, row in flagged.iterrows():

            top_records.append(
                {
                    "booking_id": str(
                        row[
                            "booking_id"
                        ]
                    ),

                    "customer_id": str(
                        row[
                            "customer_id"
                        ]
                    ),

                    "value": float(
                        row[
                            source_column
                        ]
                    ),
                }
            )


        result[
            "top_flagged_journeys"
        ] = top_records


        if flagged_count > 0:

            status = (
                "THRESHOLD_MATCHES_FOUND"
            )


            message = (
                f"Investigation completed for "
                f"'{metric_name}'. "
                f"{flagged_count:,} of "
                f"{count:,} journeys "
                f"({flagged_percentage:.2f}%) "
                f"meet or exceed the threshold "
                f"of {threshold:.4f}."
            )

        else:

            status = (
                "NO_THRESHOLD_MATCHES"
            )


            message = (
                f"Investigation completed for "
                f"'{metric_name}'. "
                f"No journeys meet or exceed "
                f"the threshold of "
                f"{threshold:.4f}."
            )

    else:

        status = "ANALYZED"


        message = (
            f"Investigation completed for "
            f"'{metric_name}'. "
            f"No threshold was supplied; "
            f"descriptive statistics were returned."
        )


    return InvestigationResponse(

        metric=metric_name,

        status=status,

        message=message,

        result=result,
    )