"use client";

import { BarChart2 } from "lucide-react";

const SAMPLE_QUESTIONS = [
  "What is the expense ratio of HSBC Small Cap Fund?",
  "What is the exit load of HSBC Midcap Fund?",
  "What is the minimum SIP for HSBC Gilt Fund?",
] as const;

interface WelcomeScreenProps {
  onSelectQuestion: (question: string) => void;
}

export default function WelcomeScreen({ onSelectQuestion }: WelcomeScreenProps) {
  return (
    <section className="flex min-h-[55vh] animate-fade-in flex-col items-center justify-center px-4 py-12 text-center">
      <div className="mb-8 flex h-20 w-20 items-center justify-center rounded-2xl border border-border bg-surface shadow-lg">
        <BarChart2 className="h-10 w-10 text-blue-300" strokeWidth={1.75} aria-hidden />
      </div>

      <div className="mx-auto max-w-[600px] space-y-4">
        <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
          Welcome to HSBC Mutual Fund Assistant
        </h2>
        <p className="text-base leading-relaxed text-muted sm:text-lg">
          Ask any factual question about HSBC Mutual Fund schemes. Get verified, source-backed answers
          instantly.
        </p>
      </div>

      <div className="mt-10 flex max-w-3xl flex-wrap items-center justify-center gap-3">
        {SAMPLE_QUESTIONS.map((question) => (
          <button
            key={question}
            type="button"
            onClick={() => onSelectQuestion(question)}
            className="chip-glow rounded-full border border-border bg-surface px-5 py-2.5 text-left text-sm leading-snug text-muted transition-all duration-200 hover:-translate-y-0.5 hover:border-accent/60 hover:bg-[#22262f] hover:text-white sm:text-[15px]"
          >
            {question}
          </button>
        ))}
      </div>
    </section>
  );
}

export { SAMPLE_QUESTIONS };
