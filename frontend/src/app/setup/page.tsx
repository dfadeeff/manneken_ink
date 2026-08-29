"use client";

import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import { useApi } from "@/lib/api";
import { setActiveLearner, setActiveSession } from "@/lib/handoff";

const CLASSES = [2, 3, 4];

export default function Setup() {
  const { isLoaded, isSignedIn } = useAuth();
  const api = useApi();
  const router = useRouter();

  const [name, setName] = useState("");
  const [schoolClass, setSchoolClass] = useState(3);
  const [language, setLanguage] = useState<"de" | "en">("de");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isLoaded && !isSignedIn) router.replace("/");
  }, [isLoaded, isSignedIn, router]);

  async function save() {
    if (!name.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const learner = await api.createLearner({
        name: name.trim(),
        school_class: schoolClass,
        language,
        avatar: "fox",
      });
      const session = await api.createSession({ learner_id: learner.id });
      setActiveSession(session.id);
      setActiveLearner(learner.id);
      router.push("/tutor");
    } catch {
      setError("Das hat nicht geklappt. Bitte noch einmal versuchen.");
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <TopBar />

      <main className="flex flex-1 items-center justify-center px-5 pb-24">
        <div className="w-full max-w-[440px]">
          <h1 className="font-display text-[1.75rem] leading-tight tracking-tight">
            Wer wird üben?
          </h1>
          <p className="mt-2 text-sm text-muted">
            Nur der Vorname. Mika fragt nie nach Nachname, Adresse oder Schule.
          </p>

          <div className="mt-7 space-y-6 rounded-[22px] border border-line bg-surface p-6 shadow-lift">
            <label className="block">
              <span className="text-sm text-muted">Vorname</span>
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
                onKeyDown={(event) => event.key === "Enter" && save()}
                maxLength={60}
                autoFocus
                placeholder="Lena"
                className="mt-2 w-full rounded-xl border border-line bg-transparent px-3 py-2.5 outline-none transition-colors focus:border-accent"
              />
            </label>

            <fieldset>
              <legend className="text-sm text-muted">Klasse</legend>
              <div className="mt-2 flex gap-2">
                {CLASSES.map((value) => (
                  <button
                    key={value}
                    onClick={() => setSchoolClass(value)}
                    aria-pressed={schoolClass === value}
                    className={`flex-1 rounded-xl border py-2.5 text-sm transition-colors ${
                      schoolClass === value
                        ? "border-accent bg-accent-soft text-ink"
                        : "border-line text-muted hover:border-line-strong"
                    }`}
                  >
                    {value}.
                  </button>
                ))}
              </div>
            </fieldset>

            <fieldset>
              <legend className="text-sm text-muted">Sprache</legend>
              <div className="mt-2 flex gap-2">
                {([["de", "Deutsch"], ["en", "English"]] as const).map(([code, label]) => (
                  <button
                    key={code}
                    onClick={() => setLanguage(code)}
                    aria-pressed={language === code}
                    className={`flex-1 rounded-xl border py-2.5 text-sm transition-colors ${
                      language === code
                        ? "border-accent bg-accent-soft text-ink"
                        : "border-line text-muted hover:border-line-strong"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </fieldset>

            <button
              onClick={save}
              disabled={!name.trim() || busy}
              className="w-full rounded-xl bg-accent py-3 text-sm font-medium text-accent-ink transition-opacity disabled:opacity-30"
            >
              {busy ? "Einen Moment…" : "Los geht’s"}
            </button>

            {error && <p className="text-sm text-muted">{error}</p>}
          </div>
        </div>
      </main>
    </div>
  );
}
