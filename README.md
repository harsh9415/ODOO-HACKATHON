# HRMS — Human Resource Management System

A full-stack HRMS built for hackathon demo with React (Vite), FastAPI, and PostgreSQL.

## Features

- JWT authentication (access + refresh tokens)
- Admin-provisioned employee accounts with auto-generated Login IDs and temp passwords
- Employee grid with real-time status (present / on leave / absent)
- Check-in / Check-out from navigation bar
- Employee profiles: Resume, Private Info, Salary Info, Security tabs
- Auto-calculated salary components with server-side validation
- Attendance tracking (employee month view + admin day view)
- Leave management with approval workflow

## Prerequisites

- Python 3.9+ (3.11+ recommended)
- Node.js 18+
- PostgreSQL 14+ **or** Docker

## Quick Start (Docker + setup script)

```bash
cd hrms
chmod +x setup.sh
./setup.sh
```

Then in two terminals:

```bash
# Terminal 1 — Backend
cd hrms/backend && source venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2 — Frontend
cd hrms/frontend && npm run dev
```

## Manual Setup

### 1. Database

**Option A — Docker:**

```bash
cd hrms
docker compose up -d
```

**Option B — local PostgreSQL:**

```bash
createdb hrms
```

Update `backend/.env` if your credentials differ from `postgres:postgres@localhost:5432/hrms`.

### 2. Backend

```bash
cd hrms/backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Edit DATABASE_URL if needed
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

Backend runs at **http://localhost:8000**

### 3. Frontend

```bash
cd hrms/frontend
npm install
cp .env.example .env
npm run dev
```

Frontend runs at **http://localhost:5173**

## Demo Credentials

| Role     | Login ID          | Password      |
|----------|-------------------|---------------|
| Admin    | `OIADMIN20220001` | `Admin@123`   |
| Employee | `OIJODO20220001`  | `Employee@123`|

> Employee login ID follows: `[CompanyInitials][NameInitials][Year][Serial]`  
> Example: Odoo India + John Dodo + 2022 + 0001 = `OIJODO20220001`

## Running Tests

```bash
cd hrms/backend
pytest tests/ -v
```

## API Docs

Once the backend is running, visit **http://localhost:8000/docs** for Swagger UI.

## Project Structure

```
hrms/
├── backend/          # FastAPI + SQLAlchemy + Alembic
│   ├── app/
│   │   ├── routers/  # auth, employees, attendance, leave
│   │   ├── services/ # login_id, password, payroll calculators
│   │   └── models/
│   ├── alembic/
│   └── seed.py
└── frontend/         # React + Vite + TailwindCSS
    └── src/
        ├── pages/
        └── components/
```

## Key Business Rules

- **No public sign-up** — only Admin can create employees via Employees → NEW
- **Login ID format**: `[CompanyInitials][First2+Last2 letters][Year][4-digit serial]`
- **HRA** is calculated as % of Basic Salary (not total wage)
- **Fixed Allowance** = Monthly Wage − sum of all other components
- **Standard daily hours** for extra hours calculation: 9 hrs (configurable via `STANDARD_DAILY_HOURS`)
