export const S2P_CATEGORIES = [
  "price_variance",
  "quantity_mismatch",
  "duplicate_risk",
  "contract_gap",
  "format_compliance"
] as const;

export const S2P_ACTIONS = [
  "auto_approve",
  "hold_for_review",
  "escalate_to_buyer",
  "flag_leakage",
  "refer_to_specialist"
] as const;

export const S2P_FACTORS = [
  "match_status",
  "amount_variance_ratio",
  "duplicate_score",
  "supplier_exception_history",
  "payment_terms_impact",
  "commodity_index_correlation",
  "tax_regulatory_compliance"
] as const;

export type S2PCategory = (typeof S2P_CATEGORIES)[number];
export type S2PAction = (typeof S2P_ACTIONS)[number];
export type S2PFactor = (typeof S2P_FACTORS)[number];

export type FactorMap = Partial<Record<S2PFactor, number>> & Record<string, number | undefined>;

export interface InvoiceException {
  invoice_id?: string;
  invoiceId?: string;
  supplier?: string;
  supplier_name?: string;
  supplierName?: string;
  amount?: number;
  category?: S2PCategory | string;
  scored_action?: S2PAction | string;
  scoredAction?: S2PAction | string;
  recommended_action?: S2PAction | string;
  recommendedAction?: S2PAction | string;
  confidence?: number;
  factors?: FactorMap;
}

export interface SupplierProfile {
  supplier_id?: string;
  supplierId?: string;
  name: string;
  category?: string;
  exception_rate?: number;
  exceptionRate?: number;
  avg_invoice_amount?: number;
  avgInvoiceAmount?: number;
  payment_terms?: string;
  paymentTerms?: string;
  otif_score?: number;
  otifScore?: number;
  total_invoices?: number;
  totalInvoices?: number;
  total_exceptions?: number;
  totalExceptions?: number;
  recent_trend?: string;
  recentTrend?: string;
}

export interface ConservationStatus {
  engine_version?: string;
  source?: string;
  status?: string;
  auto_approve_rate?: number;
  autoApproveRate?: number;
  accuracy?: number;
  verified_decisions?: number;
  verifiedDecisions?: number;
  penalty_ratio?: number;
  penaltyRatio?: number;
  passed?: boolean;
}

export interface PreviewQueueResponse {
  engine_version?: string;
  exceptions: InvoiceException[];
  total: number;
  auto_approve_rate?: number;
  autoApproveRate?: number;
  confidence_avg?: number;
  confidenceAvg?: number;
}

export interface PreviewSuppliersResponse {
  engine_version?: string;
  suppliers: SupplierProfile[];
  total: number;
}

export interface ExceptionQueueResponse {
  exceptions: InvoiceException[];
  total: number;
}
