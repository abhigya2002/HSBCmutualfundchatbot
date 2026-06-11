import { Radio, ShieldCheck, Wallet } from "lucide-react";

export default function Navbar() {
  return (
    <header className="fixed top-0 z-50 flex h-20 w-full items-center justify-between gap-4 border-b border-border bg-surface/90 px-4 backdrop-blur-xl sm:px-6 lg:px-8">
      <div className="flex min-w-0 flex-1 items-center gap-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-border bg-surface">
          <Wallet className="h-5 w-5 text-blue-300" strokeWidth={2} aria-hidden />
        </div>
        <div className="min-w-0">
          <h1 className="truncate text-lg font-bold leading-tight text-white sm:text-xl">
            HSBC Mutual Fund Assistant
          </h1>
          <div className="mt-1 flex items-center gap-2">
            <span className="h-2 w-2 shrink-0 rounded-full bg-emerald-400 animate-pulse-dot" />
            <p className="truncate text-xs text-muted sm:text-sm">
              Live • Facts-only. No investment advice.
            </p>
          </div>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-3 sm:gap-6">
        <div className="hidden items-center gap-3 border-r border-border pr-6 lg:flex">
          <div className="flex flex-col items-end">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-muted">
              Data Stream
            </span>
            <span className="text-sm font-medium text-emerald-400">Active Connection</span>
          </div>
          <Radio className="h-5 w-5 text-muted" strokeWidth={2} aria-hidden />
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-1.5">
          <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-400" strokeWidth={2} aria-hidden />
          <span className="hidden text-[10px] font-semibold uppercase tracking-wider text-muted sm:inline">
            Verified Accuracy
          </span>
        </div>
      </div>
    </header>
  );
}
