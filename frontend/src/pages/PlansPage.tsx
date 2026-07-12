import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  Clock,
  ListChecks,
  Plus
} from "lucide-react";

import {
  ApiError,
  Course,
  MultiCoursePlanAnalysis,
  StudyPlan,
  StudyPlanItem,
  StudyPlanPage,
  TaskPreview,
  TaskPreviewItem,
  analyzeMultiCoursePlan,
  createStudyPlan,
  createPlanTasks,
  listCourses,
  listStudyPlans,
  previewPlanTasks,
  updateStudyPlanItem
} from "../api/client";

type PlanView = "list" | "calendar";

export function PlansPage() {
  const queryClient = useQueryClient();
  const [selectedCourseIds, setSelectedCourseIds] = useState<string[]>([]);
  const [goal, setGoal] = useState("");
  const [deadline, setDeadline] = useState(defaultDeadlineValue());
  const [dailyMinutes, setDailyMinutes] = useState(120);
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [view, setView] = useState<PlanView>("list");
  const [formError, setFormError] = useState<string | null>(null);
  const [multiCourseAnalysis, setMultiCourseAnalysis] = useState<MultiCoursePlanAnalysis | null>(null);

  const coursesQuery = useQuery({
    queryKey: ["courses", "plans"],
    queryFn: () => listCourses(),
    retry: 1
  });
  const plansQuery = useQuery({
    queryKey: ["study-plans"],
    queryFn: () => listStudyPlans(),
    retry: 1
  });

  const courses = coursesQuery.data ?? [];
  const plans = plansQuery.data?.items ?? [];
  const courseMap = useMemo(() => buildCourseMap(courses), [courses]);
  const selectedPlan = plans.find((plan) => plan.id === selectedPlanId) ?? plans[0] ?? null;

  useEffect(() => {
    if (selectedCourseIds.length === 0 && courses.length > 0) {
      setSelectedCourseIds([courses[0].id]);
    }
  }, [courses, selectedCourseIds.length]);

  useEffect(() => {
    if (!selectedPlanId && plans.length > 0) {
      setSelectedPlanId(plans[0].id);
    }
  }, [plans, selectedPlanId]);

  const createMutation = useMutation({
    mutationFn: () =>
      createStudyPlan({
        course_ids: selectedCourseIds,
        goal,
        deadline: new Date(deadline).toISOString(),
        daily_minutes: dailyMinutes
      }),
    onSuccess: (plan) => {
      setSelectedPlanId(plan.id);
      setGoal("");
      setFormError(null);
      queryClient.setQueryData<StudyPlanPage>(["study-plans"], (current) => ({
        ...(current ?? { total: 0, page: 1, page_size: 20 }),
        items: [plan, ...(current?.items ?? [])],
        total: (current?.total ?? 0) + 1
      }));
      queryClient.invalidateQueries({ queryKey: ["study-plans"] });
    }
  });

  const itemMutation = useMutation({
    mutationFn: ({ plan, item }: { plan: StudyPlan; item: StudyPlanItem }) =>
      updateStudyPlanItem(plan.id, item.id, item.status === "DONE" ? "TODO" : "DONE"),
    onSuccess: (plan) => {
      queryClient.setQueryData<StudyPlanPage>(["study-plans"], (current) => ({
        ...(current ?? { total: 0, page: 1, page_size: 20 }),
        items: (current?.items ?? plans).map((existing) =>
          existing.id === plan.id ? plan : existing
        )
      }));
    }
  });

  const analysisMutation = useMutation({
    mutationFn: () =>
      analyzeMultiCoursePlan({
        course_ids: selectedCourseIds,
        deadline: new Date(deadline).toISOString(),
        daily_minutes: dailyMinutes
      }),
    onSuccess: (analysis) => {
      setMultiCourseAnalysis(analysis);
      setFormError(null);
    },
    onError: (caughtError) => {
      const message =
        caughtError instanceof ApiError ? caughtError.message : "多课程分析失败，请稍后重试";
      setFormError(message);
    }
  });

  function toggleCourse(courseId: string) {
    setSelectedCourseIds((current) => {
      if (current.includes(courseId)) {
        return current.filter((id) => id !== courseId);
      }
      return [...current, courseId];
    });
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedCourseIds.length === 0 || !goal.trim()) {
      return;
    }
    setFormError(null);
    try {
      await createMutation.mutateAsync();
    } catch (caughtError) {
      const message =
        caughtError instanceof ApiError ? caughtError.message : "学习计划生成失败，请稍后重试";
      setFormError(message);
    }
  }

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">阶段八学习计划</p>
          <h2>学习计划</h2>
        </div>
      </header>

      <section className="plans-layout">
        <aside className="panel plan-builder">
          <div className="panel-header">
            <div>
              <p className="eyebrow">生成计划</p>
              <h3>目标与时间</h3>
            </div>
            <Plus size={20} />
          </div>
          {coursesQuery.isLoading ? (
            <p className="materials-hint plan-hint">课程加载中</p>
          ) : courses.length === 0 ? (
            <p className="materials-hint plan-hint">先创建课程后再生成学习计划。</p>
          ) : (
            <form className="form plan-form" onSubmit={handleCreate}>
              <label>
                <span>课程</span>
                <div className="course-check-list">
                  {courses.map((course) => (
                    <label className="check-row" key={course.id}>
                      <input
                        type="checkbox"
                        checked={selectedCourseIds.includes(course.id)}
                        onChange={() => toggleCourse(course.id)}
                      />
                      <span>{course.name}</span>
                    </label>
                  ))}
                </div>
              </label>
              <label>
                <span>学习目标</span>
                <textarea
                  value={goal}
                  maxLength={2000}
                  placeholder="例如：两周内复习完高数期末重点"
                  onChange={(event) => setGoal(event.target.value)}
                />
              </label>
              <label>
                <span>截止时间</span>
                <input
                  type="datetime-local"
                  value={deadline}
                  onChange={(event) => setDeadline(event.target.value)}
                />
              </label>
              <label>
                <span>每日可用时间</span>
                <input
                  type="number"
                  min={15}
                  max={720}
                  step={15}
                  value={dailyMinutes}
                  onChange={(event) => setDailyMinutes(Number(event.target.value))}
                />
              </label>
              {formError && <p className="form-error">{formError}</p>}
              <button
                className="primary-button"
                type="submit"
                disabled={
                  createMutation.isPending || selectedCourseIds.length === 0 || !goal.trim()
                }
              >
                <CalendarDays size={18} />
                生成计划
              </button>
              <button
                className="secondary-button"
                type="button"
                disabled={analysisMutation.isPending || selectedCourseIds.length === 0}
                onClick={() => analysisMutation.mutate()}
              >
                分析多课程
              </button>
              {multiCourseAnalysis && <MultiCourseAnalysisPanel analysis={multiCourseAnalysis} />}
            </form>
          )}
        </aside>

        <section className="plans-main">
          <div className="plan-tabs panel">
            {plansQuery.isLoading ? (
              <p className="materials-hint">计划加载中</p>
            ) : plans.length === 0 ? (
              <p className="materials-hint">还没有学习计划。</p>
            ) : (
              plans.map((plan) => (
                <button
                  className={plan.id === selectedPlan?.id ? "active" : ""}
                  key={plan.id}
                  type="button"
                  onClick={() => setSelectedPlanId(plan.id)}
                >
                  <ListChecks size={16} />
                  <span>{plan.goal}</span>
                </button>
              ))
            )}
          </div>

          {selectedPlan ? (
            <PlanDetail
              courseMap={courseMap}
              isUpdating={itemMutation.isPending}
              plan={selectedPlan}
              view={view}
              onToggleItem={(item) => itemMutation.mutate({ plan: selectedPlan, item })}
              onViewChange={setView}
            />
          ) : (
            <section className="panel empty-state">
              <CalendarDays size={34} />
              <h3>生成第一个计划</h3>
              <p>输入目标、截止时间和每日可用时间后，系统会生成结构化每日安排。</p>
            </section>
          )}
        </section>
      </section>
    </>
  );
}

function MultiCourseAnalysisPanel({ analysis }: { analysis: MultiCoursePlanAnalysis }) {
  return (
    <section className="multi-analysis">
      <div>
        <strong>综合安排</strong>
        <span>
          任务估时 {analysis.total_task_minutes} 分钟 / 可用 {analysis.available_minutes} 分钟
        </span>
      </div>
      {analysis.risk_message && <p>{analysis.risk_message}</p>}
      <div className="allocation-list">
        {analysis.course_stats.map((item) => (
          <article key={item.course_id}>
            <span>{item.course_name}</span>
            <div>
              <i style={{ width: `${Math.max(6, item.allocation_ratio * 100)}%` }} />
            </div>
            <em>{Math.round(item.allocation_ratio * 100)}%</em>
          </article>
        ))}
      </div>
    </section>
  );
}

function PlanDetail({
  courseMap,
  isUpdating,
  plan,
  view,
  onToggleItem,
  onViewChange
}: {
  courseMap: Map<string, Course>;
  isUpdating: boolean;
  plan: StudyPlan;
  view: PlanView;
  onToggleItem: (item: StudyPlanItem) => void;
  onViewChange: (view: PlanView) => void;
}) {
  const groupedItems = groupItemsByDate(plan.items);
  const completedCount = plan.items.filter((item) => item.status === "DONE").length;
  const progress = plan.items.length === 0 ? 0 : Math.round((completedCount / plan.items.length) * 100);
  const [taskPreview, setTaskPreview] = useState<TaskPreview | null>(null);
  const [taskMessage, setTaskMessage] = useState<string | null>(null);

  useEffect(() => {
    setTaskPreview(null);
    setTaskMessage(null);
  }, [plan.id]);

  const previewMutation = useMutation({
    mutationFn: (planItemIds?: string[]) => previewPlanTasks(plan.id, planItemIds),
    onSuccess: (preview) => {
      setTaskPreview(preview);
      setTaskMessage(null);
    },
    onError: (caughtError) => {
      const message =
        caughtError instanceof ApiError ? caughtError.message : "任务预览生成失败，请稍后重试";
      setTaskMessage(message);
    }
  });

  const createTasksMutation = useMutation({
    mutationFn: () => {
      const planItemIds = taskPreview?.items
        .filter((item) => !item.already_added)
        .map((item) => item.source_id);
      return createPlanTasks(plan.id, planItemIds);
    },
    onSuccess: (tasks) => {
      setTaskMessage(tasks.length > 0 ? `已加入 ${tasks.length} 个待办` : "这些任务已经在待办中");
      setTaskPreview((current) =>
        current
          ? {
              ...current,
              already_added_count: current.items.length,
              items: current.items.map((item) => ({ ...item, already_added: true }))
            }
          : current
      );
    },
    onError: (caughtError) => {
      const message =
        caughtError instanceof ApiError ? caughtError.message : "加入待办失败，请稍后重试";
      setTaskMessage(message);
    }
  });

  const hasPreviewItemsToAdd = taskPreview?.items.some((item) => !item.already_added) ?? false;

  return (
    <section className="panel plan-detail">
      <div className="plan-detail-header">
        <div>
          <p className="eyebrow">当前计划</p>
          <h3>{plan.goal}</h3>
          <p>
            截止 {formatDateTime(plan.deadline)} · 每日 {plan.daily_minutes} 分钟 · {progress}%
          </p>
        </div>
        <div className="plan-detail-actions">
          <button
            className="secondary-button"
            type="button"
            disabled={previewMutation.isPending || plan.items.length === 0}
            onClick={() => previewMutation.mutate(undefined)}
          >
            <ClipboardList size={17} />
            预览任务
          </button>
          <div className="segmented" role="group" aria-label="计划视图">
            <button className={view === "list" ? "active" : ""} type="button" onClick={() => onViewChange("list")}>
              列表
            </button>
            <button className={view === "calendar" ? "active" : ""} type="button" onClick={() => onViewChange("calendar")}>
              日历
            </button>
          </div>
        </div>
      </div>

      {plan.risk_message && (
        <div className={`plan-risk ${plan.risk_level.toLowerCase()}`}>
          <AlertTriangle size={18} />
          <span>{plan.risk_message}</span>
        </div>
      )}

      {(taskPreview || taskMessage || previewMutation.isPending) && (
        <TaskPreviewPanel
          courseMap={courseMap}
          isCreating={createTasksMutation.isPending}
          isLoading={previewMutation.isPending}
          message={taskMessage}
          preview={taskPreview}
          canCreate={hasPreviewItemsToAdd}
          onCreate={() => createTasksMutation.mutate()}
        />
      )}

      {view === "list" ? (
        <div className="plan-item-list">
          {plan.items.map((item) => (
            <PlanItemRow
              courseName={courseMap.get(item.course_id)?.name ?? "课程"}
              disabled={isUpdating}
              item={item}
              key={item.id}
              onToggle={() => onToggleItem(item)}
              onPreviewTask={() => previewMutation.mutate([item.id])}
            />
          ))}
        </div>
      ) : (
        <div className="plan-calendar">
          {groupedItems.map(([date, items]) => (
            <section className="plan-day" key={date}>
              <header>
                <strong>{formatDate(date)}</strong>
                <span>{items.reduce((sum, item) => sum + item.estimated_minutes, 0)} 分钟</span>
              </header>
              {items.map((item) => (
                <PlanItemRow
                  compact
                  courseName={courseMap.get(item.course_id)?.name ?? "课程"}
                  disabled={isUpdating}
                  item={item}
                  key={item.id}
                  onToggle={() => onToggleItem(item)}
                  onPreviewTask={() => previewMutation.mutate([item.id])}
                />
              ))}
            </section>
          ))}
        </div>
      )}
    </section>
  );
}

function PlanItemRow({
  compact = false,
  courseName,
  disabled,
  item,
  onPreviewTask,
  onToggle
}: {
  compact?: boolean;
  courseName: string;
  disabled: boolean;
  item: StudyPlanItem;
  onPreviewTask: () => void;
  onToggle: () => void;
}) {
  const done = item.status === "DONE";
  return (
    <article className={`plan-item ${done ? "done" : ""} ${compact ? "compact" : ""}`}>
      <button className="icon-button light" type="button" onClick={onToggle} disabled={disabled}>
        <CheckCircle2 size={18} />
      </button>
      <div>
        <strong>{item.title}</strong>
        <p>{item.description}</p>
        <span>
          {courseName} · {formatDate(item.scheduled_date)}
        </span>
      </div>
      <button
        className="icon-button light"
        type="button"
        title="从此计划项生成任务"
        onClick={onPreviewTask}
      >
        <ClipboardList size={17} />
      </button>
      <time>
        <Clock size={15} />
        {item.estimated_minutes} 分钟
      </time>
    </article>
  );
}

function TaskPreviewPanel({
  canCreate,
  courseMap,
  isCreating,
  isLoading,
  message,
  preview,
  onCreate
}: {
  canCreate: boolean;
  courseMap: Map<string, Course>;
  isCreating: boolean;
  isLoading: boolean;
  message: string | null;
  preview: TaskPreview | null;
  onCreate: () => void;
}) {
  return (
    <section className="task-preview">
      <header>
        <div>
          <p className="eyebrow">任务预览</p>
          <h4>{isLoading ? "正在生成待办" : `${preview?.items.length ?? 0} 个待办任务`}</h4>
        </div>
        <button
          className="primary-button"
          type="button"
          disabled={isLoading || isCreating || !canCreate}
          onClick={onCreate}
        >
          <ClipboardList size={17} />
          加入待办
        </button>
      </header>
      {preview?.risk_message && (
        <div className={`plan-risk ${preview.risk_level.toLowerCase()}`}>
          <AlertTriangle size={18} />
          <span>{preview.risk_message}</span>
        </div>
      )}
      {message && <p className="task-message">{message}</p>}
      {preview && (
        <div className="task-preview-list">
          {preview.items.map((item) => (
            <TaskPreviewRow
              courseName={courseMap.get(item.course_id)?.name ?? "课程"}
              item={item}
              key={item.source_id}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function TaskPreviewRow({ courseName, item }: { courseName: string; item: TaskPreviewItem }) {
  return (
    <article className={`task-preview-item ${item.already_added ? "added" : ""}`}>
      <div>
        <strong>{item.title}</strong>
        <p>{item.description}</p>
        <span>
          {courseName} · {formatDate(item.due_date)} · {priorityLabel(item.priority)}
        </span>
        {item.risk_message && <em>{item.risk_message}</em>}
      </div>
      <time>
        <Clock size={15} />
        {item.estimated_minutes} 分钟
      </time>
    </article>
  );
}

function buildCourseMap(courses: Course[]) {
  return new Map(courses.map((course) => [course.id, course]));
}

function groupItemsByDate(items: StudyPlanItem[]) {
  const groups = new Map<string, StudyPlanItem[]>();
  for (const item of items) {
    const date = item.scheduled_date;
    groups.set(date, [...(groups.get(date) ?? []), item]);
  }
  return [...groups.entries()];
}

function defaultDeadlineValue() {
  const deadline = new Date();
  deadline.setDate(deadline.getDate() + 14);
  deadline.setHours(20, 0, 0, 0);
  return toDateTimeLocal(deadline);
}

function toDateTimeLocal(date: Date) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "short",
    day: "numeric",
    weekday: "short"
  }).format(new Date(value));
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function priorityLabel(priority: TaskPreviewItem["priority"]) {
  const labels: Record<TaskPreviewItem["priority"], string> = {
    LOW: "低优先级",
    MEDIUM: "中优先级",
    HIGH: "高优先级"
  };
  return labels[priority] ?? priority;
}
