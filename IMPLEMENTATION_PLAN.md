# Balanced News Aggregator — Implementation Plan

## Overview

A web application designed to combat doom-scrolling by keeping users informed about essential global events without overwhelming them. The app features a "Need to Know" section for major political events (presented as objective TL;DRs) and a primary positive news feed.

---

## Recommended Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| **Frontend** | Next.js 14 (App Router) + TypeScript | SSR for fast initial load, file-based routing, ISR for cached pages |
| **Styling** | Tailwind CSS | Rapid, responsive UI without a heavy component library |
| **Backend** | FastAPI (Python 3.12) | Async, first-class type hints, natural fit for the Anthropic Python SDK |
| **AI / Summarization** | Claude API (`claude-sonnet-4-6`) | Categorization, sentiment scoring, TL;DR generation |
| **Database** | PostgreSQL + SQLAlchemy + Alembic | Relational, proven, full-text search capable |
| **Cache / Dedup** | Redis | API response caching (5-min TTL), URL deduplication (7-day TTL) |
| **Task Scheduling** | APScheduler | Background ingestion every 30 minutes |
| **Containerization** | Docker + Docker Compose | Single-command local development setup |

---

## System Architecture

```
┌────────────────────────────────────────────────────────┐
│                  Ingestion Worker                      │
│              (APScheduler, every 30 min)               │
│                                                        │
│  Sources:                                              │
│  • NewsAPI.org (REST)                                  │
│  • The Guardian Open Platform (REST)                   │
│  • RSS feeds: BBC, Reuters, AP, Good News Network,     │
│    Positive News, Solutions Journalism                 │
└───────────────────────┬────────────────────────────────┘
                        │ raw articles
                        ▼
┌────────────────────────────────────────────────────────┐
│              Redis Deduplicator                        │
│         (SHA-256 URL hash, 7-day TTL)                  │
└───────────────────────┬────────────────────────────────┘
                        │ new articles only
                        ▼
┌────────────────────────────────────────────────────────┐
│                   AI Pipeline                          │
│           (Claude API — claude-sonnet-4-6)             │
│                                                        │
│  Per article, Claude returns JSON:                     │
│  • category: "political" | "positive" | "neutral"      │
│             | "negative"                               │
│  • sentiment_score: float -1.0 → 1.0                  │
│  • tldr: 1-2 sentence objective summary                │
│  • keep: boolean (filter ads/clickbait)                │
└───────────────────────┬────────────────────────────────┘
                        │ categorized articles
                        ▼
┌────────────────────────────────────────────────────────┐
│                  PostgreSQL                            │
│  articles(id, url, title, source, image_url,           │
│    description, category, sentiment_score, tldr,       │
│    published_at, created_at)                           │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│              FastAPI REST API                          │
│  GET  /api/need-to-know   → top 5 political articles   │
│  GET  /api/feed           → paginated positive feed    │
│  GET  /api/articles/{id}  → full article detail        │
│  POST /api/refresh        → manual ingestion trigger   │
│                                                        │
│  Redis caching on /need-to-know and /feed (5-min TTL)  │
└───────────────────────┬────────────────────────────────┘
                        │ JSON
                        ▼
┌────────────────────────────────────────────────────────┐
│              Next.js Frontend                          │
│  /            → Header + NeedToKnow + PositiveFeed     │
│  /article/[id] → Deep Dive page                        │
└────────────────────────────────────────────────────────┘
```

---

## Data Sources

| Source | Type | Notes |
|---|---|---|
| **NewsAPI.org** | REST API | 100 req/day free tier; `top-headlines` endpoint |
| **The Guardian** | REST API | Free API key; `trailText` + `thumbnail` fields |
| **BBC News** | RSS | `http://feeds.bbci.co.uk/news/rss.xml` |
| **Reuters** | RSS | `https://feeds.reuters.com/reuters/topNews` |
| **Good News Network** | RSS | `https://www.goodnewsnetwork.org/feed/` |
| **Positive News** | RSS | `https://www.positive.news/feed/` |
| **Solutions Journalism** | RSS | `https://thewholestory.solutionsjournalism.org/feed` |

The system fetches from all sources every 30 minutes, deduplicates by URL, and only sends new articles through the (paid) Claude API pipeline.

---

## Feed Filtering Logic

| Category | Sentiment | Outcome |
|---|---|---|
| `political` | any | → Need to Know section (capped at 5) |
| `positive` | ≥ 0.2 | → Main positive feed |
| `neutral` | ≥ 0.4 | → Main positive feed |
| `keep == false` | any | Discarded (ads, clickbait) |
| `negative` | any | Discarded |
| `neutral` | < 0.4 | Discarded |

---

## Project Structure

```
news-agg/
├── docker-compose.yml
├── .env.example
├── IMPLEMENTATION_PLAN.md
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 0001_create_articles_table.py
│   ├── app/
│   │   ├── main.py          # FastAPI app + APScheduler startup
│   │   ├── config.py        # Pydantic settings (env vars)
│   │   ├── database.py      # SQLAlchemy engine + session
│   │   ├── models.py        # Article ORM model
│   │   ├── schemas.py       # Pydantic response models
│   │   ├── api/
│   │   │   └── routes.py    # All API endpoints
│   │   ├── ingestion/
│   │   │   ├── fetcher.py      # NewsAPI + RSS fetching
│   │   │   ├── deduplicator.py # Redis URL dedup
│   │   │   └── scheduler.py    # Main ingestion job
│   │   └── ai/
│   │       └── pipeline.py     # Claude API integration
│   └── tests/
│       └── test_pipeline.py    # Unit tests (mocked Claude)
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── next.config.ts
    ├── tailwind.config.ts
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx              # Home page (SSR)
        │   └── article/[id]/
        │       └── page.tsx          # Deep Dive page
        ├── components/
        │   ├── Header.tsx
        │   ├── NeedToKnow.tsx        # Collapsible political section
        │   ├── PositiveFeed.tsx      # Infinite-scroll positive feed
        │   └── ArticleCard.tsx       # Shared card component
        └── lib/
            └── api.ts                # Typed API fetch helpers
```

---

## Development Phases

### Phase 1: Project Scaffolding
- `docker-compose.yml` with backend, frontend, db, redis services
- Backend: FastAPI skeleton, SQLAlchemy models, Alembic migration
- Frontend: Next.js + Tailwind scaffold
- `.env.example` with all required variables
- Verify `docker compose up --build` starts all services

### Phase 2: Data Ingestion & AI Pipeline
- `fetcher.py`: fetch from NewsAPI + RSS feeds via `feedparser` + `httpx`
- `deduplicator.py`: Redis SHA-256 URL hash dedup (7-day TTL)
- `pipeline.py`: Claude API structured JSON response (category + sentiment + tldr + keep)
- `scheduler.py`: orchestrate fetch → dedup → AI → DB store
- APScheduler wired into FastAPI startup event (30-min interval)
- Unit tests with mocked Claude responses

### Phase 3: Backend API
- `GET /api/need-to-know`: top 5 political articles
- `GET /api/feed?page=N&limit=20`: paginated positive/neutral feed
- `GET /api/articles/{id}`: full article detail
- `POST /api/refresh`: authenticated manual trigger
- Redis caching on feed endpoints (5-min TTL)
- CORS configured for Next.js origin

### Phase 4: Frontend UI
- **Home page**: sticky header + NeedToKnow panel + PositiveFeed
- **NeedToKnow**: collapsible section, muted gray palette, objective framing
- **PositiveFeed**: "Load more" pagination, loading skeletons
- **ArticleCard**: shared card with image (positive only), source badge, tldr
- **Deep Dive page `/article/[id]`**: full tldr box, sentiment badge, link to original
- ISR (`revalidate = 300`) for server-side caching

### Phase 5: Polish & Production Readiness
- Error boundaries in frontend, graceful empty states
- Structured JSON logging in backend
- Unique constraint on `articles.url` prevents DB-level duplicates
- `POST /api/refresh` protected by `X-API-Key` header
- Update README with full setup instructions

---

## Environment Variables

```bash
# AI
ANTHROPIC_API_KEY=sk-ant-...

# News APIs (optional but recommended)
NEWS_API_KEY=...          # newsapi.org
GUARDIAN_API_KEY=...      # open-platform.theguardian.com

# Database
DATABASE_URL=postgresql://postgres:password@db:5432/newsagg

# Redis
REDIS_URL=redis://redis:6379/0

# App
INGESTION_INTERVAL_MINUTES=30
MAX_POLITICAL_ARTICLES=5
MAX_POSITIVE_ARTICLES=50
REFRESH_API_KEY=change-me-in-production
```

---

## End-to-End Verification

1. Copy `.env.example` → `.env` and fill in your API keys
2. `docker compose up --build` — wait for all 4 services to be healthy
3. Check startup logs: initial ingestion should run automatically
4. `curl -X POST http://localhost:8000/api/refresh -H "X-API-Key: change-me-in-production"` — manually trigger
5. `curl http://localhost:8000/api/need-to-know` — should return ≤5 political articles with `tldr`
6. `curl http://localhost:8000/api/feed` — should return positive articles with `sentiment_score ≥ 0.2`
7. Open `http://localhost:3000` — Need to Know at top, scrollable positive feed below
8. Click any card → Deep Dive page with AI summary + "Read original article" button
9. Run backend tests: `docker compose exec backend python -m pytest tests/ -v`
