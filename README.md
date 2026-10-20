# TaskFlow — Collaborative Project Management Application

TaskFlow is a modern, high-velocity project management platform inspired by Trello and Asana. It provides real-time collaborative Kanban boards, customizable task workflows, granular role-based permissions, notifications, and activity audit trails.

---

## 🛠 Technology Stack

### Frontend
- **Framework:** React 19 + Vite 8
- **Language:** Modern JavaScript (ES Modules)
- **Routing:** React Router v7
- **Styling:** Tailwind CSS v4 with `@tailwindcss/vite`
- **Data Fetching:** Axios with interceptors
- **Forms & Validation:** React Hook Form
- **Icons:** Lucide React

### Backend
- **Framework:** Python 3.14 + FastAPI
- **Server:** Uvicorn ASGI
- **ORM:** SQLAlchemy 2.0 (Declarative Base & connection pooling)
- **Validation:** Pydantic v2 & `pydantic-settings`
- **Database Driver:** `psycopg` (v3 with binary wheels)
- **Migrations:** Alembic (Phase 2)
- **Real-time:** WebSockets & Starlette (Phase 7)

### Database
- **Engine:** PostgreSQL 16
- **Local Dev:** Docker Compose (`postgres:16-alpine`)
- **Connection Management:** Pre-ping connection health probing, configurable pool sizes, connection timeouts

### Testing & Quality
- **Backend:** `pytest` + `httpx` / FastAPI `TestClient`
- **Frontend:** Vite production build verification & Oxlint

---

## 📁 Project Directory Structure

```
D:\taskflow\
├── .gitignore                   # Comprehensive ignores for Python, Node, OS, .env
├── docker-compose.yml           # PostgreSQL 16 alpine service configuration
├── README.md                    # Project documentation, architecture & runbook
├── .venv/                       # Python virtual environment
├── backend/
│   ├── .env.example             # Backend environment template
│   ├── .env                     # Local backend configuration
│   ├── pyproject.toml           # Pytest & package configuration
│   ├── requirements.txt         # Pinned backend dependencies
│   ├── app/
│   │   ├── __init__.py          # Package root
│   │   ├── main.py              # FastAPI app factory, CORS, lifespan & error handlers
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # Central API router
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           └── health.py # Health checks (/health, /api/v1/health, /api/v1/ping)
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py        # Pydantic Settings & environment parsing
│   │   │   └── database.py      # SQLAlchemy 2.x engine, SessionLocal & health probe
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── health.py        # Health response Pydantic models
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py          # Pytest fixtures & TestClient
│       └── test_health.py       # Automated health, schema & CORS tests
└── frontend/
    ├── .env.example             # Frontend environment template
    ├── .env                     # Local frontend configuration
    ├── index.html               # Vite HTML entry point
    ├── package.json             # Frontend dependencies & scripts
    ├── vite.config.js           # Vite configuration with Tailwind plugin & API proxy
    └── src/
        ├── App.jsx              # React router root application
        ├── index.css            # Tailwind CSS v4 entry
        ├── main.jsx             # React DOM entry
        ├── api/
        │   ├── client.js        # Axios instance with interceptors
        │   └── health.js        # Health check API functions
        ├── components/
        │   └── common/
        │       ├── Navbar.jsx   # Header with status indicator
        │       └── StatusBadge.jsx # Live probe indicator
        └── pages/
            └── HomePage.jsx     # Overview, live diagnostics & roadmap
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Node.js**: v18+ (verified on v24.14.0)
- **Python**: 3.11+ (verified on 3.14.2)
- **Docker / Docker Desktop** (or a local/remote PostgreSQL instance)

---

### 2. PostgreSQL Setup

#### Option A: Using Docker Compose (Recommended)
Start the PostgreSQL container with persistent storage:
```powershell
docker compose up -d
```
To stop the database:
```powershell
docker compose down
```

#### Option B: Standalone / Cloud PostgreSQL
If using an existing PostgreSQL server or cloud database (e.g., Supabase, Neon, AWS RDS), update `backend/.env`:
```ini
DATABASE_URL="postgresql+psycopg://<user>:<password>@<host>:<port>/<dbname>"
```

---

### 3. Backend Setup & Run

From `D:\taskflow`:

```powershell
# 1. Activate or create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Start the FastAPI development server
$env:PYTHONPATH="backend"
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

The API will be available at:
- **Interactive Swagger Documentation:** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **ReDoc Documentation:** [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)
- **Health Endpoint:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Ping Probe:** [http://localhost:8000/api/v1/ping](http://localhost:8000/api/v1/ping)

---

### 4. Running Backend Automated Tests

Run the test suite using `pytest`:
```powershell
Set-Location D:\taskflow\backend
..\.venv\Scripts\pytest.exe
```

All 8 tests verify:
- Root endpoint metadata
- Liveness ping probe
- Health endpoint schema integrity
- Top-level `/health` alias
- Healthy database detection
- Degraded database handling (non-strict mode returns 200 with diagnostics)
- Strict mode database failure (returns 503 Service Unavailable)
- CORS header negotiation

---

### 5. Frontend Setup & Run

In a separate terminal:
```powershell
Set-Location D:\taskflow\frontend

# Install dependencies (already installed during Phase 1)
npm install

# Start Vite development server
npm run dev
```

Open your browser at [http://localhost:5173](http://localhost:5173).

To verify the production build:
```powershell
npm run build
```

---

## 📡 API Endpoints (Phase 1)

| Method | Path | Description | Query Parameters |
|---|---|---|---|
| `GET` | `/` | API status and documentation entry points | None |
| `GET` | `/health` | Top-level system & DB health alias | None |
| `GET` | `/api/v1/ping` | Rapid liveness probe (`{"ping": "pong"}`) | None |
| `GET` | `/api/v1/health` | Comprehensive system health & database probe | `strict` (boolean, default: false) |
| `GET` | `/api/v1/docs` | OpenAPI / Swagger interactive documentation | None |
| `GET` | `/api/v1/openapi.json` | Raw OpenAPI 3.1 specification | None |

---

## 🗺 Development Roadmap

- [x] **Phase 1: Project structure, React + Vite, FastAPI, PostgreSQL configuration, health endpoints, initial tests.**
- [ ] **Phase 2: Database models, SQLAlchemy configuration, Alembic migrations, and database integration tests.**
- [ ] **Phase 3: Registration, login, logout, authentication, protected routes, and security tests.**
- [ ] **Phase 4: Project CRUD, memberships, invitations, and role-based authorization.**
- [ ] **Phase 5: Task CRUD, assignments, priorities, statuses, deadlines, search, and filtering.**
- [ ] **Phase 6: Task comments, activity history, and collaboration.**
- [ ] **Phase 7: Notifications and real-time WebSocket updates.**
- [ ] **Phase 8: Dashboard, responsive UI, accessibility, and frontend integration.**
- [ ] **Phase 9: Comprehensive testing, security review, bug fixes, and performance checks.**
- [ ] **Phase 10: Production configuration, GitHub documentation, deployment, and final verification.**
