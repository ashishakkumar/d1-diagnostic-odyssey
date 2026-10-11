/* Generated from contracts/openapi.json. Do not edit by hand. */

export interface ApprovalRequest {
  decision: "approve" | "reject";
  draft_id: string;
  seen_hash: string;
}

export interface DemoCaseOut {
  blurb: string;
  case_id: string;
  slug: string;
  title: string;
}

export interface DemoListOut {
  cases: DemoCaseOut[];
}

export interface DemoLoadedOut {
  case_id: string;
  slug: string;
}

export interface HTTPValidationError {
  detail?: ValidationError[];
}

export interface PopulationPriorOut {
  allele_frequency?: number | null;
  experimental: boolean;
  found: boolean;
  label: string;
  limits: string;
  opted_in: boolean;
  population?: string | null;
  source?: string | null;
  track: string;
  variant?: string | null;
  version?: string | null;
}

export interface ReliabilityPoint {
  observed: number;
  predicted: number;
}

export interface Report {
  abstain_reason?: "many_within_factor" | "top_flips_between_bounds" | "tied_for_first" | "no_scoreable_disease" | null;
  abstained: boolean;
  evidence: TermEvidence[];
  leading_orphanet_id?: string | null;
  margin: number | null;
  margin_reason?: "runner_up_ratio_is_zero" | null;
  probability?: number | null;
  reliability_curve?: ReliabilityPoint[] | null;
}

export interface SessionBody {
  name: string;
}

export interface TermDraftBody {
  hpo_id: string;
  label: string;
  presence: string;
}

export interface TermEvidence {
  hpo_id: string;
  lower_ratio?: number | null;
  orphanet_id?: string | null;
  relation: "supports" | "does_not_support";
  source: string;
  upper_ratio?: number | null;
  version: string;
}

export interface ValidationError {
  ctx?: Record<string, unknown>;
  input?: unknown;
  loc: string | number[];
  msg: string;
  type: string;
}

export interface VariantBody {
  gene_symbol: string;
  lab_words: string;
  report_date: string;
  variant: string;
}
