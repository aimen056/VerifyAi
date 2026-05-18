# VerifyAI — AI-Powered Fake News & Screenshot Verification Platform

> Monorepo for the VerifyAI platform. Built with **FastAPI** (Python) + **Next.js 14** (TypeScript).

## 📁 Project Structure

```
verifyai/
├── backend/                    # FastAPI REST API
│   ├── app/
│   │   ├── main.py             # App entry point + ML lifecycle
│   │   ├── config.py           # Environment settings
│   │   ├── models/             # Pydantic schemas
│   │   ├── routers/            # API route handlers
│   │   ├── database/           # Async SQLAlchemy
│   │   └── services/           # AI pipeline
│   │       ├── base.py         # Abstract interfaces
│   │       ├── classifier.py   # RoBERTa fake news classifier
│   │       ├── processor.py    # Tesseract OCR
│   │       ├── fact_checker.py # Google Fact Check API
│   │       ├── explainer.py    # SHAP explainability
│   │       └── pipeline.py     # Orchestrator
│   ├── .env                    # Backend environment
│   └── requirements.txt        # Python dependencies
├── frontend/                   # Next.js 14 (App Router)
│   ├── src/
│   │   ├── app/                # Pages & layouts
│   │   ├── components/         # UI components
│   │   │   └── ui/             # shadcn/ui primitives
│   │   └── lib/                # API client & utilities
│   └── .env.local              # Frontend environment
├── docker-compose.yml          # PostgreSQL + Redis
├── platform-spec.md            # Product specification
└── README.md                   # You are here
```

## 🧠 AI Pipeline (Phase 2)

The verification pipeline chains four services:

1. **Tesseract OCR** (`processor.py`) — Extracts text from screenshot images
2. **RoBERTa Classifier** (`classifier.py`) — Fine-tuned fake news detection model (`hamzab/roberta-fake-news-classification`)
3. **SHAP Explainer** (`explainer.py`) — Token-level attribution for transparent verdicts
4. **Google Fact Check API** (`fact_checker.py`) — Cross-references claims against fact-check databases

**Data Flow:** `Input → [OCR] → RoBERTa Classification → SHAP Explanation → Fact-Check Lookup → Verdict`

## 🚀 Quick Start

### 1. Start Infrastructure
```bash
docker compose up -d
```
This starts PostgreSQL (port 5432) and Redis (port 6379).

### 2. Start Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
> **Note:** First startup downloads the RoBERTa model (~500MB). Subsequent starts use the cached version.

API docs available at: http://localhost:8000/docs

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:3000

### 4. System Dependencies

- **Tesseract OCR**: [Install for Windows](https://github.com/UB-Mannheim/tesseract/wiki) — set `TESSERACT_CMD` in `.env`
- **Google Fact Check API**: [Get API key](https://console.cloud.google.com/apis/credentials) — set `GOOGLE_FACTCHECK_API_KEY` in `.env`

## 🔌 API Endpoints

| Method | Path           | Description                    |
|--------|----------------|--------------------------------|
| GET    | `/health`      | Health check + pipeline status |
| POST   | `/verify/text`  | Verify a text headline         |
| POST   | `/verify/image` | Verify an uploaded screenshot  |
| POST   | `/verify/url`   | Verify a news article URL      |

## ⚙️ Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `ML_MODEL_NAME` | `hamzab/roberta-fake-news-classification` | HuggingFace model ID |
| `ML_DEVICE` | auto-detect | Force `cpu` or `cuda` |
| `TESSERACT_CMD` | system PATH | Path to Tesseract binary |
| `GOOGLE_FACTCHECK_API_KEY` | — | Google Fact Check API key |
| `SHAP_TIMEOUT_SECONDS` | `30` | Max SHAP computation time |

## 🏗️ Phase Roadmap

- [x] **Phase 1** — Project scaffolding & Hello World connectivity
- [x] **Phase 2** — AI Pipeline (RoBERTa, SHAP, OCR, Fact-Check API)
- [ ] **Phase 3** — Frontend polish & admin dashboard
