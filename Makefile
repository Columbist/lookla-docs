.PHONY: up down restart logs shell-api shell-db test lint fmt migrate backup bootstrap

# ── Services ──────────────────────────────────────────────────────────────────

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart api web

logs:
	docker compose logs -f api web

shell-api:
	docker exec -it beauty_api bash

shell-db:
	docker exec -it beauty_db psql -U $${DB_USER:-beauty} $${DB_NAME:-beauty_gr}

# ── Development ───────────────────────────────────────────────────────────────

bootstrap:
	@echo "==> Copying .env.example → .env (skip if exists)"
	@cp -n .env.example .env || true
	@echo "==> Installing pre-commit hooks"
	pre-commit install
	@echo "==> Starting services"
	docker compose up -d
	@echo ""
	@echo "Done. Edit .env with real values, then run: make migrate"

# ── Database ──────────────────────────────────────────────────────────────────

migrate:
	docker exec beauty_api alembic upgrade head

migrate-status:
	docker exec beauty_api alembic current

backup:
	docker exec beauty_db pg_dump -U $${DB_USER:-beauty} $${DB_NAME:-beauty_gr} \
	  | gzip > /opt/backups/lookla_manual_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "Backup saved to /opt/backups/"

# ── Quality ───────────────────────────────────────────────────────────────────

lint:
	docker exec beauty_api ruff check app/
	cd frontend && npm run lint

fmt:
	docker exec beauty_api ruff format app/
	cd frontend && npx prettier --write .

test:
	docker exec beauty_api pytest --tb=short

test-v:
	docker exec beauty_api pytest -v

# ── Health ────────────────────────────────────────────────────────────────────

health:
	@curl -sf https://lookla.gr/api/health | python3 -m json.tool || \
	  curl -sf http://localhost:8000/api/health | python3 -m json.tool
