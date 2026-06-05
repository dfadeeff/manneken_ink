import os
import json

from fastapi import APIRouter
from openai import OpenAI
from pydantic import BaseModel, Field

from .session import session, MOODS
from .prompts import ttt_move_prompt

router = APIRouter(prefix="/api/ttt")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class StartRequest(BaseModel):
    board_size: int = Field(default=3, ge=3, le=9)


class MoveRequest(BaseModel):
    position: int
    gender: str = "boy"
    mood: str = "happy"
    board_size: int = Field(default=3, ge=3, le=9)


def check_winner(board: list[str], n: int) -> str | None:
    for r in range(n):
        line = [r * n + c for c in range(n)]
        if board[line[0]] and all(board[line[0]] == board[i] for i in line):
            return board[line[0]]
    for c in range(n):
        line = [r * n + c for r in range(n)]
        if board[line[0]] and all(board[line[0]] == board[i] for i in line):
            return board[line[0]]
    diag1 = [i * n + i for i in range(n)]
    if board[diag1[0]] and all(board[diag1[0]] == board[i] for i in diag1):
        return board[diag1[0]]
    diag2 = [i * n + (n - 1 - i) for i in range(n)]
    if board[diag2[0]] and all(board[diag2[0]] == board[i] for i in diag2):
        return board[diag2[0]]
    if all(cell != "" for cell in board):
        return "draw"
    return None


@router.post("/start")
async def start_game(req: StartRequest = StartRequest()):
    session.reset_ttt(req.board_size)
    return {"board": session.ttt_board, "active": True, "board_size": session.ttt_board_size}


@router.post("/move")
async def player_move(req: MoveRequest):
    session.gender = req.gender
    session.mood = req.mood
    n = session.ttt_board_size
    total = n * n

    if not session.ttt_active:
        return {"error": "No active game", "board": session.ttt_board}

    if req.position < 0 or req.position >= total or session.ttt_board[req.position] != "":
        return {"error": "Invalid move", "board": session.ttt_board}

    session.ttt_board[req.position] = session.ttt_player_symbol

    winner = check_winner(session.ttt_board, n)
    if winner:
        session.ttt_active = False
        return {
            "board": session.ttt_board,
            "winner": winner,
            "active": False,
            "comment": "Tolles Spiel!" if winner == "draw" else "Du hast gewonnen! Super!",
            "mood": "excited" if winner == session.ttt_player_symbol else "happy",
        }

    prompt = ttt_move_prompt(req.gender, req.mood, session.ttt_board, session.ttt_manneken_symbol, n)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.choices[0].message.content.strip()
    try:
        for line in raw.split("\n"):
            line = line.strip()
            if line.startswith("{"):
                data = json.loads(line)
                break
        else:
            data = json.loads(raw)
    except (json.JSONDecodeError, UnboundLocalError):
        empty = [i for i, c in enumerate(session.ttt_board) if c == ""]
        data = {"move": empty[0] if empty else 0, "comment": "My turn!", "mood": req.mood}

    move = data.get("move", 0)
    if not (0 <= move < total) or session.ttt_board[move] != "":
        empty = [i for i, c in enumerate(session.ttt_board) if c == ""]
        move = empty[0] if empty else 0

    session.ttt_board[move] = session.ttt_manneken_symbol
    new_mood = data.get("mood", req.mood)
    if new_mood not in MOODS:
        new_mood = req.mood
    session.mood = new_mood

    winner = check_winner(session.ttt_board, n)
    if winner:
        session.ttt_active = False

    comment = data.get("comment", "My turn!")
    session.add_message("assistant", comment)

    return {
        "board": session.ttt_board,
        "manneken_move": move,
        "comment": comment,
        "mood": new_mood,
        "winner": winner,
        "active": session.ttt_active,
    }


@router.get("/state")
async def get_state():
    return {
        "board": session.ttt_board,
        "board_size": session.ttt_board_size,
        "active": session.ttt_active,
        "winner": check_winner(session.ttt_board, session.ttt_board_size),
    }
