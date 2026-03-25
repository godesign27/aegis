# Aegis — development convenience commands
# Usage: make <target>

.PHONY: install build dev api rebuild help

## Install Python dependencies
install:
	pip install -r requirements.txt

## Build the React frontend into frontend/dist
build:
	cd frontend && npm install && npm run build

## Start the FastAPI server (serves built UI at http://localhost:8000)
api:
	uvicorn aegis.main:app --reload --host 0.0.0.0 --port 8000

## Start the Vite dev server on port 5173 (with hot-reload, proxies API to 8000)
dev:
	cd frontend && npm run dev

## Rebuild frontend then restart API  (single terminal shortcut)
rebuild: build
	@echo "✓ Frontend rebuilt — restart the API server to pick up changes."

## Run tests
test:
	pytest tests/ -v

help:
	@echo ""
	@echo "  make install   Install Python deps"
	@echo "  make build     Build React → frontend/dist"
	@echo "  make api       Start FastAPI on :8000  (serves built UI)"
	@echo "  make dev       Start Vite dev server on :5173 (hot-reload)"
	@echo "  make rebuild   Rebuild frontend (then restart API)"
	@echo "  make test      Run test suite"
	@echo ""
