"use client";

import Link from "next/link";
import { MannekenProvider, useManneken } from "@/components/MannekenContext";
import Character from "@/components/Character";
import ChatPanel from "@/components/ChatPanel";
import { MOOD_CONFIG } from "@/components/clothingData";
import { ReactNode } from "react";

function PlayContent({ children }: { children: ReactNode }) {
  const { gender, mood, clothes, isTalking, switchGender } = useManneken();
  const moodInfo = MOOD_CONFIG[mood];

  return (
    <main
      className={`flex-1 flex flex-col gap-3 p-4 max-w-6xl mx-auto w-full transition-colors duration-500 ${moodInfo.bg}`}
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="text-amber-500 hover:text-amber-700 transition-colors text-sm font-medium"
          >
            &larr; Games
          </Link>
          <h1 className="text-2xl font-bold text-amber-700">Manneken</h1>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <div
            className={`px-3 py-1 rounded-full text-sm font-medium border-2 ${moodInfo.accent} bg-white/80 transition-all duration-500`}
          >
            {moodInfo.emoji} {moodInfo.label}
          </div>

          <div className="flex rounded-full bg-white/80 border border-amber-200 overflow-hidden">
            <button
              onClick={() => switchGender("boy")}
              className={`px-3 py-1 text-sm font-medium transition-colors ${
                gender === "boy"
                  ? "bg-blue-400 text-white"
                  : "text-gray-500 hover:bg-gray-100"
              }`}
            >
              👦 Boy
            </button>
            <button
              onClick={() => switchGender("girl")}
              className={`px-3 py-1 text-sm font-medium transition-colors ${
                gender === "girl"
                  ? "bg-pink-400 text-white"
                  : "text-gray-500 hover:bg-gray-100"
              }`}
            >
              👧 Girl
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col lg:flex-row gap-4">
        <div className="lg:w-1/3 flex flex-col items-center gap-2">
          <div
            className={`p-4 rounded-2xl border-2 ${moodInfo.accent} bg-white/60 transition-all duration-500 w-full flex justify-center`}
          >
            <Character
              gender={gender}
              clothes={clothes}
              mood={mood}
              isTalking={isTalking}
            />
          </div>
        </div>

        <div className="lg:w-1/3 bg-white/80 rounded-2xl border border-amber-200 p-3 overflow-y-auto max-h-[500px]">
          {children}
        </div>

        <div className="lg:w-1/3 flex flex-col bg-amber-50 rounded-2xl border border-amber-200 shadow-lg min-h-[400px] max-h-[500px]">
          <div className="px-4 py-2 border-b border-amber-200 bg-amber-100 rounded-t-2xl flex items-center justify-between">
            <h2 className="font-bold text-amber-700 text-sm">
              💬 Chat with Manneken
            </h2>
            <span className="text-xs text-amber-500">
              {moodInfo.emoji} feeling {moodInfo.label.toLowerCase()}
            </span>
          </div>
          <ChatPanel />
        </div>
      </div>
    </main>
  );
}

export default function PlayLayout({ children }: { children: ReactNode }) {
  return (
    <MannekenProvider>
      <PlayContent>{children}</PlayContent>
    </MannekenProvider>
  );
}
