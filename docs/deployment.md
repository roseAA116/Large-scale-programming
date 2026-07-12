# Deployment Guide

## Environment

Copy `backend/.env.example` to `backend/.env` and set production values for database, Redis, object storage, JWT secret, LLM, embeddings, and `COURSE_AGENT_ADMIN_EMAILS`.

## Database Migration

Run migrations before starting the API:

```powershell
cd backend
alembic upgrade head
```

## Start Services

Development:

```powershell
docker compose up -d
.\scripts\start_backend.ps1
.\scripts\start_worker.ps1
```

Production-style compose:

```powershell
docker compose -f docker-compose.prod.yml up -d --build
```

## HTTPS

Terminate HTTPS at a reverse proxy such as Nginx, Caddy, or a cloud load balancer. Forward `/api` to the backend and serve the frontend build as static files. Enable HSTS after certificates and redirects are verified.
