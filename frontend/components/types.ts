export type ExplanationItem = {
  claim: string;
  chunk_id: string;
  quote: string;
};

export type QueryPayload = {
  direct_answer?: string;
  explanation?: ExplanationItem[];
  confidence?: "high" | "medium" | "low" | "insufficient";
  conflicting_sources?: Array<Record<string, unknown>> | null;
  validation_warnings?: string[];
  message?: string;
  error?: string;
};

export type SourceSelection = {
  source: string;
  pageRef: string;
  quote: string;
  chunkId: string;
  pdfUrl?: string | null;
};
