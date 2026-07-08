export type ApiResponse<T> = {
  success: boolean;
  data: T;
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  } | null;
  trace_id: string | null;
};

type HealthData = {
  status: string;
  service: string;
};

export async function getHealth(): Promise<ApiResponse<HealthData>> {
  const response = await fetch("/api/v1/healthz");

  if (!response.ok) {
    throw new Error("API health check failed");
  }

  return response.json();
}

