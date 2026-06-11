"use client";

import { AlertTriangle, Copy, Link2, ShieldCheck } from "lucide-react";
import { useState } from "react";
import type { ChatApiResponse } from "@/lib/types";
import { buildCopyText } from "@/lib/api";
import { citationLabelFromUrl, isAllowlistedCitationUrl } from "@/lib/allowlist";

interface ChatBubbleProps {
  role: "user" | "assistant";
  text: string;
  response?: ChatApiResponse;
}

export default function ChatBubble({ role, text, response }: ChatBubbleProps) {
  const [copied, setCopied] = useState(false);

  if (role === "user") {
    return (
      <div className="flex animate-fade-in justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-accent px-4 py-3 text-base text-white shadow-lg sm:max-w-[70%] sm:px-5 sm:py-4">
          {text}
        </div>
      </div>
    );
  }

  if (!response) return null;

  const isRefusal = response.outcome_type === "refusal" || response.outcome_type === "abstention";
  const cardClass = isRefusal ? "glass-card-amber bg-amber-500/5" : "border border-border bg-surface";
  const badgeClass = isRefusal
    ? "border-amber-500/30 bg-amber-500/10 text-amber-500"
    : "border-emerald-500/30 bg-emerald-500/10 text-emerald-400";
  const badgeLabel = isRefusal ? "Disclaimer" : "Facts Only";
  const citationAllowed = isAllowlistedCitationUrl(response.citation_url);
  const citationLabel = citationLabelFromUrl(response.citation_url);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(buildCopyText(response!));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <div className="flex animate-fade-in justify-start">
      <div className={`relative w-full rounded-2xl rounded-tl-sm p-4 shadow-xl sm:p-5 ${cardClass}`}>
        <button
          type="button"
          onClick={handleCopy}
          className="absolute right-3 top-3 inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-blue-300 transition-colors hover:bg-white/5 hover:text-blue-200"
          aria-label="Copy answer"
        >
          <Copy className="h-3.5 w-3.5" strokeWidth={2} aria-hidden />
          <span className="hidden sm:inline">{copied ? "Copied" : "Copy"}</span>
        </button>

        <div className="flex flex-col gap-3 pr-16 sm:flex-row sm:items-center sm:justify-between sm:pr-20">
          <div
            className={`inline-flex w-fit items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${badgeClass}`}
          >
            {isRefusal ? (
              <AlertTriangle className="h-3 w-3" strokeWidth={2} aria-hidden />
            ) : (
              <ShieldCheck className="h-3 w-3" strokeWidth={2} aria-hidden />
            )}
            <span>{badgeLabel}</span>
          </div>
        </div>

        <div className="mt-3 text-base leading-relaxed text-gray-200">{response.answer}</div>

        {response.citation_url && (
          <div className="mt-4 text-sm">
            {citationAllowed ? (
              <a
                href={response.citation_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-blue-300 underline-offset-2 hover:underline"
              >
                <Link2 className="h-4 w-4 shrink-0" strokeWidth={2} aria-hidden />
                <span className="truncate">Source: {citationLabel}</span>
              </a>
            ) : (
              <span className="text-muted">Source: {response.citation_url}</span>
            )}
          </div>
        )}

        <p className="mt-2 text-xs text-muted">Last updated from sources: {response.footer_date}</p>
      </div>
    </div>
  );
}
