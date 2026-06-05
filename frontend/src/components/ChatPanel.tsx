"use client";

import { useState, useRef } from "react";
import { useManneken } from "./MannekenContext";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPanel() {
  const { gender, mood, setMood, setIsTalking } = useManneken();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  async function sendMessage(text: string) {
    if (!text.trim()) return;
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, gender, mood }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
      if (data.mood) setMood(data.mood);
      await speakText(data.reply, data.mood || mood);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Oops, I can't talk right now! Try again?" },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  }

  async function speakText(text: string, currentMood: string) {
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
      audio.onended = () => { setIsTalking(false); URL.revokeObjectURL(url); };
      await audio.play();
    } catch {
      setIsTalking(false);
    }
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("file", blob, "recording.webm");
        try {
          const res = await fetch(`${API}/api/stt`, { method: "POST", body: formData });
          const data = await res.json();
          if (data.text) await sendMessage(data.text);
        } catch { /* ignore */ }
      };
      mediaRecorder.start();
      setRecording(true);
    } catch { /* mic denied */ }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-3 space-y-2 min-h-0">
        {messages.length === 0 && (
          <p className="text-center text-gray-400 text-sm mt-8">Say hi to Manneken!</p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[80%] px-3 py-2 rounded-2xl text-sm ${
              m.role === "user"
                ? "ml-auto bg-blue-500 text-white rounded-br-sm"
                : "mr-auto bg-white text-gray-800 rounded-bl-sm shadow-sm"
            }`}
          >
            {m.content}
          </div>
        ))}
        {loading && (
          <div className="mr-auto bg-white text-gray-400 px-3 py-2 rounded-2xl rounded-bl-sm shadow-sm text-sm">
            thinking...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-amber-200 p-2 flex gap-2">
        <button
          onClick={recording ? stopRecording : startRecording}
          className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-lg transition-colors ${
            recording ? "bg-red-500 text-white animate-pulse" : "bg-gray-100 hover:bg-gray-200 text-gray-600"
          }`}
        >
          🎤
        </button>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !loading && sendMessage(input)}
          placeholder="Type a message..."
          className="flex-1 px-3 py-2 rounded-full bg-white border border-amber-200 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
          disabled={loading}
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={loading || !input.trim()}
          className="shrink-0 w-10 h-10 rounded-full bg-amber-400 hover:bg-amber-500 text-white flex items-center justify-center text-lg disabled:opacity-40 transition-colors"
        >
          ➤
        </button>
      </div>
    </div>
  );
}