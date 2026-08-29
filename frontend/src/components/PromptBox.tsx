"use client";

import { useEffect, useRef, useState } from "react";

interface PromptBoxProps {
  onSubmit: (text: string) => void;
  placeholder?: string;
  disabled?: boolean;
  autoFocus?: boolean;
  initialValue?: string;
  /** Omitted on the signed-out landing page, where there is no learner to bill the mic to. */
  onMicToggle?: () => void;
  recording?: boolean;
  transcribing?: boolean;
}

export default function PromptBox({
  onSubmit,
  placeholder = "Was möchtest du üben?",
  disabled = false,
  autoFocus = false,
  initialValue = "",
  onMicToggle,
  recording = false,
  transcribing = false,
}: PromptBoxProps) {
  const [value, setValue] = useState(initialValue);
  const textarea = useRef<HTMLTextAreaElement>(null);

  // Grow with the text instead of scrolling inside a fixed box.
  useEffect(() => {
    const el = textarea.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  function submit() {
    const text = value.trim();
    if (!text || disabled) return;
    setValue("");
    onSubmit(text);
  }

  const hint = recording
    ? "Ich höre zu … tippe nochmal aufs Mikrofon, wenn du fertig bist"
    : transcribing
      ? "Einen Moment, ich höre nach …"
      : "Mathe und Deutsch, Klasse 2–4";

  return (
    <div className="rounded-[22px] border border-line bg-surface shadow-lift transition-colors focus-within:border-line-strong">
      <textarea
        ref={textarea}
        value={value}
        autoFocus={autoFocus}
        rows={1}
        maxLength={500}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            submit();
          }
        }}
        placeholder={placeholder}
        aria-label={placeholder}
        className="reading w-full resize-none bg-transparent px-5 pt-4 text-ink outline-none placeholder:text-muted"
      />
      <div className="flex items-center justify-between gap-3 px-4 pb-3 pt-1">
        <span className="pl-1 text-xs text-muted">{hint}</span>

        <div className="flex items-center gap-2">
          {onMicToggle && (
            <button
              onClick={onMicToggle}
              disabled={disabled || transcribing}
              aria-label={recording ? "Aufnahme beenden" : "Sprechen statt tippen"}
              aria-pressed={recording}
              className={`flex h-9 w-9 items-center justify-center rounded-full border transition-colors disabled:opacity-30 ${
                recording
                  ? "border-transparent bg-accent text-accent-ink"
                  : "border-line text-muted hover:border-line-strong hover:text-ink"
              }`}
            >
              {recording ? (
                <span className="block h-3 w-3 rounded-[3px] bg-current" />
              ) : (
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                  <rect x="5.5" y="1.5" width="5" height="8" rx="2.5" stroke="currentColor" strokeWidth="1.5" />
                  <path
                    d="M3 7.5a5 5 0 0 0 10 0M8 12.5V15"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  />
                </svg>
              )}
            </button>
          )}

          <button
            onClick={submit}
            disabled={disabled || !value.trim()}
            aria-label="Senden"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-accent-ink transition-opacity disabled:opacity-25"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path
                d="M8 13V3M8 3L3.5 7.5M8 3l4.5 4.5"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
