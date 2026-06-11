export default function TypingIndicator() {
  return (
    <div className="mt-6 inline-flex max-w-fit animate-fade-in items-center gap-4 rounded-xl glass-card px-6 py-4">
      <div className="flex gap-1.5">
        <div className="typing-dot bg-accent" />
        <div className="typing-dot bg-accent" />
        <div className="typing-dot bg-accent" />
      </div>
      <span className="text-xs font-semibold uppercase tracking-widest text-muted">
        Querying Official Sources
      </span>
    </div>
  );
}
