export interface User {
  id: string | number;
  name: string;
  email: string;
  role?: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface RegulatorySource {
  document_name?: string;
  doc_title?: string;
  doc_filename?: string;
  page_start?: number;
  page_end?: number;
  section?: string;
  section_title?: string;
  similarity?: number;
  content?: string;
}

export interface Finding {
  requirement: string;
  status: 'COMPLIANT' | 'SATISFIED' | 'PARTIALLY_COMPLIANT' | 'POTENTIALLY_NON_COMPLIANT' | 'NEEDS_ATTENTION' | 'NON_COMPLIANT' | 'MISSING_EVIDENCE' | 'NEEDS_REVIEW' | 'INSUFFICIENT_INFORMATION' | string;
  explanation: string;
  evidence_found?: string[];
  evidence_missing?: string[];
  recommended_actions?: string[];
  regulatory_sources?: RegulatorySource[];
}

export interface ComplianceReport {
  id?: string | number;
  product_name?: string;
  compliance_area?: string;
  overall_status: string;
  summary: string;
  disclaimer?: string;
  created_at?: string;
  findings?: Finding[];
  retrieved_sources?: RegulatorySource[];
  question?: string;
  facility_description?: string;
}

export interface AuditItem {
  id: string | number;
  product_name?: string;
  question?: string;
  compliance_area: string;
  overall_status: string;
  summary: string;
  created_at: string;
  user_id?: string | number;
}

export interface AuditPagination {
  total: number;
  limit: number;
  offset: number;
}

export interface AuditListResponse {
  data: AuditItem[];
  pagination: AuditPagination;
}

export interface SearchResultItem {
  doc_title?: string;
  doc_filename?: string;
  page_start?: number;
  page_end?: number;
  section_title?: string;
  similarity: number;
  content: string;
}

export type NavView = 'Dashboard' | 'Upload Document' | 'Compliance Reports' | 'Search Regulations';
