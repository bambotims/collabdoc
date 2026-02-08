# Infrastructure notes

Use root `docker-compose.yml` for local full-stack runtime.

Services:
- web (Django ASGI with Daphne)
- postgres
- redis
- celery-worker
- celery-beat
- frontend (Vite)

Local backend commands:
- `python manage.py runserver 0.0.0.0:8000` (WebSocket-capable via `daphne` app integration)
- `daphne -b 0.0.0.0 -p 8000 config.asgi:application`

Render deployment:
- This repo includes `render.yaml` for a Blueprint deployment.
- Services provisioned by the blueprint:
- `collabdoc-web` (Django + Channels + built frontend served on same origin)
- `collabdoc-worker` (Celery worker)
- `collabdoc-beat` (Celery beat)
- `collabdoc-redis` (Redis)
- `collabdoc-db` (Postgres)
- In Render dashboard: `New +` -> `Blueprint` -> select this repo -> apply.
- The web service runs `python manage.py migrate` on boot before starting Daphne.
- After first deploy, create a Django superuser in a one-off shell:
- `python manage.py createsuperuser`
