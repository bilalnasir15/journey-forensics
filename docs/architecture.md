# Journey Forensics Architecture

## High-Level Architecture

User
↓
Next.js Frontend
↓
FastAPI Backend
↓
Analytics Engine
↓
PostgreSQL / Analytical Data
↓
AI Investigation Layer
↓
Evidence-backed Findings
↓
Frontend / Power BI


## Main Components

### Frontend

Responsible for:

- User interface
- Dataset upload
- KPI visualization
- Customer journey visualization
- Investigation interface

### Backend

Responsible for:

- API endpoints
- Business logic
- Authentication
- Communication between frontend and analytical services

### Analytics

Responsible for:

- Data profiling
- EDA
- SQL analytics
- Statistical analysis
- Customer journey reconstruction
- Customer segmentation

### Database

Responsible for:

- Application data
- Analytical data
- Customer and journey information

### AI

Responsible for:

- Investigation planning
- Selecting analytical tools
- Interpreting analytical results
- Generating evidence-backed explanations

### Power BI

Responsible for:

- Executive dashboards
- Business KPIs
- High-level reporting

### Tests

Responsible for:

- Unit tests
- Integration tests
- API tests
- Analytics tests
- AI evaluation

### Infrastructure

Responsible for:

- Docker
- Deployment
- Environment configuration
- CI/CD