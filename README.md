# AI Resume Analyzer

An explainable, deterministic natural language processing (NLP) platform for automated resume evaluation, candidate competency extraction, and job compatibility assessment.

Developed as a Computer Engineering capstone project with a **FastAPI** backend and a **Next.js (App Router)** TypeScript frontend.

---

## System Architecture

```
AI Resume Analyzer
├── api/
│   └── index.py             # Serverless entrypoint for Vercel deployment
├── app/                     # Next.js 14 App Router (Page components & theme)
├── backend/                 # Python backend modules
│   ├── analyzer.py          # Deterministic NLP engine (spaCy PhraseMatcher + Heuristics)
│   ├── database.py          # SQLAlchemy 2.0 session manager & serverless connection pool
│   ├── main.py              # FastAPI REST endpoints & payload validators
│   ├── models.py            # PostgreSQL ORM schema (JSONB columns & UUIDs)
│   └── report_generator.py  # ReportLab in-memory branded PDF report generator
├── scripts/
│   ├── migrate.py           # Database migration & schema initialization utility
│   └── test_local_e2e.py    # Automated 10-test validation runner
├── package.json             # Lightweight frontend dependencies
├── requirements.txt         # Lean backend dependencies (serverless-optimized)
├── vercel.json              # Production routing configuration
└── ROADMAP.md               # Final-year engineering design & viva roadmap
```

---

## Core Features & Technical Methodology

1. **Deterministic Skill Extraction**: Uses spaCy's `PhraseMatcher` with a canonical multi-alias taxonomy (normalizing terms like `Postgres` $\rightarrow$ `postgresql`, `K8s` $\rightarrow$ `kubernetes`, `ReactJS` $\rightarrow$ `react`).
2. **Noise-Filtered Keyword Alignment**: Computes token set intersection between the job description and candidate resume minus stop words.
3. **Structural Section Verification**: Regex-based detection for standard ATS headers (*Experience*, *Education*, *Skills*, *Projects*, *Summary*).
4. **Format & Contact Integrity**: Validates RFC-compliant email formatting and document length bounds (250 – 12,000 characters).
5. **Persistent Traceability**: Commits complete evaluation records and extracted skill arrays as JSONB to PostgreSQL.
6. **Payload Guardrails**: Enforces a 2 MB upload limit with `%PDF-` binary magic-byte validation and encrypted document rejection.

---

## Local Development Setup

### 1. Prerequisites
- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- [PostgreSQL](https://www.postgresql.org/download/) (or a free cloud database like [Neon](https://neon.tech))

### 2. Backend Setup
1. Create and activate a Python virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install lean backend dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Copy environment configuration and configure your database:
   ```powershell
   Copy-Item .env.example .env
   ```
4. Run schema migration:
   ```powershell
   python scripts/migrate.py
   ```
5. Start the FastAPI API server:
   ```powershell
   uvicorn backend.main:app --reload --port 8000
   ```
   API interactive docs: <http://127.0.0.1:8000/docs>

### 3. Frontend Setup
In a second terminal:
```powershell
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Production Deployment (Vercel)

1. Push this repository to GitHub.
2. Import the repository into **Vercel**.
3. Set the environment variable in Vercel:
   - `DATABASE_URL`: Hosted PostgreSQL connection string (from Neon, Supabase, etc. with `sslmode=require`).
4. Run `python scripts/migrate.py` against your hosted database to initialize tables.
5. Deploy.
