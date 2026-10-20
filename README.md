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
- **Real-time:** FastAPI WebSockets and in-memory project channels

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

## 🔐 Authentication (Phase 3)

The API stores Argon2id password hashes and issues signed HS256 bearer access tokens. Set `JWT_SECRET_KEY` in `backend/.env`; use a unique random value of at least 32 characters for production. `JWT_ALGORITHM` is restricted to `HS256`, and `ACCESS_TOKEN_EXPIRE_MINUTES` controls token lifetime. Production startup fails if the JWT key is not explicitly configured securely. Do not commit actual environment files or production secrets.

Authentication endpoints under `/api/v1/auth`:

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create an account |
| `POST` | `/api/v1/auth/login` | Verify credentials and return a bearer access token |
| `GET` | `/api/v1/auth/me` | Return the authenticated user's safe profile |
| `POST` | `/api/v1/auth/logout` | Confirm client sign-out; requires a valid bearer token |

The frontend keeps the access token in `localStorage` and sends it through the Axios `Authorization` header. This is simple for the current SPA but exposes bearer tokens to JavaScript executing through an XSS flaw; use a hardened Content Security Policy and consider migrating to `HttpOnly`, `Secure`, `SameSite` cookies for a stronger session boundary. Passwords are never stored in browser storage. Logout removes the token from this browser only; stateless JWTs remain usable until expiration and are not revoked server-side.

### Auth environment and dependencies

Copy `backend/.env.example` to `backend/.env`, then set a private `JWT_SECRET_KEY`. Install backend dependencies with `pip install -r backend/requirements.txt`; the frontend needs no added dependencies. Run the API and Vite frontend using the setup steps below. Authentication tests run with `pytest` from `backend`; their SQLite test database does not require a live PostgreSQL server. The separately existing live migration integration test skips unless a disposable PostgreSQL test database is available.

## 🗂 Project Management (Phase 4)

Authenticated users can create projects and access only projects where they are members. The creator receives the `owner` role. Owners control settings and membership and are the only role that can delete a project; admins can update project settings and manage member-level membership; all members can create and update tasks and comments; only owners/admins can delete tasks. Project owners cannot be removed. Membership invitations use an existing active account's email; no public user directory is exposed.

Tasks and comments are scoped to project membership. Assignees must be members. Valid task statuses are `todo`, `in_progress`, and `done`; priorities are `low`, `medium`, `high`, and `urgent`. Server-side search and filters include text, status, priority, assignee, due-date range, sorting, and pagination. Activity entries are written in the same transaction as their successful operation. The authenticated dashboard reports only projects and tasks the current user can access.

Main Phase 4 routes require a bearer token:

| Method | Path | Description |
|---|---|---|
| `GET` / `POST` | `/api/v1/projects` | List accessible projects / create a project |
| `GET` / `PATCH` / `DELETE` | `/api/v1/projects/{project_id}` | Read, update (owner/admin), or delete (owner) |
| `GET` / `POST` | `/api/v1/projects/{project_id}/members` | List members / add registered user by email |
| `DELETE` | `/api/v1/projects/{project_id}/members/{user_id}` | Remove a non-owner member |
| `GET` / `POST` | `/api/v1/projects/{project_id}/tasks` | Filter/list tasks / create task |
| `GET` / `PATCH` / `DELETE` | `/api/v1/projects/{project_id}/tasks/{task_id}` | Read, update, or delete task |
| `GET` / `POST` | `/api/v1/projects/{project_id}/tasks/{task_id}/comments` | List or add task comments |
| `PATCH` / `DELETE` | `/api/v1/projects/{project_id}/tasks/{task_id}/comments/{comment_id}` | Edit or remove authorized comment |
| `GET` | `/api/v1/projects/{project_id}/activity` | View project activity |
| `GET` | `/api/v1/projects/dashboard` | Access-scoped dashboard summaries |
| `GET` | `/api/v1/projects/tasks/search` | Search across accessible projects |

Task list/search query parameters include `q`, `project_id` (search), `status`, `priority`, `assignee_id`, `due_from`, `due_to`, `sort`, `order`, `limit`, and `offset` as applicable. The existing initial migration already defines the required schema, so Phase 4 adds no migration. For a fresh local database, run `alembic upgrade head` from `backend`; do not downgrade a database containing data you need. Run tests with `pytest` from `backend` and build the frontend with `npm run build` from `frontend`. Feature API tests use isolated SQLite; the live migration test requires disposable PostgreSQL.

## 🔔 Notifications and live updates (Phase 5)

Persistent notifications use the existing `notifications` table. Current triggers cover project membership additions, task assignment, task status changes, and comments on another user's assigned task; the actor is not notified about their own change. Notification REST endpoints are `GET /api/v1/notifications?limit=30&offset=0&unread_only=false`, `GET /api/v1/notifications/unread-count`, `PATCH /api/v1/notifications/{notification_id}/read`, and `PATCH /api/v1/notifications/read-all`. Results and updates are scoped to the authenticated user.

Project updates use `ws(s)://<backend-origin>/api/v1/ws/projects/{project_id}`. Because browsers don't allow custom Authorization headers for native WebSockets, the client sends its bearer token in the first WebSocket data frame (not in the URL); the server validates it and checks active project membership before registering the socket. Events include project/task/comment/activity and notification updates. Failed WebSockets do not disable REST operations; the UI reconnects with bounded backoff and refreshes REST data when events arrive. The in-memory manager is single-process only: configure one Uvicorn worker/instance, or add a shared pub/sub broker before scaling horizontally. Do not enable WebSocket compression or log access tokens. Production must use HTTPS/WSS and a proxy/host that supports WebSocket upgrades and suitable idle timeouts.

### Deployment preparation (not deployed)

- Host the Vite static output (`frontend/dist`) on a static host/CDN with SPA history fallback; configure `VITE_API_BASE_URL` to the HTTPS backend origin and `VITE_WS_BASE_URL` to that same origin (or leave both blank when frontend/backend share an origin and the reverse proxy routes `/api`). WebSocket URL selection automatically uses `wss:` for HTTPS pages.
- Run FastAPI on a host that supports long-lived WebSocket upgrades and configure the proxy/load balancer for HTTP/1.1 Upgrade/Connection headers, suitable idle timeouts, and sticky routing if there are multiple workers (though shared event delivery remains unavailable across workers).
- Use managed PostgreSQL with network allow-lists/private networking and TLS. Configure `DATABASE_URL`, `JWT_SECRET_KEY`, and exact comma-separated/JSON `BACKEND_CORS_ORIGINS` as host secrets/environment variables. Never use `.env.example` values as production credentials.
- Run `alembic upgrade head` as a one-off release step against a backup/verified database; the current Phase 5 features do not change the schema. Do not use downgrade as a deployment rollback strategy when it could drop user data.
- Deployment is only prepared in this repository; hosting account access, DNS, provider settings, secrets, and production verification remain manual.

## 📡 API Endpoints

| Method | Path | Description | Query Parameters |
|---|---|---|---|
| `GET` | `/` | API status and documentation entry points | None |
| `GET` | `/health` | Top-level system & DB health alias | None |
| `GET` | `/api/v1/ping` | Rapid liveness probe (`{"ping": "pong"}`) | None |
| `GET` | `/api/v1/health` | Comprehensive system health & database probe | `strict` (boolean, default: false) |
| `GET` | `/api/v1/docs` | OpenAPI / Swagger interactive documentation | None |
| `GET` | `/api/v1/openapi.json` | Raw OpenAPI 3.1 specification | None |
| `POST` | `/api/v1/auth/register` | Register a user | None |
| `POST` | `/api/v1/auth/login` | Obtain an access token | None |
| `GET` | `/api/v1/auth/me` | Get authenticated user profile | Bearer token |
| `POST` | `/api/v1/auth/logout` | Client-side sign-out confirmation | Bearer token |
| `GET` / `POST` | `/api/v1/projects` | List accessible projects / create a project | Bearer token |
| `GET` / `PATCH` / `DELETE` | `/api/v1/projects/{project_id}` | Read/update/delete an authorized project | Bearer token |
| `GET` / `POST` | `/api/v1/projects/{project_id}/tasks` | List/filter or create project tasks | Bearer token |
| `GET` | `/api/v1/projects/dashboard` | Access-scoped dashboard counts and task lists | Bearer token |
| `GET` | `/api/v1/notifications` | Current user's notifications | Bearer token |
| `GET` | `/api/v1/notifications/unread-count` | Current user's unread count | Bearer token |
| `PATCH` | `/api/v1/notifications/{notification_id}/read` | Mark own notification read | Bearer token |
| `PATCH` | `/api/v1/notifications/read-all` | Mark own notifications read | Bearer token |
| `WebSocket` | `/api/v1/ws/projects/{project_id}` | Membership-authorized project events | Initial auth frame |

---

## 🗺 Development Roadmap

- [x] **Phase 1: Project structure, React + Vite, FastAPI, PostgreSQL configuration, health endpoints, initial tests.**
- [x] **Phase 2: Database models, SQLAlchemy configuration, Alembic migrations, and database integration tests.**
- [x] **Phase 3: Registration, login, logout, authentication, protected routes, and security tests.**
- [x] **Phase 4: Project CRUD, memberships, invitations, and role-based authorization.**
- [x] **Phase 5: Notifications, real-time project events, testing, and deployment preparation.**
- [ ] **Phase 6: External deployment, multi-instance event broker, and production monitoring.**
- [ ] **Phase 5: Task CRUD, assignments, priorities, statuses, deadlines, search, and filtering.**
- [ ] **Phase 6: Task comments, activity history, and collaboration.**
- [ ] **Phase 7: Notifications and real-time WebSocket updates.**
- [ ] **Phase 8: Dashboard, responsive UI, accessibility, and frontend integration.**
- [ ] **Phase 9: Comprehensive testing, security review, bug fixes, and performance checks.**
- [ ] **Phase 10: Production configuration, GitHub documentation, deployment, and final verification.**
