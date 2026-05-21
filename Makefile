# GiziGo top-level Makefile
# Solo developer, time-budgeted hackathon build. Keep targets boring and fast.

SHELL := /bin/bash
.DEFAULT_GOAL := help

PYTHON := python3.13
API_DIR := services/api
WEB_DIR := apps/web
VENV := $(API_DIR)/.venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
UVICORN := $(VENV)/bin/uvicorn

.PHONY: help bootstrap api-venv web-install postgres-up postgres-down db-init data api-dev web-dev lint test deploy submission-bundle clean

help:
	@echo "GiziGo make targets:"
	@echo "  bootstrap          - Install api venv + web deps + start local postgres + run db-init"
	@echo "  api-venv           - Create Python venv and install API deps"
	@echo "  web-install        - Install web app dependencies via pnpm"
	@echo "  postgres-up        - Start local Postgres docker container on :5433"
	@echo "  postgres-down      - Stop local Postgres docker container"
	@echo "  db-init            - Run schema bootstrap against local Postgres"
	@echo "  data               - Run scrape + normalize + validate data pipeline"
	@echo "  api-dev            - Run FastAPI in dev mode on :8001"
	@echo "  web-dev            - Run Vite dev server on :5173"
	@echo "  lint               - Run ruff + tsc"
	@echo "  test               - Run pytest"
	@echo "  deploy             - Build web + push to vpsgw + restart systemd"
	@echo "  submission-bundle  - Produce a clean tarball of the repo for archival"
	@echo "  clean              - Remove venv, node_modules, dist"

bootstrap: api-venv web-install postgres-up db-init
	@echo "==> Bootstrap complete."

api-venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "==> Creating Python venv at $(VENV)"; \
		$(PYTHON) -m venv $(VENV); \
	fi
	$(PIP) install --upgrade pip wheel
	$(PIP) install -e "$(API_DIR)[dev]"

web-install:
	cd $(WEB_DIR) && pnpm install --frozen-lockfile

postgres-up:
	bash scripts/docker-postgres.sh up

postgres-down:
	bash scripts/docker-postgres.sh down

db-init: postgres-up
	@sleep 2
	docker exec -i gizigo-pg psql -U gizigo -d gizigo < scripts/db-init.sql

data:
	$(PY) $(API_DIR)/scripts/scrape_panganku.py
	$(PY) $(API_DIR)/scripts/normalize_panganku.py

api-dev:
	cd $(API_DIR) && PYTHONHASHSEED=0 ../../$(VENV)/bin/uvicorn src.main:app --reload --host 127.0.0.1 --port 8001

web-dev:
	cd $(WEB_DIR) && pnpm dev

lint:
	$(VENV)/bin/ruff check $(API_DIR)
	cd $(WEB_DIR) && pnpm tsc --noEmit

test:
	cd $(API_DIR) && ../../$(VENV)/bin/pytest -q

deploy:
	bash scripts/deploy.sh

submission-bundle:
	bash scripts/make-submission-bundle.sh

clean:
	rm -rf $(VENV)
	rm -rf $(WEB_DIR)/node_modules $(WEB_DIR)/dist
	@echo "==> Clean complete."
