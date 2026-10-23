<div align="center">

# 🤖 MASDS — Multi-Agent Software Development System

**Describe your app. Watch AI build it.**

A team of 6 specialized AI agents that autonomously plan, architect, code, test, review, and deploy software — end to end — from a single natural-language requirement.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.1-FF6B35?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

---

![MASDS Dashboard Preview](https://placehold.co/900x500/0a0a0f/4f8ef7?text=MASDS+Live+Dashboard&font=roboto)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [How It Works](#-how-it-works)
- [The Agent Team](#-the-agent-team)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Dashboard Features](#-dashboard-features)
- [API Reference](#-api-reference)
- [RAG Knowledge Base](#-rag-knowledge-base)
- [Code Execution Sandbox](#-code-execution-sandbox)
- [Development Guide](#-development-guide)
- [Running Tests](#-running-tests)
- [Deployment](#-deployment)
- [Cost Estimation](#-cost-estimation)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

**MASDS** (Multi-Agent Software Development System) is an agentic AI platform where specialized agents collaborate like a real engineering team to build software from scratch.

You type:
```
Build a REST API for a blog platform with JWT authentication,
CRUD for posts and comments, PostgreSQL, and rate limiting.
```

MASDS delivers:
- ✅ Complete, working source code (structured by module)
- ✅ Comprehensive pytest test suite (>80% coverage)
- ✅ Security-reviewed, OWASP-grounded code
- ✅ Dockerfile + docker-compose + GitHub Actions CI/CD
- ✅ Auto-deployed to a staging environment
- ✅ Real-time dashboard showing every agent's thinking

### Why MASDS?

| Traditional Dev | MASDS |
|---|---|
| Weeks of planning + coding | Minutes, end-to-end |
| Manual code review | Automated, RAG-grounded review |
| Siloed work | Agents debate and iterate |
| Static output | Self-healing (tests fail → coder retries) |
| No visibility | Live dashboard of every decision |

---

## 🔄 How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     MASDS PIPELINE                              │
│                                                                 │
│  You describe the app                                           │
│         │                                                       │
│         ▼                                                       │
│  🗂️  Planner   →  Breaks into modules, picks tech stack        │
│         │                                                       │
│         ▼                                                       │
│  🏛️  Architect  →  Designs API, DB schema, file structure      │
│         │                                                       │
│         ▼                                                       │
│  💻  Coder     →  Writes code module by module                 │
│         │                                                       │
│         ▼                                                       │
│  🧪  Tester    →  Writes & runs tests in Docker sandbox        │
│         │                                                       │
│    ┌────▼────┐                                                  │
│    │ Passed? │──── NO (attempt < 3) ──► back to Coder         │
│    └────┬────┘                                                  │
│         │ YES                                                   │
│         ▼                                                       │
│  🔍  Reviewer  →  RAG-grounded security + quality review       │
│         │                                                       │
│    ┌────▼──────────┐                                           │
│    │ Approved?     │──── NO (cycle < 2) ──► back to Coder     │
│    └────┬──────────┘                                           │
│         │ YES                                                   │
│         ▼                                                       │
│  🚀  DevOps    →  Dockerfile, CI/CD, deploy to staging         │
│         │                                                       │
│         ▼                                                       │
│  ✅  Your software is live!                                     │
└─────────────────────────────────────────────────────────────────┘
```

The entire pipeline is **stateful** (powered by LangGraph) and **event-driven** — every agent action is broadcast over WebSocket to the live dashboard in real time.

---

## 🤖 The Agent Team

| Agent | Role | LLM | Responsibility |
|---|---|---|---|
| 🗂️ **Planner** | Engineering Manager | Gemini 1.5 Flash | Decomposes requirements into modules, sets milestones, picks tech stack |
| 🏛️ **Architect** | Principal Architect | Claude 3.5 Sonnet | Designs system architecture, API contracts, DB schema, file structure |
| 💻 **Coder** | Senior Engineer | GPT-4o | Writes production-quality code, module by module, with retry on bug reports |
| 🧪 **Tester** | QA Automation | GPT-4o | Writes pytest suites, executes in isolated Docker sandbox, reports failures |
| 🔍 **Reviewer** | Staff Engineer | Claude 3.5 Sonnet | RAG-grounded code review against OWASP, PEP 8, and design patterns |
| 🚀 **DevOps** | Platform Engineer | Gemini 1.5 Pro | Generates Dockerfile, CI/CD config, deploys to staging |

### Agent Communication

Agents don't work in isolation — they pass structured state through a **LangGraph StateGraph**:

- **Tester → Coder**: Bug reports with file path, line number, and traceback
- **Reviewer → Coder**: HIGH-severity issue descriptions with fix suggestions + OWASP citations
- **All agents → Dashboard**: Real-time events over Redis Pub/Sub → WebSocket

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                 │
│   Next.js 14 + TailwindCSS + shadcn/ui conventions                │
│   Real-time dashboard · Monaco code viewer · Agent activity feed   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTPS + WebSocket (WSS)
┌───────────────────────────────▼─────────────────────────────────────┐
│                        API GATEWAY LAYER                            │
│         FastAPI (Python 3.11) + Uvicorn                             │
│   REST /api/v1/*   ·   WebSocket /ws/{session_id}                  │
│   SlowAPI rate limiting   ·   JWT auth   ·   CORS                  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                     ORCHESTRATION LAYER                             │
│              LangGraph Stateful Agent Pipeline                      │
│   Planner → Architect → Coder ⇄ Tester → Reviewer → DevOps        │
│   Celery Worker (async job execution)                               │
└──────┬────────────────────────┬───────────────────────┬─────────────┘
       │                        │                       │
┌──────▼──────┐  ┌──────────────▼────────┐  ┌──────────▼────────────┐
│  LLM LAYER  │  │     RAG LAYER         │  │   EXECUTION LAYER     │
│  GPT-4o     │  │  ChromaDB             │  │  Docker Sandbox       │
│  Claude 3.5 │  │  + text-embedding-3   │  │  --network none       │
│  Gemini 1.5 │  │  + LangChain          │  │  --user nobody        │
└──────┬──────┘  └──────────────┬────────┘  └──────────┬────────────┘
       │                        │                       │
┌──────▼────────────────────────▼───────────────────────▼────────────┐
│                          DATA LAYER                                 │
│   PostgreSQL 16  ·  Redis 7  ·  ChromaDB  ·  MinIO (S3-compat.)   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Next.js 14 (App Router) | Dashboard UI |
| **Styling** | Tailwind CSS + Framer Motion | Dark cyber theme + animations |
| **Code Editor** | Monaco Editor | Embedded code viewer |
| **State** | Zustand | Client-side state management |
| **Backend API** | FastAPI + Uvicorn | REST + WebSocket server |
| **Agent Framework** | LangGraph | Stateful, cyclical agent graph |
| **LLM Providers** | OpenAI + Anthropic + Google | Tiered model routing |
| **Job Queue** | Celery + Redis | Async pipeline execution |
| **Vector DB** | ChromaDB | RAG knowledge retrieval |
| **Embeddings** | text-embedding-3-small | Semantic search |
| **Primary DB** | PostgreSQL 16 | Sessions, events, artifacts |
| **Cache / PubSub** | Redis 7 | Real-time event streaming |
| **Object Storage** | MinIO (S3-compatible) | Generated file storage |
| **Sandbox** | Docker (isolated containers) | Safe code execution |
| **Reverse Proxy** | Nginx | Production load balancing |
| **Migrations** | Alembic | DB schema versioning |
| **Logging** | Structlog | JSON structured logs |
| **Tracing** | OpenTelemetry | Distributed request tracing |
| **CI/CD** | GitHub Actions | Automated test + build |

---

## 📁 Project Structure

```
MASDS/
├── .env                          # Your API keys (never commit this)
├── .env.example                  # Template — copy to .env
├── .gitignore
├── docker-compose.yml            # All 8 services
├── Makefile                      # Developer shortcuts
├── README.md
│
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions CI pipeline
│
├── backend/                      # FastAPI + LangGraph backend
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                   # FastAPI app entrypoint
│   │
│   ├── agents/                   # The 6 AI agents
│   │   ├── base_agent.py         # Abstract base with event emission
│   │   ├── planner_agent.py
│   │   ├── architect_agent.py
│   │   ├── coder_agent.py
│   │   ├── tester_agent.py
│   │   ├── reviewer_agent.py
│   │   └── devops_agent.py
│   │
│   ├── graph/                    # LangGraph pipeline
│   │   ├── state.py              # AgentState TypedDict
│   │   ├── builder.py            # StateGraph construction
│   │   ├── edges.py              # Conditional routing logic
│   │   └── runner.py             # Pipeline execution + events
│   │
│   ├── api/                      # FastAPI routes
│   │   ├── dependencies.py       # DB, Redis, auth injection
│   │   └── routes/
│   │       ├── sessions.py       # POST/GET /api/v1/sessions
│   │       ├── artifacts.py      # GET artifacts + ZIP download
│   │       └── ws.py             # WebSocket /ws/{session_id}
│   │
│   ├── rag/                      # RAG pipeline
│   │   ├── embedder.py           # OpenAI embedding wrapper
│   │   ├── retriever.py          # ChromaDB semantic search
│   │   └── ingestor.py           # Document ingestion + seeding
│   │
│   ├── sandbox/                  # Docker code execution
│   │   ├── executor.py           # Secure container runner
│   │   └── parser.py             # Pytest output parser
│   │
│   ├── services/
│   │   ├── event_bus.py          # Redis Pub/Sub event emitter
│   │   └── llm_router.py         # Tiered LLM selection
│   │
│   ├── db/
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   ├── crud.py               # Async DB operations
│   │   └── migrations/           # Alembic migration scripts
│   │
│   ├── config/
│   │   ├── settings.py           # Pydantic Settings
│   │   └── prompts/              # Agent system prompts
│   │       ├── planner.txt
│   │       ├── architect.txt
│   │       ├── coder.txt
│   │       ├── tester.txt
│   │       ├── reviewer.txt
│   │       └── devops.txt
│   │
│   ├── worker/
│   │   └── celery_app.py         # Async task runner
│   │
│   └── tests/
│       ├── test_sessions.py
│       ├── test_agents.py
│       └── test_sandbox.py
│
├── frontend/                     # Next.js 14 dashboard
│   ├── Dockerfile
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── next.config.mjs
│   │
│   ├── app/
│   │   ├── layout.tsx            # Root layout
│   │   ├── page.tsx              # Landing / requirement input
│   │   └── session/[id]/
│   │       └── page.tsx          # Live dashboard
│   │
│   ├── components/
│   │   ├── AgentCard.tsx         # Agent status card (animated)
│   │   ├── ActivityFeed.tsx      # Real-time event feed
│   │   ├── PipelineProgress.tsx  # Vertical stepper
│   │   ├── CodePanel.tsx         # Monaco file viewer
│   │   ├── TestResultPanel.tsx   # Test pass/fail display
│   │   ├── ReviewPanel.tsx       # Code review issues
│   │   └── ArtifactList.tsx      # Generated files + download
│   │
│   ├── hooks/
│   │   ├── useWebSocket.ts       # WS lifecycle + reconnect
│   │   └── useSession.ts         # Session polling
│   │
│   ├── stores/
│   │   └── sessionStore.ts       # Zustand global state
│   │
│   └── lib/
│       ├── api.ts                # Axios API client
│       ├── ws.ts                 # WebSocket client (exp. backoff)
│       └── utils.ts              # cn(), formatDuration(), etc.
│
└── infra/
    └── nginx/
        └── nginx.conf            # Reverse proxy + WS upgrade
```

---

## ✅ Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Docker Desktop | >= 4.0 | Must be running |
| Docker Compose | >= v2.0 | Bundled with Docker Desktop |
| OpenAI API Key | — | For Coder + Tester (GPT-4o) |
| Anthropic API Key | — | For Architect + Reviewer (Claude 3.5) |
| Google AI API Key | — | For Planner + DevOps (Gemini) |

> **Note**: You need all 3 API keys for the full pipeline. Each agent uses the optimal model for its task to balance quality and cost.

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-username/masds.git
cd masds
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your API keys:

```env
OPENAI_API_KEY=sk-...           # Required: Coder + Tester agents
ANTHROPIC_API_KEY=sk-ant-...    # Required: Architect + Reviewer agents
GOOGLE_API_KEY=AI...            # Required: Planner + DevOps agents
```

All other values (database, Redis, MinIO) are pre-configured for local Docker.

### 3. Launch all services

```bash
docker compose up --build
```

This starts **8 services** automatically:
- PostgreSQL, Redis, ChromaDB, MinIO (infrastructure)
- FastAPI backend + Celery worker (intelligence layer)
- Next.js frontend (dashboard)
- MinIO setup (auto-creates the `masds-artifacts` bucket)

First build takes ~3–5 minutes. Subsequent starts take ~30 seconds.

### 4. Open the dashboard

```
http://localhost:3000
```

### 5. Build your first app

Type a requirement like:

```
Build a REST API for a task management app with:
- User authentication (JWT)
- Projects and tasks CRUD
- Task assignment and due dates
- PostgreSQL database
- Rate limiting
```

Click **"Start Building"** and watch the agents work! 🚀

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ | — | OpenAI API key (GPT-4o) |
| `ANTHROPIC_API_KEY` | ✅ | — | Anthropic API key (Claude 3.5) |
| `GOOGLE_API_KEY` | ✅ | — | Google AI API key (Gemini) |
| `DATABASE_URL` | — | auto | PostgreSQL connection string |
| `REDIS_URL` | — | auto | Redis connection string |
| `CHROMADB_HOST` | — | `chromadb` | ChromaDB hostname |
| `S3_ENDPOINT_URL` | — | auto | MinIO endpoint |
| `JWT_SECRET_KEY` | — | `change-me` | JWT signing secret (change in prod!) |
| `MAX_CODER_RETRIES` | — | `3` | Max times coder retries on test failure |
| `MAX_REVIEWER_CYCLES` | — | `2` | Max review cycles before force-approve |
| `SANDBOX_TIMEOUT_SECONDS` | — | `60` | Max code execution time per run |
| `SANDBOX_MEMORY_LIMIT` | — | `512m` | Docker container memory cap |
| `LOG_LEVEL` | — | `INFO` | Logging verbosity |

### Makefile Commands

```bash
make dev          # Start all services (docker compose up)
make build        # Rebuild all Docker images
make down         # Stop all services
make logs         # Tail all container logs
make migrate      # Run Alembic DB migrations
make seed-rag     # Seed ChromaDB knowledge base
make test         # Run all backend tests
make backend-shell # Open shell in backend container
make clean        # Remove all containers + volumes (WARNING: deletes data)
make help         # Show all commands
```

---

## 📊 Dashboard Features

### Live Activity Feed
Real-time stream of every agent action — filterable by category:
- 🤖 Agent thinking messages
- 📄 File creation events
- ✅/❌ Test results
- 🔍 Review issues

### Pipeline Progress Stepper
Visual pipeline showing all 6 agents with:
- Live status (pending / running / complete / failed)
- Per-agent execution time
- Connecting lines animating green as stages complete
- Overall progress percentage

### Code Viewer (Monaco Editor)
- File tree grouped by directory
- Syntax highlighting for Python, TypeScript, YAML, Dockerfile, JSON
- Search across files
- One-click copy

### Test Results Panel
- Pass / fail counts with coverage bar
- Expandable accordion per failed test
- Full traceback with copy button

### Code Review Panel
- Circular quality score gauge (0–100)
- Issues grouped by severity: 🔴 HIGH · 🟡 MEDIUM · ⚫ LOW
- RAG source citations (OWASP, PEP 8, etc.)
- Approved / Rejected badge

### Artifacts Panel
- All generated files with type badges (Source / Tests / DevOps)
- Individual file inspector
- **Download All as ZIP** button

### WebSocket Reconnection
The dashboard auto-reconnects with exponential backoff (1s → 30s max) and replays missed events from Redis on reconnect — you never lose progress even if the tab is refreshed.

---

## 📡 API Reference

### REST Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/sessions` | Start a new pipeline run |
| `GET` | `/api/v1/sessions/{id}` | Get session status + agent progress |
| `GET` | `/api/v1/sessions/{id}/events` | Paginated event history |
| `GET` | `/api/v1/sessions/{id}/artifacts` | List all generated files |
| `GET` | `/api/v1/artifacts/{id}/content` | Get file content (text) |
| `GET` | `/api/v1/sessions/{id}/artifacts/download` | Download all files as ZIP |
| `GET` | `/health` | Health check (DB + Redis status) |

### WebSocket

```
WS ws://localhost:8000/ws/{session_id}
```

**Events streamed (server → client):**

```typescript
type WSEvent =
  | { type: 'AGENT_STARTED';    agent: AgentName }
  | { type: 'AGENT_THINKING';   agent: AgentName; message: string }
  | { type: 'AGENT_COMPLETE';   agent: AgentName; duration_s: number }
  | { type: 'AGENT_FAILED';     agent: AgentName; error: string }
  | { type: 'FILE_CREATED';     path: string; agent: AgentName }
  | { type: 'TEST_RESULT';      passed: number; failed: number; coverage: number }
  | { type: 'REVIEW_ISSUE';     severity: 'HIGH'|'MEDIUM'|'LOW'; file: string }
  | { type: 'PIPELINE_COMPLETE'; staging_url: string }
  | { type: 'PIPELINE_FAILED';   error: string }
  | { type: 'PING' }
```

### Interactive Docs

```
http://localhost:8000/docs      # Swagger UI
http://localhost:8000/redoc     # ReDoc
```

---

## 📚 RAG Knowledge Base

The **Reviewer** and **Architect** agents query a ChromaDB vector store seeded with curated knowledge:

| Collection | Sources | Used By |
|---|---|---|
| `security` | OWASP Top 10, CVE patterns | Reviewer |
| `best_practices` | PEP 8, PEP 20, Clean Code | Reviewer |
| `frameworks` | FastAPI docs, React docs, SQLAlchemy | Architect, Coder |
| `patterns` | Design patterns, REST conventions | Architect |

### Seeding the knowledge base

```bash
make seed-rag
# or manually:
docker compose exec backend python -m rag.ingestor
```

You can add custom documents:

```python
from rag.ingestor import DocumentIngestor

ingestor = DocumentIngestor()
await ingestor.ingest_url(
    url="https://your-internal-docs.com/api-standards",
    collection="best_practices"
)
```

---

## 🔒 Code Execution Sandbox

All generated code is executed in **fully isolated Docker containers** with:

| Security Layer | Configuration |
|---|---|
| Network | `--network none` (no internet access) |
| User | `--user nobody` (non-root) |
| CPU | `--cpus 0.5` (half core max) |
| Memory | `--memory 512m` |
| Filesystem | `tmpfs` workspace only (ephemeral) |
| Syscalls | Seccomp profile (blocks dangerous calls) |
| Timeout | Hard kill after 60 seconds |

**Supported runtimes:**

| Language | Image | Test Framework |
|---|---|---|
| Python | `python:3.11-slim` | pytest |
| JavaScript | `node:20-slim` | Jest |
| TypeScript | `node:20-slim` | Jest + ts-jest |

---

## 🧑‍💻 Development Guide

### Running locally (without Docker)

**Backend:**
```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Start only infrastructure services
docker compose up postgres redis chromadb minio -d

# Run backend
uvicorn main:app --reload --port 8000
```

**Celery worker (separate terminal):**
```bash
celery -A worker.celery_app worker --loglevel=info
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev     # http://localhost:3000
```

### Adding a New Agent

1. Create `backend/agents/my_agent.py` extending `BaseAgent`
2. Add system prompt to `backend/config/prompts/my_agent.txt`
3. Register in `backend/graph/builder.py` as a new node
4. Add conditional edges in `backend/graph/edges.py`
5. Update `AgentState` in `backend/graph/state.py` if new state fields are needed

---

## 🧪 Running Tests

```bash
# All tests via Makefile
make test

# Backend tests with coverage
docker compose exec backend pytest tests/ -v --cov=. --cov-report=term-missing

# Specific test file
docker compose exec backend pytest tests/test_agents.py -v

# Frontend lint + type check
docker compose exec frontend npm run lint
```

### Test Suite Overview

| File | What It Tests |
|---|---|
| `tests/test_sessions.py` | Session create/get/events API endpoints |
| `tests/test_agents.py` | Agent output parsing, retry logic, approval gates |
| `tests/test_sandbox.py` | Docker execution, timeout handling, syntax errors |

---

## 🌐 Deployment

### Production with Docker Compose + Nginx

```bash
# 1. Set production secrets
cp .env.example .env.prod
# Fill in real API keys and a strong JWT_SECRET_KEY

# 2. Launch with production compose
docker compose -f docker-compose.yml --env-file .env.prod up -d

# 3. Nginx handles all routing
#    /         -> frontend:3000
#    /api/     -> backend:8000
#    /ws/      -> backend:8000 (WebSocket upgrade headers applied)
```

### Cloud Deployment Options

The project is container-first and works on any Docker-capable platform:

**Railway (easiest):**
```bash
railway login && railway init && railway up
```

**AWS ECS + managed services:**
- Deploy `backend` + `worker` as ECS Fargate services
- Replace `postgres` with RDS PostgreSQL
- Replace `redis` with ElastiCache Redis
- Replace MinIO with AWS S3 (update `S3_ENDPOINT_URL=https://s3.amazonaws.com`)
- Deploy `frontend` to Vercel (zero config for Next.js)

---

## 💰 Cost Estimation

MASDS uses a **tiered LLM strategy** to minimize API costs:

| Agent | Model | Avg tokens/run | Est. cost |
|---|---|---|---|
| Planner | Gemini 1.5 Flash | ~2,000 | ~$0.001 |
| Architect | Claude 3.5 Sonnet | ~4,000 | ~$0.060 |
| Coder | GPT-4o | ~8,000 | ~$0.200 |
| Tester | GPT-4o | ~5,000 | ~$0.120 |
| Reviewer | Claude 3.5 Sonnet | ~6,000 | ~$0.090 |
| DevOps | Gemini 1.5 Pro | ~3,000 | ~$0.010 |
| **Total** | | **~28,000** | **~$0.48/run** |

> Estimates for a medium-complexity project (5–8 modules). Larger projects or retry cycles increase cost.

**Cost-saving tips:**
- Set `MAX_CODER_RETRIES=1` for simpler projects
- Switch Coder to `gpt-4o-mini` in `services/llm_router.py` for a budget mode (~60% cheaper)
- Frequent RAG queries are cached in Redis (1h TTL) — no re-embedding cost

---

## 🗺️ Roadmap

- [x] 6-agent autonomous pipeline (Plan → Code → Test → Review → Deploy)
- [x] Real-time WebSocket dashboard
- [x] Docker sandbox for safe code execution
- [x] RAG-backed code review (OWASP, PEP 8)
- [x] Artifact download as ZIP
- [ ] **v1.1** — Multi-language support (Go, Java, Rust)
- [ ] **v1.2** — Agent debate mode (agents challenge each other's decisions)
- [ ] **v1.3** — GitHub integration (auto-create PR with generated code)
- [ ] **v1.4** — Custom RAG ingestion UI (paste your own docs/style guides)
- [ ] **v2.0** — Multi-user sessions with real-time collaboration
- [ ] **v2.1** — Fine-tuned agents on your codebase patterns

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

```bash
# Fork the repo, then:
git clone https://github.com/your-username/masds.git
cd masds
git checkout -b feature/your-feature-name
```

**Guidelines:**
- Follow the existing agent pattern when adding new agents
- Write tests for new features in the `tests/` directory
- Use `structlog` for logging (not `print`)
- Keep agent prompts in `config/prompts/` files, not hardcoded in Python
- Run `make test` before submitting a PR

**Good first issues:**
- Add a new RAG collection for a framework you love
- Improve the Reviewer agent's OWASP prompt coverage
- Add JavaScript/TypeScript support to the sandbox executor
- Improve the dashboard UI for mobile screen sizes

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with LangGraph · FastAPI · Next.js · ChromaDB · Docker**

*Concepts: Agentic AI · LLM Orchestration · RAG · Real-time Systems · DevOps Automation*

⭐ **Star this repo if it helped you!** ⭐

</div>
