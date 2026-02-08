.PHONY: install migrate runserver daphne worker beat test frontend up down

install:
	python -m pip install -r requirements.txt

migrate:
	python manage.py makemigrations
	python manage.py migrate

runserver:
	python manage.py runserver 0.0.0.0:8000

daphne:
	daphne -b 0.0.0.0 -p 8000 config.asgi:application

worker:
	celery -A config worker -l info

beat:
	celery -A config beat -l info

frontend:
	cd frontend && npm install && npm run dev

test:
	pytest

up:
	docker compose up --build

down:
	docker compose down
