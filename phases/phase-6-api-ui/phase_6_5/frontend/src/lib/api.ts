import type { AnswerEnvelope, ChatApiResponse, OutcomeType } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

function mapOutcomeType(raw: string): OutcomeType {
  if (raw === "refusal" || raw === "abstention" || raw === "factual") {
    return raw;
  }
  return "factual";
}

export function mapEnvelopeToResponse(envelope: AnswerEnvelope): ChatApiResponse {
  const assistant = envelope.assistant || {};
  const outcome = mapOutcomeType(envelope.outcome_type);
  const answer =
    (assistant.body_text || "").trim() ||
    (envelope.display_text || "").trim() ||
    (assistant.display_text || "").trim();

  let footerDate = (assistant.footer_date || "").trim();
  if (!footerDate && assistant.footer_line) {
    const match = assistant.footer_line.match(/Last updated from sources:\s*(.+)$/i);
    if (match) footerDate = match[1].trim();
  }

  return {
    answer,
    citation_url: (assistant.citation_url || "").trim(),
    footer_date: footerDate || "date unavailable",
    outcome_type: outcome,
  };
}

export async function sendQuery(query: string): Promise<ChatApiResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query.trim() }),
    });
  } catch {
    throw new Error("Could not fetch answer. Please try again.");
  }

  if (!response.ok) {
    throw new Error("Could not fetch answer. Please try again.");
  }

  let data: AnswerEnvelope;
  try {
    data = (await response.json()) as AnswerEnvelope;
  } catch {
    throw new Error("Could not fetch answer. Please try again.");
  }

  return mapEnvelopeToResponse(data);
}

export function buildCopyText(response: ChatApiResponse): string {
  const lines = [response.answer];
  if (response.citation_url) {
    lines.push(`Source: ${response.citation_url}`);
  }
  lines.push(`Last updated from sources: ${response.footer_date}`);
  return lines.join("\n");
}
