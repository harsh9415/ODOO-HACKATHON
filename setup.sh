#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "==> Starting PostgreSQL (Docker)..."
cd "$ROOT"
docker compose up -d
sleep 3

echo "==> Setting up backend..."
cd "$ROOT/backend"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env 2>/dev/null || true
alembic upgrade head
python seed.py

echo "==> Setting up frontend..."
cd "$ROOT/frontend"
npm install
cp -n .env.example .env 2>/dev/null || true

echo ""
echo "Setup complete!"
echo "Run backend:  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "Run frontend: cd frontend && npm run dev"
echo ""
echo "Admin login:    OIADMIN20220001 / Admin@123"
echo "Employee login: OIJODO20220001 / Employee@123"
