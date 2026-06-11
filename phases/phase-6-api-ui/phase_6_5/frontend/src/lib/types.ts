export type OutcomeType = "factual" | "refusal" | "abstention";

export interface ChatApiResponse {
  answer: string;
  citation_url: string;
  footer_date: string;
  outcome_type: OutcomeType;
}

export interface AnswerEnvelope {
  outcome_type: OutcomeType;
  display_text: string;
  assistant: {
    body_text: string;
    citation_url: string;
    citation_markdown?: string;
    footer_line?: string;
    footer_date?: string;
    disclaimer_line?: string;
    display_text?: string;
    refusal_type?: string;
    answer_type?: string;
  };
}

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  text: string;
  response?: ChatApiResponse;
}
