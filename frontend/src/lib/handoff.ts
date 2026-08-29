/**
 * The prompt box is usable before sign-in. Whatever was typed is parked here so
 * that after the Clerk modal (and, first time round, after setting up a child)
 * the child never has to type it a second time.
 */

const DRAFT = "mika:draft";
const SESSION = "mika:session";
const LEARNER = "mika:learner";

function store(): Storage | null {
  return typeof window === "undefined" ? null : window.sessionStorage;
}

export function parkDraft(text: string) {
  store()?.setItem(DRAFT, text);
}

export function takeDraft(): string | null {
  const value = store()?.getItem(DRAFT) ?? null;
  store()?.removeItem(DRAFT);
  return value;
}

export function peekDraft(): string | null {
  return store()?.getItem(DRAFT) ?? null;
}

export function setActiveSession(sessionId: string) {
  store()?.setItem(SESSION, sessionId);
}

export function getActiveSession(): string | null {
  return store()?.getItem(SESSION) ?? null;
}

export function setActiveLearner(learnerId: string) {
  store()?.setItem(LEARNER, learnerId);
}

export function getActiveLearner(): string | null {
  return store()?.getItem(LEARNER) ?? null;
}
