export type VerificationStatus = 'VERIFIED' | 'INACCURATE' | 'FALSE' | 'UNVERIFIED';

export interface VerificationSourceCitation {
  source_domain: string;
  url: string;
  title: string;
  publication_date?: string | null;
  evidence_type?: string | null;
  relevance_score?: number | null;
  content_snippet?: string | null;
}

export interface ExtractedClaimItem {
  claim_id: string;
  page_number: number;
  original_claim: string;
  claim_type: string;
  entities: string[];
  numbers: string[];
  dates: string[];
}

export interface ClaimVerificationResult {
  claim_id: string;
  original_claim: string;
  page_number: number;
  claim_type: string;
  status: VerificationStatus;
  confidence: number;
  explanation: string;
  corrected_information?: string | null;
  evidence_summary?: string | null;
  sources: VerificationSourceCitation[];
  verification_notes?: string | null;
}

export interface VerificationReport {
  document_name: string;
  total_pages: number;
  total_claims: number;
  verified_count: number;
  inaccurate_count: number;
  false_count: number;
  unverified_count: number;
  results: ClaimVerificationResult[];
  processed_at?: string;
}

export interface PageExtraction {
  page_number: number;
  text: string;
  character_count: number;
  is_empty: boolean;
}

export interface PDFExtractionResult {
  document_name: string;
  total_pages: number;
  total_characters: number;
  pages: PageExtraction[];
  extraction_status: string;
  is_scanned_document: boolean;
  error_message?: string | null;
}

export interface EvidenceItem {
  source_title: string;
  source_url: string;
  source_domain: string;
  publication_date?: string | null;
  content_snippet: string;
  relevance_score?: number | null;
  query_used: string;
}

export interface ClaimEvidenceResult {
  claim_id: string;
  original_claim: string;
  search_queries: string[];
  evidence: EvidenceItem[];
  search_status: string;
}

export interface ClaimExtractionResponse {
  document_name: string;
  total_claims: number;
  claims: ExtractedClaimItem[];
  extraction_model_used?: string | null;
  error_message?: string | null;
}
