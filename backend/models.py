from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# CUSTOMER RESPONSE
# ============================================================

class CustomerResponse(BaseModel):
    customer_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    country: Optional[str] = None
    customer_segment: Optional[str] = None


# ============================================================
# CUSTOMER PROFILE RESPONSE
# ============================================================

class ProfileResponse(BaseModel):
    customer_id: str

    total_bookings: float
    total_revenue: float
    average_booking_value: float
    recency_days: float
    booking_frequency: float
    repeat_booking_flag: int

    customer_segment: str
    segment_reason: str

    cohort_month: Optional[str] = None
    cluster_id: Optional[int] = None

    complaint_segment_status: str

    segmentation_status: str
    segmentation_method: str


# ============================================================
# CUSTOMER LIST RESPONSE
# ============================================================

class CustomerListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    customers: list[CustomerResponse]


# ============================================================
# JOURNEY RESPONSE
# ============================================================

class JourneyResponse(BaseModel):
    customer_id: str
    booking_id: str
    trip_id: Optional[str] = None

    booking_status: Optional[str] = None
    booking_amount: Optional[float] = None

    payment_attempts: int = 0
    failed_payments: int = 0
    successful_payments: int = 0
    retry_count: int = 0
    payment_success_rate: Optional[float] = None

    total_events: int = 0
    search_events: int = 0
    view_trip_events: int = 0
    booking_started_events: int = 0
    booking_created_events: int = 0
    payment_started_events: int = 0
    payment_failed_events: int = 0
    payment_retry_events: int = 0
    payment_completed_events: int = 0
    booking_confirmed_events: int = 0

    journey_duration_minutes: Optional[float] = None
    payment_duration_minutes: Optional[float] = None

    friction_score: Optional[float] = None
    risk_level: Optional[str] = None
    anomaly_summary: Optional[str] = None


# ============================================================
# KPI RESPONSE
# ============================================================

class KPIResponse(BaseModel):
    kpi_name: str
    value: Optional[float] = None
    unit: str
    status: str
    definition: str


# ============================================================
# KPI LIST RESPONSE
# ============================================================

class KPIListResponse(BaseModel):
    total_kpis: int
    available_kpis: int
    proxy_kpis: int
    unsupported_kpis: int
    kpis: list[KPIResponse]


# ============================================================
# UPLOAD RESPONSE
# ============================================================

class UploadResponse(BaseModel):
    filename: str
    stored_filename: str
    rows: int
    columns: int
    status: str


# ============================================================
# INVESTIGATION REQUEST
# ============================================================

class InvestigationRequest(BaseModel):
    metric: str = Field(
        ...,
        min_length=1,
        description="Numeric journey metric to investigate.",
    )

    threshold: Optional[float] = Field(
        default=None,
        description=(
            "Optional threshold. Journeys greater than "
            "or equal to this value are flagged."
        ),
    )


# ============================================================
# INVESTIGATION RESPONSE
# ============================================================

class InvestigationResponse(BaseModel):
    metric: str
    status: str
    message: str
    result: Optional[dict] = None


# ============================================================
# DATA QUALITY DATASET
# ============================================================

class QualityDatasetResponse(BaseModel):
    dataset: str
    rows: int
    expected_rows: int
    row_count_status: str
    columns: int

    missing_cells: int
    missing_percentage: float
    columns_with_missing: int

    duplicate_rows: int
    duplicate_percentage: float

    unique_values: int
    cardinality_percentage: float

    numeric_columns: int
    object_columns: int
    string_columns: int
    datetime_like_columns: int

    invalid_values: int
    invalid_percentage: float

    quality_score: float
    quality_status: str


# ============================================================
# DATA QUALITY RESPONSE
# ============================================================

class QualityResponse(BaseModel):
    total_datasets: int
    overall_quality_score: float

    excellent_datasets: int
    warning_datasets: int
    failed_datasets: int

    total_rows: int
    total_missing_cells: int
    total_duplicate_rows: int
    total_invalid_values: int

    datasets: list[QualityDatasetResponse]


# ============================================================
# STANDARD ERROR RESPONSE
# ============================================================

class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int
    path: str