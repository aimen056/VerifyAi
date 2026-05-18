/**
 * VerifyAI API Client
 * Handles communication between the Next.js frontend and the FastAPI backend.
 */

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

// ── Types ────────────────────────────────────────────────────
export type Verdict = "TRUE" | "FALSE" | "MISLEADING" | "UNVERIFIED";

export interface SourceReference {
  name: string;
  url: string | null;
  trust_score: number | null;
}

export interface TokenAttribution {
  token: string;
  attribution: number;
}

export interface ExplanationData {
  summary: string;
  tokens: TokenAttribution[];
}

export interface ModelScores {
  scores: Record<string, number>;
}

export interface VerifyResponse {
  id: string;
  verdict: Verdict;
  confidence: number;
  summary: string;
  explanation: ExplanationData;
  model_scores: ModelScores;
  sources: SourceReference[];
  processing_time_ms: number;
  created_at: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  services: Record<string, string>;
}

// ── API Methods ──────────────────────────────────────────────

const TIMEOUT_MS = 120_000; // 2 min — model + SHAP can take time

async function fetchWithTimeout(
  input: RequestInfo,
  init?: RequestInit,
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(input, { ...init, signal: controller.signal });
    return res;
  } finally {
    clearTimeout(timer);
  }
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function verifyText(text: string): Promise<VerifyResponse> {
  const res = await fetchWithTimeout(`${API_BASE}/verify/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(
      res.status === 503
        ? "ML pipeline is still loading — please wait a moment and try again."
        : `Verification failed (${res.status}): ${body}`,
    );
  }
  return res.json();
}

export async function verifyImage(
  file: File,
  description?: string,
): Promise<VerifyResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (description) formData.append("description", description);

  const res = await fetchWithTimeout(`${API_BASE}/verify/image`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(
      res.status === 503
        ? "ML pipeline is still loading — please wait a moment and try again."
        : `Image verification failed (${res.status}): ${body}`,
    );
  }
  return res.json();
}

export async function verifyUrl(url: string): Promise<VerifyResponse> {
  const res = await fetchWithTimeout(`${API_BASE}/verify/url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(
      res.status === 503
        ? "ML pipeline is still loading — please wait a moment and try again."
        : `URL verification failed (${res.status}): ${body}`,
    );
  }
  return res.json();
}
