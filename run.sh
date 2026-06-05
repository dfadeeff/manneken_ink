#!/bin/bash
set -e

echo "=============================="
echo "  Manneken - Dress Up & Chat  "
echo "=============================="

# Check for .env
if [ ! -f backend/.env ]; then
  echo ""
  echo "ERROR: backend/.env not found!"
  echo "Create it with your OpenAI API key:"
  echo "  echo 'OPENAI_API_KEY=sk-your-key' > backend/.env"
  echo ""
  exit 1
fi

# Backend setup
echo ""
echo "[1/3] Setting up Python backend..."
cd backend
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

echo ""
echo "[2/3] Starting backend on http://localhost:8000 ..."
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Frontend setup
echo ""
echo "[3/3] Starting frontend on http://localhost:3000 ..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "================================"
echo "  Open http://localhost:3000"
echo "  Press Ctrl+C to stop both"
echo "================================"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait