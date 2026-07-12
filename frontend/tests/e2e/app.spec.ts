import { expect, Page, test } from "@playwright/test";

const user = {
  id: "user-1",
  email: "admin@example.com",
  username: "admin",
  full_name: "Admin User",
  is_active: true,
  is_admin: true,
  created_at: "2026-07-12T00:00:00Z",
  updated_at: "2026-07-12T00:00:00Z"
};

const courses = [
  {
    id: "course-1",
    user_id: "user-1",
    name: "高等数学",
    description: "期末复习",
    teacher: "Li",
    semester: "2026 Spring",
    created_at: "2026-07-12T00:00:00Z",
    updated_at: "2026-07-12T00:00:00Z"
  },
  {
    id: "course-2",
    user_id: "user-1",
    name: "大学英语",
    description: null,
    teacher: null,
    semester: null,
    created_at: "2026-07-12T00:00:00Z",
    updated_at: "2026-07-12T00:00:00Z"
  }
];

const summary = {
  id: "summary-1",
  user_id: "user-1",
  course_id: "course-1",
  material_id: null,
  scope: "COURSE",
  version: 1,
  title: "高等数学 复习提纲 v1",
  outline_md: "# 高等数学 复习提纲\n\n## 重点知识点\n1. **函数极限**",
  knowledge_points: [
    {
      title: "函数极限",
      detail: "函数极限描述自变量趋近某点时函数值的变化趋势。",
      source_count: 2
    }
  ],
  status: "READY",
  created_at: "2026-07-12T00:00:00Z",
  updated_at: "2026-07-12T00:00:00Z"
};

test.beforeEach(async ({ page }) => {
  await page.addInitScript((sessionUser) => {
    window.localStorage.setItem("course_agent_access_token", "test-token");
    window.localStorage.setItem("course_agent_user", JSON.stringify(sessionUser));
  }, user);
  await mockApi(page);
});

test("dashboard renders aggregate data and quick links", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: /你好/ })).toBeVisible();
  await expect(page.getByText("今日任务")).toBeVisible();
  await expect(page.getByRole("link", { name: "继续对话" })).toBeVisible();
  await expect(page.getByRole("link", { name: "打开学习计划" })).toBeVisible();
});

test("summary page can generate and display knowledge outline", async ({ page }) => {
  await page.goto("/summaries");

  await expect(page.getByRole("heading", { name: "复习提纲" })).toBeVisible();
  await page.getByRole("button", { name: /生成提纲/ }).click();
  await expect(page.getByText("函数极限").first()).toBeVisible();
  await expect(page.locator(".markdown-preview")).toContainText("高等数学 复习提纲");
});

test("plans page shows multi-course allocation analysis", async ({ page }) => {
  await page.goto("/plans");

  await page.getByRole("button", { name: "分析多课程" }).click();
  await expect(page.getByText("综合安排")).toBeVisible();
  await expect(page.getByText("高等数学").first()).toBeVisible();
  await expect(page.getByText("大学英语").first()).toBeVisible();
});

test("admin page shows operations checks for admin user", async ({ page }) => {
  await page.goto("/admin");

  await expect(page.getByRole("heading", { name: "系统状态" })).toBeVisible();
  await expect(page.getByText('"available": true')).toBeVisible();
  await expect(page.getByText('"ready": true')).toBeVisible();
});

async function mockApi(page: Page) {
  await page.route("/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();

    if (path === "/api/v1/healthz") {
      return route.fulfill({ json: ok({ status: "ok", service: "course-agent-backend" }) });
    }
    if (path === "/api/v1/readyz") {
      return route.fulfill({
        json: ok({
          ready: true,
          checks: {
            database: { ok: true },
            redis: { ok: true },
            object_storage_config: { ok: true }
          }
        })
      });
    }
    if (path === "/api/v1/dashboard/summary") {
      return route.fulfill({
        json: ok({
          course_count: 2,
          material_count: 3,
          ready_material_count: 2,
          ready_material_ratio: 0.6667,
          today_tasks: [
            {
              id: "task-1",
              course_id: "course-1",
              title: "完成极限复习",
              due_date: "2026-07-12",
              priority: "HIGH",
              status: "TODO"
            }
          ],
          recent_chats: [
            {
              id: "chat-1",
              course_id: "course-1",
              title: "函数极限是什么",
              updated_at: "2026-07-12T00:00:00Z"
            }
          ],
          recent_plans: [
            {
              id: "plan-1",
              goal: "两周复习高数",
              deadline: "2026-07-26T12:00:00Z",
              risk_level: "LOW",
              status: "ACTIVE"
            }
          ]
        })
      });
    }
    if (path === "/api/v1/courses" && method === "GET") {
      return route.fulfill({ json: ok(courses) });
    }
    if (path === "/api/v1/summaries" && method === "GET") {
      return route.fulfill({ json: ok({ items: [summary], total: 1 }) });
    }
    if (path === "/api/v1/courses/course-1/summaries" && method === "POST") {
      return route.fulfill({ status: 201, json: ok(summary) });
    }
    if (path === "/api/v1/plans" && method === "GET") {
      return route.fulfill({ json: ok({ items: [], total: 0, page: 1, page_size: 20 }) });
    }
    if (path === "/api/v1/plans/multi-course/analyze" && method === "POST") {
      return route.fulfill({
        json: ok({
          course_stats: [
            {
              course_id: "course-1",
              course_name: "高等数学",
              task_count: 3,
              total_estimated_minutes: 240,
              earliest_due_date: "2026-07-12",
              high_priority_count: 2,
              ready_material_count: 2,
              urgency_score: 10,
              allocation_minutes: 420,
              allocation_ratio: 0.7
            },
            {
              course_id: "course-2",
              course_name: "大学英语",
              task_count: 1,
              total_estimated_minutes: 60,
              earliest_due_date: "2026-07-18",
              high_priority_count: 0,
              ready_material_count: 1,
              urgency_score: 4,
              allocation_minutes: 180,
              allocation_ratio: 0.3
            }
          ],
          total_task_minutes: 300,
          available_minutes: 600,
          risk_level: "LOW",
          risk_message: null,
          suggested_goal: "综合规划高等数学、大学英语"
        })
      });
    }
    if (path === "/api/v1/admin/status") {
      return route.fulfill({
        json: ok({
          users: 1,
          courses: 2,
          materials: 3,
          failed_materials: 0,
          tasks: 4,
          plans: 1,
          generated_at: "2026-07-12T00:00:00Z"
        })
      });
    }
    if (path === "/api/v1/admin/queues") {
      return route.fulfill({
        json: ok({
          queue_name: "course_agent:jobs",
          retry_queue_name: "course_agent:jobs:retry",
          pending_count: 0,
          retry_count: 0,
          available: true,
          error: null
        })
      });
    }

    return route.fulfill({ status: 404, json: ok(null) });
  });
}

function ok<T>(data: T) {
  return {
    success: true,
    data,
    error: null,
    trace_id: "test-trace"
  };
}
