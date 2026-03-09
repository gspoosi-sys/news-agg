# Balanced News Aggregator

Stay informed about the world without the overwhelm. This app combats doom-scrolling by:

- **Need to Know**: Major political and geopolitical events summarized as calm, objective TL;DRs (max 5 at a time)
- **Positive Feed**: A scrollable feed of uplifting, solution-oriented, and hopeful news
- **Deep Dive**: Click any summary to read the full AI-generated summary and link to the original source

AI-powered by Claude (`claude-sonnet-4-6`) for categorization, sentiment analysis, and TL;DR generation.

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- An [Anthropic API key](https://console.anthropic.com/) or a [Gemini API key](https://aistudio.google.com/)
- Optionally: [NewsAPI key](https://newsapi.org/) and [Guardian API key](https://open-platform.theguardian.com/)

### Setup

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd news-agg

# 2. Configure environment
cp .env.example .env
# Edit .env and fill in ANTHROPIC_API_KEY or GEMINI_API_KEY (minimum required)

# 3. Start everything
docker compose up --build

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Manual ingestion trigger

```bash
curl -X POST http://localhost:8000/api/refresh \
  -H "X-API-Key: change-me-in-production"
```

### Run backend tests

```bash
docker compose exec backend python -m pytest tests/ -v
```

---

## Architecture

See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for full system design and data flow.

**Stack**: FastAPI + PostgreSQL + Redis (backend) · Next.js 14 + Tailwind CSS (frontend) · Claude or Gemini API (AI)

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/need-to-know` | Top 5 political articles (cached 5 min) |
| `GET` | `/api/feed?page=1&limit=20` | Paginated positive feed (cached 5 min) |
| `GET` | `/api/articles/{id}` | Full article detail |
| `POST` | `/api/refresh` | Manually trigger ingestion (requires `X-API-Key`) |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |
