"use client";

import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import Mascot from "@/components/Mascot";
import PromptBox from "@/components/PromptBox";
import TopBar from "@/components/TopBar";
import { useApi } from "@/lib/api";
import { getActiveLearner, getActiveSession, takeDraft } from "@/lib/handoff";
import { useRecorder } from "@/lib/useRecorder";

interface Bubble {
  role: "user" | "assistant";
  content: string;
  messageId?: string | null;
}

const VOICE_PREF = "mika:voice";

export default function Tutor() {
  const { isLoaded, isSignedIn } = useAuth();
  const api = useApi();
  const router = useRouter();

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [learnerId, setLearnerId] = useState<string | null>(null);
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [thinking, setThinking] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [voiceOn, setVoiceOn] = useState(false);
  const [canSpeak, setCanSpeak] = useState(false);

  const bottom = useRef<HTMLDivElement>(null);
  const started = useRef(false);
  const audio = useRef<HTMLAudioElement | null>(null);
  const voiceOnRef = useRef(false);

  useEffect(() => {
    voiceOnRef.current = voiceOn;
  }, [voiceOn]);

  const play = useCallback(
    async (messageId: string) => {
      try {
        const url = await api.speechUrl(messageId);
        audio.current?.pause();
        const player = new Audio(url);
        audio.current = player;
        player.onended = () => URL.revokeObjectURL(url);
        await player.play();
      } catch {
        /* a failed read-aloud must never break the lesson */
      }
    },
    [api],
  );

  const send = useCallback(
    async (session: string, text: string) => {
      setBubbles((prev) => [
        ...prev,
        { role: "user", content: text },
        { role: "assistant", content: "" },
      ]);
      setThinking(true);
      try {
        await api.streamReply(
          session,
          text,
          (delta) => {
            setThinking(false);
            setBubbles((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              next[next.length - 1] = { ...last, content: last.content + delta };
              return next;
            });
          },
          (messageId) => {
            setBubbles((prev) => {
              const next = [...prev];
              next[next.length - 1] = { ...next[next.length - 1], messageId };
              return next;
            });
            if (messageId && voiceOnRef.current) void play(messageId);
          },
        );
      } catch {
        setBubbles((prev) => {
          const next = [...prev];
          next[next.length - 1] = {
            role: "assistant",
            content: "Ups, da ist etwas schiefgegangen. Sag es noch einmal?",
          };
          return next;
        });
      } finally {
        setThinking(false);
      }
    },
    [api, play],
  );

  const onRecorded = useCallback(
    async (blob: Blob) => {
      if (!learnerId || !sessionId) return;
      setTranscribing(true);
      try {
        const text = await api.transcribe(learnerId, blob);
        // Spoken input takes exactly the same path as typed input from here on.
        if (text.trim()) await send(sessionId, text.trim());
      } catch {
        /* ignore - the child can always type */
      } finally {
        setTranscribing(false);
      }
    },
    [api, learnerId, sessionId, send],
  );

  const recorder = useRecorder(onRecorded);

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) {
      router.replace("/");
      return;
    }
    if (started.current) return;
    started.current = true;

    const session = getActiveSession();
    if (!session) {
      router.replace("/");
      return;
    }
    setSessionId(session);
    setVoiceOn(window.localStorage.getItem(VOICE_PREF) === "on");

    void (async () => {
      api.speechStatus().then((s) => setCanSpeak(s.speak && s.transcribe)).catch(() => {});
      api
        .session(session)
        .then((s) => setLearnerId(s.learner_id))
        .catch(() => setLearnerId(getActiveLearner()));
      const history = await api.messages(session);
      setBubbles(history.map((m) => ({ role: m.role, content: m.content, messageId: m.id })));
      const draft = takeDraft();
      if (draft) await send(session, draft);
    })();
  }, [isLoaded, isSignedIn, api, router, send]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [bubbles, thinking]);

  function toggleVoice() {
    const next = !voiceOn;
    setVoiceOn(next);
    window.localStorage.setItem(VOICE_PREF, next ? "on" : "off");
    if (!next) audio.current?.pause();
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <TopBar
        trailing={
          canSpeak && (
            <button
              onClick={toggleVoice}
              aria-pressed={voiceOn}
              title={voiceOn ? "Mika liest vor" : "Mika liest nicht vor"}
              className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm transition-colors ${
                voiceOn
                  ? "border-accent bg-accent-soft text-ink"
                  : "border-line text-muted hover:border-line-strong"
              }`}
            >
              <SpeakerIcon muted={!voiceOn} />
              Vorlesen
            </button>
          )
        }
      />

      <main className="mx-auto flex w-full max-w-[720px] flex-1 flex-col px-5">
        <div className="flex-1 space-y-6 py-6">
          {bubbles.map((bubble, index) =>
            bubble.role === "user" ? (
              <div key={index} className="flex justify-end">
                <p className="reading max-w-[85%] rounded-[18px] rounded-br-[6px] bg-accent-soft px-4 py-2.5">
                  {bubble.content}
                </p>
              </div>
            ) : (
              <div key={index} className="group flex gap-3">
                <Mascot size={26} className="mt-1 shrink-0" />
                <div className="min-w-0">
                  <p className="reading whitespace-pre-wrap pt-0.5">{bubble.content}</p>
                  {canSpeak && bubble.messageId && bubble.content && (
                    <button
                      onClick={() => play(bubble.messageId!)}
                      aria-label="Vorlesen"
                      className="mt-1 text-muted opacity-0 transition-opacity hover:text-ink focus:opacity-100 group-hover:opacity-100"
                    >
                      <SpeakerIcon />
                    </button>
                  )}
                </div>
              </div>
            ),
          )}

          {thinking && (
            <div className="flex gap-3">
              <Mascot size={26} thinking className="mt-1 shrink-0" />
              <p className="reading pt-0.5 text-muted">denkt nach…</p>
            </div>
          )}
          <div ref={bottom} />
        </div>

        <div className="sticky bottom-0 bg-ground pb-6 pt-2">
          <PromptBox
            onSubmit={(text) => sessionId && send(sessionId, text)}
            placeholder="Schreib mir, was du üben möchtest"
            disabled={!sessionId}
            onMicToggle={canSpeak && learnerId ? recorder.toggle : undefined}
            recording={recorder.recording}
            transcribing={transcribing}
          />
          {recorder.denied && (
            <p className="mt-2 text-center text-xs text-muted">
              Ich darf das Mikrofon nicht benutzen. Du kannst mir aber schreiben.
            </p>
          )}
        </div>
      </main>
    </div>
  );
}

function SpeakerIcon({ muted = false }: { muted?: boolean }) {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path
        d="M3 6h2.2L8 3.5v9L5.2 10H3V6Z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
      {muted ? (
        <path d="M11 6.5l3 3m0-3l-3 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      ) : (
        <path
          d="M10.5 6a3 3 0 0 1 0 4M12.5 4.5a5.5 5.5 0 0 1 0 7"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinecap="round"
        />
      )}
    </svg>
  );
}
