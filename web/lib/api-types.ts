/** Mirrors FastAPI / Pydantic contracts — keep in sync with docs/API.md */

export type SessionState =
  | "created"
  | "questionnaire_complete"
  | "dream_submitted"
  | "awaiting_followups"
  | "ready_to_conclude"
  | "retrieving"
  | "verifying"
  | "drafting"
  | "concluded"
  | "refused"
  | "expired"
  | "purged";

export interface Questionnaire {
  dreamer_state: string;
  dream_time: string;
  repetition: string;
  waking_emotion: string;
  locale_context?: string | null;
  sensitive_flags: string[];
}

export interface FollowUpQuestion {
  slot: string;
  prompt_en: string;
  prompt_ar: string;
}

export interface SessionSnapshot {
  id: string;
  state: SessionState;
  language: string;
  questionnaire: Partial<Questionnaire>;
  accumulated_facts: Record<string, unknown>;
  follow_up_round: number;
  max_follow_up_rounds: number;
  retain: boolean;
  expires_at?: string | null;
  guardrail_flags: string[];
  pending_follow_ups: FollowUpQuestion[];
}

export interface ConfidenceBreakdown {
  evidence_coverage: number;
  source_agreement: number;
  fact_completeness: number;
  tier_quality: number;
  sensitivity_penalty: number;
}

export interface ConclusionPayload {
  classification: {
    ruya: number;
    hulm: number;
    hadith_al_nafs: number;
    label: string;
  };
  adab: { text?: string; citation_ids?: string[] };
  conclusion_md: string;
  claims: { text: string; citation_ids: string[] }[];
  disagreements: { claim_key: string; summary: string; citation_ids: string[] }[];
  confidence: { score: number; breakdown: ConfidenceBreakdown };
  gaps: string[];
  evidence: {
    citation_id?: string | null;
    cite_key?: string | null;
    excerpt: string;
    reliability_tier?: number | null;
    hadith_grade?: string | null;
    author?: string | null;
    source_scope: "curated" | "user";
    pending_scholar_review: boolean;
  }[];
  abstained: boolean;
  guardrail_flags: string[];
}

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";
