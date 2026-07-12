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
  is_admin: boolean;
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

export type MaterialStatus = "UPLOADED" | "PARSING" | "PARSED" | "INDEXING" | "READY" | "FAILED";

export type Material = {
  id: string;
  user_id: string;
  course_id: string;
  title: string;
  material_type: string;
  original_filename: string;
  content_type: string | null;
  file_size: number;
  status: MaterialStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type SearchMode = "keyword" | "vector" | "hybrid";

export type SearchResult = {
  chunk_id: string;
  material_id: string;
  material_title: string;
  material_type: string;
  text: string;
  score: number;
  keyword_score: number;
  vector_score: number;
  page_no: number | null;
  slide_no: number | null;
  section_title: string | null;
};

export type AnswerCitation = {
  id: string;
  answer_message_id: string;
  material_id: string;
  chunk_id: string;
  material_title: string;
  material_type: string;
  section_title: string | null;
  page_no: number | null;
  slide_no: number | null;
  quote: string;
  score: number;
  sort_order: number;
  created_at: string;
};

export type ChatSession = {
  id: string;
  user_id: string;
  course_id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ChatMessageRole = "USER" | "ASSISTANT";

export type ChatMessage = {
  id: string;
  session_id: string;
  user_id: string;
  course_id: string;
  role: ChatMessageRole;
  content: string;
  token_count: number;
  created_at: string;
  citations: AnswerCitation[];
};

export type ChatSessionDetail = {
  session: ChatSession;
  messages: ChatMessage[];
};

export type ChatAskPayload = {
  course_id: string;
  question: string;
  session_id?: string | null;
  material_type?: string | null;
  search_mode?: SearchMode;
};

export type ChatAskResponse = {
  session: ChatSession;
  question: ChatMessage;
  answer: ChatMessage;
  contexts: SearchResult[];
};

export type StudyPlanStatus = "ACTIVE" | "COMPLETED" | "ARCHIVED";
export type StudyPlanItemStatus = "TODO" | "DONE" | "SKIPPED";

export type StudyPlanItem = {
  id: string;
  plan_id: string;
  user_id: string;
  course_id: string;
  title: string;
  description: string | null;
  scheduled_date: string;
  estimated_minutes: number;
  status: StudyPlanItemStatus;
  sort_order: number;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type StudyPlan = {
  id: string;
  user_id: string;
  goal: string;
  course_ids: string[];
  deadline: string;
  daily_minutes: number;
  status: StudyPlanStatus;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | string;
  risk_message: string | null;
  created_at: string;
  updated_at: string;
  items: StudyPlanItem[];
};

export type StudyPlanPage = {
  items: StudyPlan[];
  total: number;
  page: number;
  page_size: number;
};

export type StudyPlanCreatePayload = {
  course_ids: string[];
  goal: string;
  deadline: string;
  daily_minutes: number;
};

export type TaskStatus = "TODO" | "IN_PROGRESS" | "DONE" | "CANCELED";
export type TaskPriority = "LOW" | "MEDIUM" | "HIGH";

export type Task = {
  id: string;
  user_id: string;
  course_id: string;
  plan_id: string | null;
  source_id: string | null;
  title: string;
  description: string | null;
  due_date: string;
  estimated_minutes: number;
  priority: TaskPriority;
  status: TaskStatus;
  completed_at: string | null;
  canceled_at: string | null;
  created_at: string;
  updated_at: string;
};

export type TaskPage = {
  items: Task[];
  total: number;
  page: number;
  page_size: number;
};

export type TaskCreatePayload = {
  course_id: string;
  title: string;
  description?: string | null;
  due_date: string;
  estimated_minutes: number;
  priority: TaskPriority;
};

export type TaskUpdatePayload = Partial<TaskCreatePayload> & {
  status?: TaskStatus;
};

export type TaskPreviewItem = {
  source_id: string;
  plan_id: string;
  course_id: string;
  title: string;
  description: string | null;
  due_date: string;
  estimated_minutes: number;
  priority: TaskPriority;
  risk_message: string | null;
  already_added: boolean;
};

export type TaskPreview = {
  items: TaskPreviewItem[];
  risk_level: "LOW" | "MEDIUM" | "HIGH" | string;
  risk_message: string | null;
  total_estimated_minutes: number;
  already_added_count: number;
};

export type KnowledgePoint = {
  title: string;
  detail: string;
  source_count: number;
};

export type CourseSummary = {
  id: string;
  user_id: string;
  course_id: string;
  material_id: string | null;
  scope: string;
  version: number;
  title: string;
  outline_md: string;
  knowledge_points: KnowledgePoint[];
  status: string;
  created_at: string;
  updated_at: string;
};

export type CourseSummaryPage = {
  items: CourseSummary[];
  total: number;
};

export type DashboardSummary = {
  course_count: number;
  material_count: number;
  ready_material_count: number;
  ready_material_ratio: number;
  today_tasks: Array<{
    id: string;
    course_id: string;
    title: string;
    due_date: string;
    priority: TaskPriority | string;
    status: TaskStatus | string;
  }>;
  recent_chats: Array<{
    id: string;
    course_id: string;
    title: string;
    updated_at: string;
  }>;
  recent_plans: Array<{
    id: string;
    goal: string;
    deadline: string;
    risk_level: string;
    status: string;
  }>;
};

export type CoursePlanningStat = {
  course_id: string;
  course_name: string;
  task_count: number;
  total_estimated_minutes: number;
  earliest_due_date: string | null;
  high_priority_count: number;
  ready_material_count: number;
  urgency_score: number;
  allocation_minutes: number;
  allocation_ratio: number;
};

export type MultiCoursePlanAnalysis = {
  course_stats: CoursePlanningStat[];
  total_task_minutes: number;
  available_minutes: number;
  risk_level: string;
  risk_message: string | null;
  suggested_goal: string;
};

export type AdminSystemStatus = {
  users: number;
  courses: number;
  materials: number;
  failed_materials: number;
  tasks: number;
  plans: number;
  generated_at: string;
};

export type AdminQueueStatus = {
  queue_name: string;
  retry_queue_name: string;
  pending_count: number | null;
  retry_count: number | null;
  available: boolean;
  error: string | null;
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

export async function getReadyz(): Promise<ApiResponse<unknown>> {
  return apiFetch<unknown>("/api/v1/readyz", { auth: false });
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

export async function listMaterials(courseId: string): Promise<Material[]> {
  const response = await apiFetch<Material[]>(`/api/v1/courses/${courseId}/materials`);
  return response.data;
}

export async function getMaterial(materialId: string): Promise<Material> {
  const response = await apiFetch<Material>(`/api/v1/materials/${materialId}`);
  return response.data;
}

export async function deleteMaterial(materialId: string): Promise<void> {
  await apiFetch<{ message: string }>(`/api/v1/materials/${materialId}`, { method: "DELETE" });
}

export async function uploadMaterial(
  courseId: string,
  payload: {
    file: File;
    title?: string;
    material_type?: string;
    onProgress?: (progress: number) => void;
  }
): Promise<Material> {
  const formData = new FormData();
  formData.append("file", payload.file);
  if (payload.title?.trim()) {
    formData.append("title", payload.title.trim());
  }
  if (payload.material_type?.trim()) {
    formData.append("material_type", payload.material_type.trim());
  }

  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("POST", `/api/v1/courses/${courseId}/materials`);
    request.setRequestHeader("Accept", "application/json");
    if (accessToken) {
      request.setRequestHeader("Authorization", `Bearer ${accessToken}`);
    }

    request.upload.onprogress = (event) => {
      if (event.lengthComputable && payload.onProgress) {
        payload.onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    request.onload = () => {
      const response = JSON.parse(request.responseText || "{}") as ApiResponse<Material>;
      if (request.status < 200 || request.status >= 300) {
        reject(
          new ApiError(
            response.error?.message ?? "资料上传失败",
            response.error?.code ?? `HTTP_${request.status}`,
            request.status
          )
        );
        return;
      }
      resolve(response.data);
    };

    request.onerror = () => {
      reject(new ApiError("网络连接失败，资料未上传", "API_NETWORK_ERROR", 0));
    };

    request.send(formData);
  });
}

export async function searchCourseMaterials(
  courseId: string,
  payload: { q: string; material_type?: string; mode?: SearchMode; limit?: number }
): Promise<SearchResult[]> {
  const searchParams = new URLSearchParams();
  searchParams.set("q", payload.q);
  if (payload.material_type?.trim()) {
    searchParams.set("material_type", payload.material_type.trim());
  }
  if (payload.mode) {
    searchParams.set("mode", payload.mode);
  }
  if (payload.limit) {
    searchParams.set("limit", String(payload.limit));
  }
  const response = await apiFetch<SearchResult[]>(
    `/api/v1/courses/${courseId}/search?${searchParams.toString()}`
  );
  return response.data;
}

export async function listChatSessions(courseId?: string): Promise<ChatSession[]> {
  const searchParams = new URLSearchParams();
  if (courseId) {
    searchParams.set("course_id", courseId);
  }
  const queryString = searchParams.toString();
  const response = await apiFetch<ChatSession[]>(
    `/api/v1/chat/sessions${queryString ? `?${queryString}` : ""}`
  );
  return response.data;
}

export async function getChatSession(sessionId: string): Promise<ChatSessionDetail> {
  const response = await apiFetch<ChatSessionDetail>(`/api/v1/chat/sessions/${sessionId}`);
  return response.data;
}

export async function askAgent(payload: ChatAskPayload): Promise<ChatAskResponse> {
  const response = await apiFetch<ChatAskResponse>("/api/v1/chat/ask", {
    body: payload,
    method: "POST"
  });
  return response.data;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await apiFetch<DashboardSummary>("/api/v1/dashboard/summary");
  return response.data;
}

export async function listCourseSummaries(courseId?: string): Promise<CourseSummaryPage> {
  const searchParams = new URLSearchParams();
  if (courseId) {
    searchParams.set("course_id", courseId);
  }
  const queryString = searchParams.toString();
  const response = await apiFetch<CourseSummaryPage>(
    `/api/v1/summaries${queryString ? `?${queryString}` : ""}`
  );
  return response.data;
}

export async function generateCourseSummary(
  courseId: string,
  materialId?: string | null
): Promise<CourseSummary> {
  const response = await apiFetch<CourseSummary>(`/api/v1/courses/${courseId}/summaries`, {
    body: { material_id: materialId ?? null, regenerate: true },
    method: "POST"
  });
  return response.data;
}

export async function analyzeMultiCoursePlan(payload: {
  course_ids: string[];
  deadline?: string | null;
  daily_minutes: number;
}): Promise<MultiCoursePlanAnalysis> {
  const response = await apiFetch<MultiCoursePlanAnalysis>("/api/v1/plans/multi-course/analyze", {
    body: payload,
    method: "POST"
  });
  return response.data;
}

export async function getAdminStatus(): Promise<AdminSystemStatus> {
  const response = await apiFetch<AdminSystemStatus>("/api/v1/admin/status");
  return response.data;
}

export async function getAdminQueueStatus(): Promise<AdminQueueStatus> {
  const response = await apiFetch<AdminQueueStatus>("/api/v1/admin/queues");
  return response.data;
}

export async function createStudyPlan(payload: StudyPlanCreatePayload): Promise<StudyPlan> {
  const response = await apiFetch<StudyPlan>("/api/v1/plans", {
    body: payload,
    method: "POST"
  });
  return response.data;
}

export async function listStudyPlans(): Promise<StudyPlanPage> {
  const response = await apiFetch<StudyPlanPage>("/api/v1/plans");
  return response.data;
}

export async function getStudyPlan(planId: string): Promise<StudyPlan> {
  const response = await apiFetch<StudyPlan>(`/api/v1/plans/${planId}`);
  return response.data;
}

export async function updateStudyPlanItem(
  planId: string,
  itemId: string,
  status: StudyPlanItemStatus
): Promise<StudyPlan> {
  const response = await apiFetch<StudyPlan>(`/api/v1/plans/${planId}/items/${itemId}`, {
    body: { status },
    method: "PATCH"
  });
  return response.data;
}

export async function previewPlanTasks(
  planId: string,
  planItemIds?: string[]
): Promise<TaskPreview> {
  const response = await apiFetch<TaskPreview>(`/api/v1/plans/${planId}/tasks/preview`, {
    body: { plan_item_ids: planItemIds },
    method: "POST"
  });
  return response.data;
}

export async function createPlanTasks(planId: string, planItemIds?: string[]): Promise<Task[]> {
  const response = await apiFetch<Task[]>(`/api/v1/plans/${planId}/tasks`, {
    body: { plan_item_ids: planItemIds },
    method: "POST"
  });
  return response.data;
}

export async function createTask(payload: TaskCreatePayload): Promise<Task> {
  const response = await apiFetch<Task>("/api/v1/tasks", {
    body: payload,
    method: "POST"
  });
  return response.data;
}

export async function listTasks(filters: {
  course_id?: string;
  status?: TaskStatus | "";
  due_from?: string;
  due_to?: string;
  page?: number;
  page_size?: number;
} = {}): Promise<TaskPage> {
  const searchParams = new URLSearchParams();
  if (filters.course_id) {
    searchParams.set("course_id", filters.course_id);
  }
  if (filters.status) {
    searchParams.set("status", filters.status);
  }
  if (filters.due_from) {
    searchParams.set("due_from", filters.due_from);
  }
  if (filters.due_to) {
    searchParams.set("due_to", filters.due_to);
  }
  if (filters.page) {
    searchParams.set("page", String(filters.page));
  }
  if (filters.page_size) {
    searchParams.set("page_size", String(filters.page_size));
  }
  const queryString = searchParams.toString();
  const response = await apiFetch<TaskPage>(`/api/v1/tasks${queryString ? `?${queryString}` : ""}`);
  return response.data;
}

export async function updateTask(taskId: string, payload: TaskUpdatePayload): Promise<Task> {
  const response = await apiFetch<Task>(`/api/v1/tasks/${taskId}`, {
    body: payload,
    method: "PATCH"
  });
  return response.data;
}

export async function completeTask(taskId: string): Promise<Task> {
  const response = await apiFetch<Task>(`/api/v1/tasks/${taskId}/complete`, { method: "POST" });
  return response.data;
}

export async function cancelTask(taskId: string): Promise<Task> {
  const response = await apiFetch<Task>(`/api/v1/tasks/${taskId}/cancel`, { method: "POST" });
  return response.data;
}

export async function postponeTask(taskId: string, dueDate: string): Promise<Task> {
  const response = await apiFetch<Task>(`/api/v1/tasks/${taskId}/postpone`, {
    body: { due_date: dueDate },
    method: "POST"
  });
  return response.data;
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
