# Infrastructure notes

Use root `docker-compose.yml` for local full-stack runtime.

Services:
- web (Django ASGI with Daphne)
- postgres
- redis
- celery-worker
- celery-beat
- frontend (Vite)
