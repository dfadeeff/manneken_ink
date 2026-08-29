"use client";

import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import Mascot from "@/components/Mascot";
import PromptBox from "@/components/PromptBox";
import TopBar from "@/components/TopBar";
import { useApi } from "@/lib/api";
import { getActiveSession, takeDraft } from "@/lib/handoff";

interface Bubble {
  role: "user" | "assistant";
  content: string;
}

export default function Tutor() {
  const { isLoaded, isSignedIn } = useAuth();
  const api = useApi();
  const router = useRouter();

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [thinking, setThinking] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);
  const started = useRef(false);

  const send = useCallback(
    async (session: string, text: string) => {
      setBubbles((prev) => [...prev, { role: "user", content: text }, { role: "assistant", content: "" }]);
      setThinking(true);
      try {
        await api.streamReply(session, text, (delta) => {
          setThinking(false);
          setBubbles((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              role: "assistant",
              content: next[next.length - 1].content + delta,
            };
            return next;
          });
        });
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
    [api],
  );

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

    void (async () => {
      const history = await api.messages(session);
      setBubbles(history.map((m) => ({ role: m.role, content: m.content })));
      const draft = takeDraft();
      if (draft) await send(session, draft);
    })();
  }, [isLoaded, isSignedIn, api, router, send]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [bubbles, thinking]);

  return (
    <div className="flex min-h-dvh flex-col">
      <TopBar />

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
              <div key={index} className="flex gap-3">
                <Mascot size={26} className="mt-1 shrink-0" />
                <p className="reading whitespace-pre-wrap pt-0.5">{bubble.content}</p>
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
          />
        </div>
      </main>
    </div>
  );
}
