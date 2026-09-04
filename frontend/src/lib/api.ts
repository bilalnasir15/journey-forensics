// ============================================================
// JOURNEY FORENSICS API CLIENT
// ============================================================

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");

// ============================================================
// KPI
// ============================================================

export interface KPI {
  kpi_name: string;
  value: number | null;
  unit: string;
  status: string;
  definition: string;
}

export interface KPIResponse {
  total_kpis: number;
  available_kpis: number;
  proxy_kpis: number;
  unsupported_kpis: number;
  kpis: KPI[];
}

// ============================================================
// CUSTOMER
// ============================================================

export interface Customer {
  customer_id: string;
  first_name?: string | null;
  last_name?: string | null;
  country?: string | null;
  customer_segment?: string | null;
}

export interface CustomerListResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  customers: Customer[];
}

// ============================================================
// PROFILE
// ============================================================

export interface Profile {
  customer_id: string;

  total_bookings: number;
  total_revenue: number;
  average_booking_value: number;
  recency_days: number;
  booking_frequency: number;
  repeat_booking_flag: number;

  customer_segment: string;
  segment_reason: string;

  cohort_month?: string | null;
  cluster_id?: number | null;

  complaint_segment_status: string;

  segmentation_status: string;
  segmentation_method: string;
}

// ============================================================
// JOURNEY
// ============================================================

export interface Journey {
  customer_id: string;
  booking_id: string;

  trip_id?: string | null;

  booking_status?: string | null;
  booking_amount?: number | null;

  payment_attempts: number;
  failed_payments: number;
  successful_payments: number;
  retry_count: number;

  payment_success_rate?: number | null;

  total_events: number;

  search_events: number;
  view_trip_events: number;
  booking_started_events: number;
  booking_created_events: number;

  payment_started_events: number;
  payment_failed_events: number;
  payment_retry_events: number;
  payment_completed_events: number;
  booking_confirmed_events: number;

  journey_duration_minutes?: number | null;
  payment_duration_minutes?: number | null;

  friction_score?: number | null;

  risk_level?: string | null;

  anomaly_summary?: string | null;
}

// ============================================================
// UPLOAD
// ============================================================

export interface UploadResponse {
  filename: string;
  stored_filename: string;
  rows: number;
  columns: number;
  status: string;
}

// ============================================================
// DATA QUALITY
// ============================================================

export interface QualityDataset {
  dataset: string;

  rows: number;
  expected_rows: number;
  row_count_status: string;

  columns: number;

  missing_cells: number;
  missing_percentage: number;
  columns_with_missing: number;

  duplicate_rows: number;
  duplicate_percentage: number;

  unique_values: number;
  cardinality_percentage: number;

  numeric_columns: number;
  object_columns: number;
  string_columns: number;
  datetime_like_columns: number;

  invalid_values: number;
  invalid_percentage: number;

  quality_score: number;
  quality_status: string;
}

export interface QualityResponse {
  total_datasets: number;

  overall_quality_score: number;

  excellent_datasets: number;
  warning_datasets: number;
  failed_datasets: number;

  total_rows: number;
  total_missing_cells: number;
  total_duplicate_rows: number;
  total_invalid_values: number;

  datasets: QualityDataset[];
}

// ============================================================
// API ERROR
// ============================================================

export interface APIError {
  error: string;
  message: string;
  status_code: number;
  path: string;
}

// ============================================================
// BASE REQUEST
// ============================================================

async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}${endpoint}`,
      {
        ...options,

        headers: {
          Accept: "application/json",
          ...(options?.headers || {}),
        },

        cache: "no-store",
      }
    );
  } catch {
    throw new Error(
      "Unable to connect to the Journey Forensics API."
    );
  }

  if (!response.ok) {
    let errorBody: APIError | null = null;

    try {
      errorBody = await response.json();
    } catch {
      // Ignore malformed error response.
    }

    throw new Error(
      errorBody?.message ||
        `API request failed with status ${response.status}.`
    );
  }

  return response.json() as Promise<T>;
}

// ============================================================
// HEALTH
// ============================================================

export async function getHealth(): Promise<{
  status: string;
}> {
  return apiRequest("/health");
}

// ============================================================
// KPIS
// ============================================================

export async function getKPIs(): Promise<KPIResponse> {
  return apiRequest("/kpis");
}

// ============================================================
// CUSTOMERS
// ============================================================

export async function getCustomers(
  page = 1,
  pageSize = 10
): Promise<CustomerListResponse> {
  return apiRequest(
    `/customers?page=${page}&page_size=${pageSize}`
  );
}

export async function getAllCustomers(): Promise<Customer[]> {
  const firstPage = await getCustomers(1, 500);

  if (firstPage.total_pages <= 1) {
    return firstPage.customers;
  }

  const remainingRequests = Array.from(
    {
      length: firstPage.total_pages - 1,
    },
    (_, index) =>
      getCustomers(index + 2, 500)
  );

  const remainingPages =
    await Promise.all(remainingRequests);

  return [
    ...firstPage.customers,
    ...remainingPages.flatMap(
      (page) => page.customers
    ),
  ];
}

// ============================================================
// PROFILE
// ============================================================

export async function getProfile(
  customerId: string
): Promise<Profile> {
  return apiRequest(
    `/profile?customer_id=${encodeURIComponent(
      customerId
    )}`
  );
}

// ============================================================
// JOURNEY
// ============================================================

export async function getJourney(
  bookingId: string
): Promise<Journey> {
  return apiRequest(
    `/journey/${encodeURIComponent(
      bookingId
    )}`
  );
}

// ============================================================
// UPLOAD
// ============================================================

export async function uploadCSV(
  file: File
): Promise<UploadResponse> {
  const formData = new FormData();

  formData.append("file", file);

  return apiRequest("/upload", {
    method: "POST",
    body: formData,
  });
}

// ============================================================
// DATA QUALITY
// ============================================================

export async function getQuality(): Promise<QualityResponse> {
  return apiRequest("/quality");
}