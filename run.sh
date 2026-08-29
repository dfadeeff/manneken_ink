#!/bin/bash
set -e

echo "=================================="
echo "  Mika - Lernbegleiter (dev)"
echo "=================================="

if [ ! -f backend/.env ]; then
  echo ""
  echo "ERROR: backend/.env not found. Start from the template:"
  echo "  cp backend/.env.example backend/.env"
  echo ""
  exit 1
fi

if [ ! -f frontend/.env.local ]; then
  echo ""
  echo "ERROR: frontend/.env.local not found. Start from the template:"
  echo "  cp frontend/.env.local.example frontend/.env.local"
  echo ""
  exit 1
fi

echo ""
echo "[1/4] Python environment..."
cd backend
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt

echo "[2/4] Database migrations..."
alembic upgrade head

echo "[3/4] Backend on http://localhost:8000 ..."
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

echo "[4/4] Frontend on http://localhost:3000 ..."
cd frontend
[ -d node_modules ] || npm install
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=================================="
echo "  Open http://localhost:3000"
echo "  Ctrl+C stops both"
echo "=================================="

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
