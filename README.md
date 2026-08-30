# AI Social Media Automation

Production-ready AI Social Media Automation SaaS built with React, Tailwind CSS, TypeScript, FastAPI, MongoDB, Redis, Celery, cron scheduling, Docker, and Nginx.

## What It Does

When a new blog, page, tool, or article is published, the system can detect it from WordPress, RSS, custom URLs, sitemap XML, or webhook triggers. It extracts page metadata, summarizes the content, generates platform-specific social copy, creates image assets, schedules publishing, publishes to connected social accounts, and stores analytics.

## Modules

- Frontend admin panel: dashboard, websites, content, AI Studio, connected accounts, schedules, analytics, settings, logs.
- Backend API: JWT auth, Google login endpoint, RBAC, rate limiting, security headers, Swagger docs.
- AI services: OpenAI or Gemini adapters for posts, hashtags, CTA, summaries, callouts, carousel and quote-card text.
- Image services: OpenAI image generation with local storage path and S3-ready settings.
- Social adapters: Facebook Pages, Instagram Business, LinkedIn Pages, X/Twitter, Threads, Pinterest, Telegram Channel.
- Jobs: Celery workers and cron scheduler for website scans and due-post publishing.
- Data: MongoDB repositories and typed domain models.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

## Hostinger Deployment

For the complete app, use Hostinger VPS or a Hostinger app hosting plan that can run the Python backend, MongoDB, Redis, worker, and scheduler. Uploading only the frontend files to shared PHP/static hosting will not support login, prompt generation, scheduling, or Facebook publishing.

See [docs/HOSTINGER_DEPLOYMENT.md](docs/HOSTINGER_DEPLOYMENT.md).

Generate a Fernet key for `ENCRYPTION_KEY`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Development

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Worker:

```bash
cd backend
celery -A app.core.celery_app.celery_app worker --loglevel=INFO
```

Scheduler:

```bash
cd backend
python -m app.scheduler.cron
```

## API Documentation

Swagger is served at `/docs`. The OpenAPI schema is served at `/api/v1/openapi.json`.

## Security

The application includes JWT authentication, Google token verification, role-based access control, encrypted social tokens, API rate limiting, validation through Pydantic, security headers, and an audit log model.
