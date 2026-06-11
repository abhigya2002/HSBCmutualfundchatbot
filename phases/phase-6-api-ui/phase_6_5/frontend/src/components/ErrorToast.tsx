"use client";

import { AlertCircle } from "lucide-react";

interface ErrorToastProps {
  visible: boolean;
}

export default function ErrorToast({ visible }: ErrorToastProps) {
  return (
    <div
      className={`fixed right-4 top-24 z-[60] max-w-sm rounded-xl border border-red-500/50 glass-card p-4 transition-transform duration-300 sm:right-6 ${
        visible ? "translate-x-0" : "translate-x-[120%]"
      }`}
      role="alert"
      aria-live="assertive"
    >
      <div className="flex items-center gap-3 text-red-300">
        <AlertCircle className="h-7 w-7 shrink-0" strokeWidth={2} aria-hidden />
        <div className="flex flex-col">
          <span className="text-base font-bold text-white">Connection Interrupted</span>
          <span className="text-xs font-semibold uppercase tracking-tight text-red-400/80">
            Please check your network
          </span>
        </div>
      </div>
    </div>
  );
}
