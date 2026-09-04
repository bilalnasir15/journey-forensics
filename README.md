# 🔎 Journey Forensics

Journey Forensics is an end-to-end customer journey analytics and investigation platform designed to identify friction, anomalies, payment issues, customer behavior patterns, and journey-level risks.

It combines:

- Data engineering
- Customer journey analytics
- Data quality monitoring
- KPI analytics
- Deterministic investigation
- AI-assisted investigation
- FastAPI backend
- Next.js frontend
- Dockerized deployment

---

# 🏗️ Architecture

```text
                         USER
                           │
                           ▼
                ┌─────────────────────┐
                │   Next.js Frontend  │
                │      Port 3000      │
                └──────────┬──────────┘
                           │ REST API
                           ▼
                ┌─────────────────────┐
                │   FastAPI Backend   │
                │      Port 8000      │
                └──────────┬──────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        Analytics        AI Layer     Data Files
              │            │            │
              ▼            ▼            ▼
          KPIs / QA     Gemini AI     Processed CSVs

🎯 Business Problem

Customer journeys often contain hidden friction such as:

Failed payments
Payment retries
Long payment duration
High journey duration
Booking failures
Customer drop-offs
Suspicious or anomalous journeys
Poor data quality

Journey Forensics converts these signals into an investigation-ready platform.

✨ Key Features
Customer Analytics
Customer-level profiles
Customer segmentation
Revenue metrics
Booking frequency
Repeat booking behavior
Customer journey exploration
Journey Investigation
Booking-level investigation
Journey duration analysis
Payment analysis
Retry analysis
Friction score analysis
Risk level
Anomaly summary
KPI Analytics

The platform exposes key business metrics including:

Total Customers
Total Bookings
Total Payment Attempts
Total Events
Booking Conversion Rate
Booking Confirmation Rate
Cancellation Rate
Payment Success Rate
Payment Failure Rate
Retry Rate
Repeat Customer Rate
Total Revenue
Revenue Per Customer
Average Booking Value
Anomaly Rate
Average Journey Duration
Average Payment Duration
Average Friction Score
Data Quality

The quality dashboard provides:

Row counts
Missing values
Duplicate records
Invalid values
Cardinality
Data quality score
Dataset quality status
AI Investigation

AI-assisted investigation supports:

Evidence-grounded analysis
Investigation summaries
AI fallback handling
Deterministic explanation fallback
Hallucination protection
Metric-aware investigation
🧰 Technology Stack
Frontend
Next.js
React
TypeScript
Tailwind CSS
Recharts
Motion
Lucide React
Backend
FastAPI
Python
Pandas
NumPy
SciPy
Pydantic
AI
Google Gemini
Gemini primary/fallback models
Evidence-grounded AI responses
Deployment
Docker
Docker Compose
Next.js standalone production build
Uvicorn
📁 Project Structure
journey-forensics/
│
├── ai/
├── analytics/
│   └── sql/
│
├── backend/
│   ├── ai/
│   ├── main.py
│   ├── models.py
│   └── requirements.txt
│
├── data/
│   ├── processed/
│   ├── raw/
│   ├── sample/
│   └── uploads/
│
├── database/
├── docs/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   ├── Dockerfile
│   ├── package.json
│   └── next.config.ts
│
├── infrastructure/
├── powerbi/
├── tests/
│
├── backend/Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
└── README.md
🚀 Local Development
1. Clone the repository
git clone <your-repository-url>
cd journey-forensics
2. Backend environment

Create:

.env

using:

.env.example

Set the required AI configuration:

LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.7-flash
GEMINI_FALLBACK_MODEL=gemini-2.5-flash-lite

Never commit .env or API keys.

🐍 Run Backend Locally

Create virtual environment:

python -m venv .venv

Activate:

.venv\Scripts\activate

Install dependencies:

pip install -r backend\requirements.txt

Run FastAPI:

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

Backend:

http://127.0.0.1:8000

Health:

http://127.0.0.1:8000/health

API documentation:

http://127.0.0.1:8000/docs
⚛️ Run Frontend Locally
cd frontend
npm install
npm run dev

Frontend:

http://127.0.0.1:3000
🐳 Docker Deployment

Build and run the complete application:

docker compose up --build

Services:

Frontend
http://127.0.0.1:3000

Backend
http://127.0.0.1:8000

Backend Health
http://127.0.0.1:8000/health

Stop containers:

docker compose down
🔌 API Endpoints
Method	Endpoint	Purpose
GET	/	API information
GET	/health	Health check
GET	/profile	Customer profile
GET	/customers	Customer listing
GET	/journey/{booking_id}	Journey details
GET	/kpis	KPI results
GET	/quality	Data quality results
POST	/upload	Upload CSV
POST	/investigate	Deterministic investigation
AI routes	/ai/...	AI investigation capabilities

Interactive API documentation:

http://127.0.0.1:8000/docs
🧪 Smoke Test

Verify frontend:

Invoke-WebRequest "http://127.0.0.1:3000" -UseBasicParsing

Verify backend:

Invoke-WebRequest "http://127.0.0.1:8000/health" -UseBasicParsing

Verify KPIs:

Invoke-WebRequest "http://127.0.0.1:8000/kpis" -UseBasicParsing

Verify customers:

Invoke-WebRequest "http://127.0.0.1:8000/customers?page=1&page_size=5" -UseBasicParsing

Expected response:

HTTP 200 OK
📊 Current Validation

The application has been validated across:

Frontend production build
Backend production build
Docker backend
Docker frontend
Docker Compose
Production logging
Environment configuration
API health checks
KPI endpoint
Customer endpoint
Frontend endpoint
🔐 Security

Secrets must never be committed.

.env

is intentionally excluded from version control.

Use:

.env.example

as the configuration template.


Example:

![Overview Dashboard](docs/screenshots/overview.png)
💼 Business Value

Journey Forensics helps teams answer:

What happened during the customer journey?

Where did friction occur?

Why did the journey fail?

Which customers were affected?

Was the problem related to payment, booking, or another journey stage?

What evidence supports the investigation?

This moves analytics from simple reporting toward actionable investigation.

🏆 Project Highlights
End-to-end customer journey analytics
Customer-level forensic investigation
KPI and business metric framework
Data quality monitoring
Journey anomaly detection
AI-assisted investigation
Evidence-grounded AI architecture
FastAPI REST API
Modern Next.js interface
Dockerized production deployment
Production request logging
API health monitoring
👨‍💻 Author

Muhammad Usama Zaid Nasir

Azure Data Engineer | Data Engineering | Analytics | AI

📄 License

This project is intended for portfolio and demonstration purposes.


### Save karne ke baad

Run:

```powershell
Get-Content README.md | Select-Object -First 30