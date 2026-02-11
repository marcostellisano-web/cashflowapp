.PHONY: dev dev-backend dev-frontend build test

dev: dev-backend dev-frontend

dev-backend:
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

build:
	cd frontend && npm run build

test:
	cd backend && python -m pytest tests/ -v

docker-up:
	docker compose up --build

docker-down:
	docker compose down
