import type {
  ConservationStatus,
  ExceptionQueueResponse,
  PreviewQueueResponse,
  PreviewSuppliersResponse
} from "./types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8002";

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) {
    throw new Error(`GET ${path} failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    throw new Error(`POST ${path} failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getPreviewQueue(): Promise<PreviewQueueResponse> {
  return apiGet<PreviewQueueResponse>("/api/s2p/preview/queue").catch(() => ({
    exceptions: [],
    total: 0,
    auto_approve_rate: 0,
    confidence_avg: 0
  }));
}

export async function getPreviewConservation(): Promise<ConservationStatus | null> {
  return apiGet<ConservationStatus>("/api/s2p/preview/conservation").catch(() => null);
}

export async function getPreviewSuppliers(): Promise<PreviewSuppliersResponse> {
  return apiGet<PreviewSuppliersResponse>("/api/s2p/preview/suppliers").catch(() => ({
    suppliers: [],
    total: 0
  }));
}

export async function getFingerprint(): Promise<unknown | null> {
  return apiGet<unknown>("/api/fingerprint").catch(() => null);
}

export async function getTrajectory(): Promise<unknown | null> {
  return apiGet<unknown>("/api/trajectory").catch(() => null);
}

export async function getConservationStatus(): Promise<ConservationStatus | null> {
  return apiGet<ConservationStatus>("/api/conservation/status").catch(() => null);
}

export async function getExceptionQueue(): Promise<ExceptionQueueResponse> {
  return apiGet<ExceptionQueueResponse>("/api/s2p/queue").catch(() => ({
    exceptions: [],
    total: 0
  }));
}

export async function scoreException(payload: unknown): Promise<unknown | null> {
  return apiPost<unknown>("/api/score", payload).catch(() => null);
}

export async function verifyDecision(payload: unknown): Promise<unknown | null> {
  return apiPost<unknown>("/api/s2p/verify", payload).catch(() => null);
}

export async function getDecisions(): Promise<{ decisions: unknown[]; total: number }> {
  return apiGet<{ decisions: unknown[]; total: number }>("/api/s2p/decisions").catch(() => ({
    decisions: [],
    total: 0
  }));
}

export async function getSupplierProfile(id: string): Promise<unknown | null> {
  return apiGet<unknown>(`/api/s2p/supplier/${encodeURIComponent(id)}/profile`).catch(() => null);
}
