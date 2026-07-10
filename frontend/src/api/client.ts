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

export type User = {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AuthSession = {
  access_token: string;
  token_type: "bearer";
  user: User;
};

export type Course = {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  teacher: string | null;
  semester: string | null;
  created_at: string;
  updated_at: string;
};

type HealthData = {
  status: string;
  service: string;
};

type RegisterPayload = {
  email: string;
  username: string;
  password: string;
  full_name?: string;
};

type LoginPayload = {
  email: string;
  password: string;
};

type ProfileUpdatePayload = {
  username?: string;
  full_name?: string;
};

export type CoursePayload = {
  name: string;
  description?: string | null;
  teacher?: string | null;
  semester?: string | null;
};

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

let accessToken: string | null = null;

export function setApiAccessToken(token: string | null) {
  accessToken = token;
}

export async function getHealth(): Promise<ApiResponse<HealthData>> {
  return apiFetch<HealthData>("/api/v1/healthz", { auth: false });
}

export async function register(payload: RegisterPayload): Promise<AuthSession> {
  const response = await apiFetch<AuthSession>("/api/v1/auth/register", {
    auth: false,
    body: payload,
    method: "POST"
  });
  return response.data;
}

export async function login(payload: LoginPayload): Promise<AuthSession> {
  const response = await apiFetch<AuthSession>("/api/v1/auth/login", {
    auth: false,
    body: payload,
    method: "POST"
  });
  return response.data;
}

export async function logout(): Promise<void> {
  await apiFetch<{ message: string }>("/api/v1/auth/logout", { method: "POST" });
}

export async function getCurrentUser(): Promise<User> {
  const response = await apiFetch<User>("/api/v1/auth/me");
  return response.data;
}

export async function updateProfile(payload: ProfileUpdatePayload): Promise<User> {
  const response = await apiFetch<User>("/api/v1/users/me", {
    body: payload,
    method: "PATCH"
  });
  return response.data;
}

export async function listCourses(keyword?: string): Promise<Course[]> {
  const searchParams = new URLSearchParams();
  if (keyword?.trim()) {
    searchParams.set("keyword", keyword.trim());
  }
  const queryString = searchParams.toString();
  const response = await apiFetch<Course[]>(`/api/v1/courses${queryString ? `?${queryString}` : ""}`);
  return response.data;
}

export async function createCourse(payload: CoursePayload): Promise<Course> {
  const response = await apiFetch<Course>("/api/v1/courses", {
    body: payload,
    method: "POST"
  });
  return response.data;
}

export async function updateCourse(courseId: string, payload: CoursePayload): Promise<Course> {
  const response = await apiFetch<Course>(`/api/v1/courses/${courseId}`, {
    body: payload,
    method: "PATCH"
  });
  return response.data;
}

export async function deleteCourse(courseId: string): Promise<void> {
  await apiFetch<{ message: string }>(`/api/v1/courses/${courseId}`, { method: "DELETE" });
}

async function apiFetch<T>(
  path: string,
  options: {
    auth?: boolean;
    body?: unknown;
    method?: string;
  } = {}
): Promise<ApiResponse<T>> {
  const headers: HeadersInit = {
    Accept: "application/json"
  };

  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  if (options.auth !== false && accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const response = await fetch(path, {
    method: options.method ?? "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body)
  });

  const payload = (await response.json()) as ApiResponse<T>;

  if (!response.ok) {
    throw new ApiError(
      payload.error?.message ?? "请求失败",
      payload.error?.code ?? `HTTP_${response.status}`,
      response.status
    );
  }

  return payload;
}
