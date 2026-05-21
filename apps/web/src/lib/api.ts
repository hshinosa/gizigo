import { OptimizeRequestZ, OptimizeResponseZ, SensitivityResponseZ, ApiErrorZ } from "./types";
import type { OptimizeRequest, OptimizeResponse, SensitivityResponse, Plan } from "./types";

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://127.0.0.1:8001";

class ApiClientError extends Error {
  errorCode: string;
  requestId: string;
  details: unknown;
  constructor(message: string, errorCode: string, requestId: string, details: unknown) {
    super(message);
    this.errorCode = errorCode;
    this.requestId = requestId;
    this.details = details;
  }
}

async function request<T>(path: string, init: RequestInit, validator: (v: unknown) => T): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, init);
  } catch {
    throw new ApiClientError(
      "Cannot reach the server. Please check your connection.",
      "NETWORK_ERROR",
      "n/a",
      null,
    );
  }
  const text = await response.text();
  let parsed: unknown;
  try {
    parsed = text ? JSON.parse(text) : null;
  } catch {
    throw new ApiClientError(
      "Respons server tidak valid.",
      "PARSE_ERROR",
      response.headers.get("x-request-id") ?? "n/a",
      text,
    );
  }
  if (!response.ok) {
    const errorParsed = ApiErrorZ.safeParse(parsed);
    if (errorParsed.success) {
      throw new ApiClientError(
        errorParsed.data.message,
        errorParsed.data.error_code,
        errorParsed.data.request_id,
        errorParsed.data.details,
      );
    }
    throw new ApiClientError(
      "An error occurred on the server.",
      "UNKNOWN_ERROR",
      response.headers.get("x-request-id") ?? "n/a",
      parsed,
    );
  }
  return validator(parsed);
}

export async function optimize(req: OptimizeRequest): Promise<OptimizeResponse> {
  OptimizeRequestZ.parse(req);
  return request("/v1/optimize", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(req),
  }, (v) => OptimizeResponseZ.parse(v));
}

export async function sensitivity(
  baseRequest: OptimizeRequest,
  perturbations: { ingredient_id: string; delta_pct: number }[],
): Promise<SensitivityResponse> {
  return request("/v1/sensitivity", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ base_request: baseRequest, perturbations }),
  }, (v) => SensitivityResponseZ.parse(v));
}

export async function humanize(plan: Plan, useLlm = false): Promise<{ meals: { meal_slot: string; title: string; description: string }[] }> {
  return request("/v1/humanize", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ plan, use_llm: useLlm }),
  }, (v) => v as { meals: { meal_slot: string; title: string; description: string }[] });
}

export { ApiClientError };
