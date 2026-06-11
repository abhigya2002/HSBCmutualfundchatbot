"use client";

import { ArrowUp } from "lucide-react";
import { FormEvent, useCallback, useRef, useState } from "react";

interface InputBarProps {
  onSubmit: (query: string) => void;
  disabled: boolean;
}

export default function InputBar({ onSubmit, disabled }: InputBarProps) {
  const [value, setValue] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSubmitRef = useRef(0);

  const submitQuery = useCallback(
    (query: string) => {
      const trimmed = query.trim();
      if (!trimmed || disabled) return;

      const now = Date.now();
      if (now - lastSubmitRef.current < 300) return;
      lastSubmitRef.current = now;

      onSubmit(trimmed);
      setValue("");
    },
    [disabled, onSubmit],
  );

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => submitQuery(value), 300);
  }

  return (
    <div className="fixed bottom-0 z-40 w-full bg-gradient-to-t from-background via-background/95 to-transparent px-4 pb-4 pt-6 sm:px-6 sm:pb-6">
      <div className="mx-auto max-w-[1000px]">
        <p className="mb-4 text-center text-xs text-muted sm:text-sm">
          Facts-only. No investment advice. Answers sourced exclusively from official HSBC Groww scheme
          pages.
        </p>

        <form onSubmit={handleSubmit} className="group relative">
          <div className="absolute inset-0 rounded-2xl bg-accent/20 opacity-0 blur-2xl transition-opacity group-focus-within:opacity-30" />
          <div className="relative flex items-center">
            <input
              autoComplete="off"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              disabled={disabled}
              placeholder="Ask a factual question about HSBC Mutual Funds..."
              className="w-full rounded-2xl border border-border bg-background py-4 pl-4 pr-16 text-base text-white shadow-xl transition-all placeholder:text-muted focus:border-accent/60 focus:outline-none focus:ring-2 focus:ring-accent/30 disabled:cursor-not-allowed disabled:opacity-50 sm:py-[18px] sm:pl-4 sm:pr-[4.5rem]"
            />
            <button
              type="submit"
              disabled={disabled || !value.trim()}
              className="absolute right-2 flex h-11 w-11 items-center justify-center rounded-full bg-accent text-white shadow-lg transition-all hover:bg-blue-600 hover:shadow-[0_0_20px_rgba(37,99,235,0.45)] active:scale-95 disabled:cursor-not-allowed disabled:bg-border disabled:opacity-40 disabled:shadow-none sm:right-3 sm:h-12 sm:w-12"
              aria-label="Send message"
            >
              <ArrowUp className="h-5 w-5" strokeWidth={2.5} aria-hidden />
            </button>
          </div>
        </form>

        <footer className="mt-6 flex flex-col items-center justify-between gap-3 opacity-60 md:flex-row">
          <p className="text-center text-xs text-muted md:text-left">
            HSBC Mutual Fund Assistant •{" "}
            <span className="text-emerald-400">Institutional Grade Data Engine</span> • v6.5.0
          </p>
          <div className="flex gap-6 text-[10px] font-semibold uppercase tracking-wider text-muted">
            <span className="cursor-default">Terms</span>
            <span className="cursor-default">Privacy</span>
            <span className="cursor-default">Disclosures</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
