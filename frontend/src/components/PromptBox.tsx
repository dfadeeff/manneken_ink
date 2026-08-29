"use client";

import { useEffect, useRef, useState } from "react";

interface PromptBoxProps {
  onSubmit: (text: string) => void;
  placeholder?: string;
  disabled?: boolean;
  autoFocus?: boolean;
  initialValue?: string;
}

export default function PromptBox({
  onSubmit,
  placeholder = "Was möchtest du üben?",
  disabled = false,
  autoFocus = false,
  initialValue = "",
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
      <div className="flex items-center justify-between px-4 pb-3 pt-1">
        <span className="pl-1 text-xs text-muted">Mathe und Deutsch, Klasse 2–4</span>
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
  );
}
