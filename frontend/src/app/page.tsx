"use client";

import { useAuth, useClerk } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import Mascot from "@/components/Mascot";
import PromptBox from "@/components/PromptBox";
import TopBar from "@/components/TopBar";
import { useApi } from "@/lib/api";
import { parkDraft, setActiveLearner, setActiveSession, takeDraft } from "@/lib/handoff";
import type { Learner } from "@/lib/types";

export default function Home() {
  const { isLoaded, isSignedIn } = useAuth();
  const { openSignIn } = useClerk();
  const api = useApi();
  const router = useRouter();

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [choice, setChoice] = useState<{ text: string; learners: Learner[] } | null>(null);
  const replayed = useRef(false);

  const begin = useCallback(
    async (learner: Learner, text: string) => {
      const session = await api.createSession({ learner_id: learner.id });
      setActiveSession(session.id);
      setActiveLearner(learner.id);
      parkDraft(text);
      router.push("/tutor");
    },
    [api, router],
  );

  const start = useCallback(
    async (text: string) => {
      setBusy(true);
      setError(null);
      try {
        const learners = await api.listLearners();
        if (learners.length === 0) {
          parkDraft(text);
          router.push("/setup");
        } else if (learners.length === 1) {
          await begin(learners[0], text);
        } else {
          setChoice({ text, learners });
          setBusy(false);
        }
      } catch {
        setError("Der Lernbegleiter ist gerade nicht erreichbar. Versuch es gleich nochmal.");
        setBusy(false);
      }
    },
    [api, begin, router],
  );

  // Coming back from the sign-in modal: pick the parked prompt up where it was left.
  useEffect(() => {
    if (!isLoaded || !isSignedIn || replayed.current) return;
    const draft = takeDraft();
    if (!draft) return;
    replayed.current = true;
    void start(draft);
  }, [isLoaded, isSignedIn, start]);

  function handleSubmit(text: string) {
    if (!isSignedIn) {
      // The gate: the prompt is kept, then sign-in is asked for.
      parkDraft(text);
      openSignIn();
      return;
    }
    void start(text);
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <TopBar />

      <main className="flex flex-1 flex-col items-center justify-center px-5 pb-24">
        <div className="w-full max-w-[640px]">
          <div className="mb-8 flex flex-col items-center text-center">
            <Mascot size={48} thinking={busy} />
            <h1 className="mt-5 font-display text-[2rem] leading-tight tracking-tight sm:text-[2.5rem]">
              Hallo, ich bin Mika
            </h1>
            <p className="mt-2 text-sm text-muted">
              Wir üben zusammen — Schritt für Schritt, in deinem Tempo.
            </p>
          </div>

          {choice ? (
            <div className="rise rounded-[22px] border border-line bg-surface p-5 shadow-lift">
              <p className="mb-4 text-sm text-muted">Wer übt gerade?</p>
              <div className="flex flex-wrap gap-2">
                {choice.learners.map((learner) => (
                  <button
                    key={learner.id}
                    onClick={() => {
                      setBusy(true);
                      void begin(learner, choice.text);
                    }}
                    className="rounded-full border border-line px-4 py-2 text-sm transition-colors hover:border-accent hover:bg-accent-soft"
                  >
                    {learner.name}
                    <span className="ml-2 text-muted">{learner.school_class}. Klasse</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <PromptBox onSubmit={handleSubmit} disabled={busy} autoFocus />
          )}

          {error && <p className="mt-4 text-center text-sm text-muted">{error}</p>}
        </div>
      </main>
    </div>
  );
}
