# Manneken

An interactive children's game app featuring a customizable character called Manneken. Kids can dress up the character, play tic-tac-toe against it, and chat with it using voice or text — all powered by AI.

Live at [manneken.ink](https://manneken.ink)

## Features

- **Dress Up** — Pick from hats, tops, bottoms, and shoes to style Manneken (boy or girl)
- **Tic Tac Toe** — Play against Manneken on boards from 3x3 up to 9x9. The AI adapts its play style based on its current mood
- **AI Chat** — Talk to Manneken via text or voice. It responds with text-to-speech and reacts with mood changes that affect its facial expression
- **Mood System** — 8 moods (happy, excited, sad, angry, silly, calm, scared, curious) that change dynamically based on interactions and affect the character's face, voice, and personality
- **Extensible** — New games can be added by creating a page component and adding one entry to the game registry

## Architecture

```
manneken/
  frontend/          Next.js 16 + Tailwind CSS v4
  backend/           Python FastAPI + OpenAI API
```

- **Frontend** (Vercel) — Landing page with game tiles, game pages with the Manneken character and chat panel
- **Backend** (Railway) — AI chat (GPT-4o-mini), text-to-speech, speech-to-text (Whisper), tic-tac-toe AI moves

## Local Development

### Prerequisites

- Node.js 18+
- Python 3.11+
- An [OpenAI API key](https://platform.openai.com/api-keys)

### Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/dfadeeff/manneken_ink.git
   cd manneken_ink
   ```

2. Create the backend env file:
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your OPENAI_API_KEY
   ```

3. Run both servers:
   ```bash
   ./run.sh
   ```

   This starts the backend on `http://localhost:8000` and the frontend on `http://localhost:3000`.

### Running manually

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

### Frontend (Vercel)

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

### Backend (Railway)

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | (required) |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000` |
| `PORT` | Server port | `8000` |

## Adding a New Game

1. Add an entry to `frontend/src/lib/gameRegistry.ts`
2. Create a page at `frontend/src/app/play/<game-id>/page.tsx`
3. (Optional) Add a backend route in `backend/app/routes_<game>.py` and include it in `backend/main.py`

No existing code needs to be modified.

## Tech Stack

- **Frontend:** Next.js 16, React 19, Tailwind CSS v4, TypeScript
- **Backend:** FastAPI, OpenAI API (GPT-4o-mini, Whisper, TTS)
- **Hosting:** Vercel (frontend), Railway (backend)
