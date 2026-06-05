"use client";

import { useState, useCallback } from "react";
import { useManneken } from "./MannekenContext";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Board = string[];
type Winner = string | null;

const BOARD_SIZES = [3, 4, 5, 6, 7, 8, 9];

function cellClasses(boardSize: number): string {
  if (boardSize <= 3) return "w-16 h-16 text-2xl";
  if (boardSize <= 5) return "w-12 h-12 text-xl";
  if (boardSize <= 7) return "w-10 h-10 text-lg";
  return "w-8 h-8 text-base";
}

export default function TicTacToe() {
  const { gender, mood, setMood, setIsTalking } = useManneken();
  const [boardSize, setBoardSize] = useState(3);
  const [board, setBoard] = useState<Board>(Array(9).fill(""));
  const [active, setActive] = useState(false);
  const [winner, setWinner] = useState<Winner>(null);
  const [thinking, setThinking] = useState(false);
  const [comment, setComment] = useState("");

  function changeBoardSize(size: number) {
    setBoardSize(size);
    setBoard(Array(size * size).fill(""));
    setWinner(null);
    setComment("");
  }

  const startGame = useCallback(async (size: number) => {
    const res = await fetch(`${API}/api/ttt/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ board_size: size }),
    });
    const data = await res.json();
    setBoard(data.board);
    setBoardSize(size);
    setActive(true);
    setWinner(null);
    setComment("Lass uns spielen! Du bist zuerst dran 😊");
  }, []);

  async function playMove(position: number) {
    if (!active || thinking || board[position] !== "") return;

    setThinking(true);
    try {
      const res = await fetch(`${API}/api/ttt/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ position, gender, mood, board_size: boardSize }),
      });
      const data = await res.json();

      if (data.error) return;

      setBoard(data.board);
      setActive(data.active);
      setComment(data.comment || "");

      if (data.mood) setMood(data.mood);
      if (data.winner) setWinner(data.winner);

      if (data.comment) {
        speakComment(data.comment, data.mood || mood);
      }
    } finally {
      setThinking(false);
    }
  }

  async function speakComment(text: string, currentMood: string) {
    try {
      setIsTalking(true);
      const res = await fetch(`${API}/api/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, mood: currentMood, gender }),
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => {
        setIsTalking(false);
        URL.revokeObjectURL(url);
      };
      await audio.play();
    } catch {
      setIsTalking(false);
    }
  }

  function statusText() {
    if (winner === "X") return "🎉 Du hast gewonnen!";
    if (winner === "O") return "Manneken gewinnt! 🏆";
    if (winner === "draw") return "Unentschieden! 🤝";
    if (thinking) return "Manneken denkt nach...";
    if (!active) return "Drück Start zum Spielen!";
    return "Du bist dran! Tipp auf ein Feld.";
  }

  const cells = cellClasses(boardSize);

  return (
    <div className="flex flex-col items-center gap-3">
      <h2 className="font-bold text-amber-700">Tic Tac Toe</h2>

      <div className="flex flex-col items-center gap-2">
        <p className="text-xs text-amber-600 font-medium">Board size</p>
        <div className="flex gap-1">
          {BOARD_SIZES.map((size) => (
            <button
              key={size}
              onClick={() => changeBoardSize(size)}
              disabled={active}
              className={`w-8 h-8 rounded-lg text-sm font-bold transition-all ${
                boardSize === size
                  ? "bg-amber-400 text-white shadow-sm"
                  : "bg-white border border-amber-200 text-amber-700 hover:bg-amber-100"
              } disabled:opacity-40 disabled:cursor-default`}
            >
              {size}
            </button>
          ))}
        </div>
        <p className="text-xs text-amber-500">{boardSize}x{boardSize} &mdash; {boardSize} in a row to win</p>
      </div>

      <p className="text-sm text-amber-600 font-medium">{statusText()}</p>

      <div
        className="grid gap-1.5 w-fit"
        style={{ gridTemplateColumns: `repeat(${boardSize}, 1fr)` }}
      >
        {board.map((cell, i) => (
          <button
            key={i}
            onClick={() => playMove(i)}
            disabled={!active || thinking || cell !== ""}
            className={`${cells} rounded-lg font-bold flex items-center justify-center transition-all
              ${cell === ""
                ? "bg-white hover:bg-amber-100 border-2 border-amber-200 cursor-pointer"
                : "border-2 border-amber-300"
              }
              ${cell === "X" ? "bg-blue-100 text-blue-600" : ""}
              ${cell === "O" ? "bg-pink-100 text-pink-600" : ""}
              disabled:cursor-default
            `}
          >
            {cell === "X" && "✕"}
            {cell === "O" && "○"}
          </button>
        ))}
      </div>

      {comment && (
        <div className="bg-white/80 rounded-xl px-4 py-2 text-sm text-gray-700 max-w-[250px] text-center shadow-sm">
          💬 {comment}
        </div>
      )}

      <button
        onClick={() => startGame(boardSize)}
        className="px-6 py-2 rounded-full bg-amber-400 hover:bg-amber-500 text-white font-bold text-sm transition-colors"
      >
        {active || winner ? "🔄 Nochmal" : "▶ Spiel starten"}
      </button>
    </div>
  );
}
