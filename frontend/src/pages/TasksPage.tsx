import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  Edit3,
  Plus,
  RotateCcw,
  X
} from "lucide-react";

import {
  ApiError,
  Course,
  Task,
  TaskCreatePayload,
  TaskPage,
  TaskPriority,
  TaskStatus,
  TaskUpdatePayload,
  cancelTask,
  completeTask,
  createTask,
  listCourses,
  listTasks,
  postponeTask,
  updateTask
} from "../api/client";

type TaskFormState = {
  course_id: string;
  title: string;
  description: string;
  due_date: string;
  estimated_minutes: number;
  priority: TaskPriority;
  status: TaskStatus;
};

const defaultFilters = {
  course_id: "",
  status: "" as TaskStatus | "",
  due_from: "",
  due_to: ""
};

const statusLabels: Record<TaskStatus, string> = {
  TODO: "待办",
  IN_PROGRESS: "进行中",
  DONE: "已完成",
  CANCELED: "已取消"
};

const priorityLabels: Record<TaskPriority, string> = {
  LOW: "低",
  MEDIUM: "中",
  HIGH: "高"
};

function emptyForm(courses: Course[]): TaskFormState {
  return {
    course_id: courses[0]?.id ?? "",
    title: "",
    description: "",
    due_date: toDateInput(new Date()),
    estimated_minutes: 45,
    priority: "MEDIUM",
    status: "TODO"
  };
}

function formFromTask(task: Task): TaskFormState {
  return {
    course_id: task.course_id,
    title: task.title,
    description: task.description ?? "",
    due_date: task.due_date,
    estimated_minutes: task.estimated_minutes,
    priority: task.priority,
    status: task.status
  };
}

function toCreatePayload(form: TaskFormState): TaskCreatePayload {
  return {
    course_id: form.course_id,
    title: form.title,
    description: form.description || null,
    due_date: form.due_date,
    estimated_minutes: form.estimated_minutes,
    priority: form.priority
  };
}

function toUpdatePayload(form: TaskFormState): TaskUpdatePayload {
  return {
    ...toCreatePayload(form),
    status: form.status
  };
}

export function TasksPage() {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState(defaultFilters);
  const [formOpen, setFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [form, setForm] = useState<TaskFormState>(() => emptyForm([]));
  const [formError, setFormError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const coursesQuery = useQuery({
    queryKey: ["courses", "tasks"],
    queryFn: () => listCourses(),
    retry: 1
  });

  const tasksQuery = useQuery({
    queryKey: ["tasks", filters],
    queryFn: () => listTasks({ ...filters, page_size: 100 }),
    retry: 1
  });

  const courses = coursesQuery.data ?? [];
  const courseMap = useMemo(() => new Map(courses.map((course) => [course.id, course])), [courses]);
  const tasks = tasksQuery.data?.items ?? [];

  useEffect(() => {
    if (!form.course_id && courses.length > 0 && !editingTask) {
      setForm((current) => ({ ...current, course_id: courses[0].id }));
    }
  }, [courses, editingTask, form.course_id]);

  const createMutation = useMutation({
    mutationFn: createTask,
    onSuccess: (task) => {
      queryClient.setQueryData<TaskPage>(["tasks", filters], (current) => ({
        ...(current ?? { total: 0, page: 1, page_size: 100 }),
        items: [task, ...(current?.items ?? [])],
        total: (current?.total ?? 0) + 1
      }));
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      closeForm();
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: TaskUpdatePayload }) =>
      updateTask(id, payload),
    onSuccess: (task) => {
      patchTask(task);
      closeForm();
    }
  });

  const completeMutation = useMutation({
    mutationFn: completeTask,
    onSuccess: patchTask
  });

  const reopenMutation = useMutation({
    mutationFn: (taskId: string) => updateTask(taskId, { status: "TODO" }),
    onSuccess: patchTask
  });

  const cancelMutation = useMutation({
    mutationFn: cancelTask,
    onSuccess: patchTask
  });

  const postponeMutation = useMutation({
    mutationFn: (task: Task) => postponeTask(task.id, nextDay(task.due_date)),
    onSuccess: patchTask
  });

  function patchTask(task: Task) {
    queryClient.setQueryData<TaskPage>(["tasks", filters], (current) => {
      if (!current) {
        return current;
      }
      return {
        ...current,
        items: current.items.map((existing) => (existing.id === task.id ? task : existing))
      };
    });
    queryClient.invalidateQueries({ queryKey: ["tasks"] });
    setActionError(null);
  }

  function openCreateForm() {
    setEditingTask(null);
    setForm(emptyForm(courses));
    setFormError(null);
    setFormOpen(true);
  }

  function openEditForm(task: Task) {
    setEditingTask(task);
    setForm(formFromTask(task));
    setFormError(null);
    setFormOpen(true);
  }

  function closeForm() {
    setEditingTask(null);
    setForm(emptyForm(courses));
    setFormError(null);
    setFormOpen(false);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.course_id || !form.title.trim()) {
      return;
    }
    setFormError(null);
    try {
      if (editingTask) {
        await updateMutation.mutateAsync({ id: editingTask.id, payload: toUpdatePayload(form) });
      } else {
        await createMutation.mutateAsync(toCreatePayload(form));
      }
    } catch (caughtError) {
      const message =
        caughtError instanceof ApiError ? caughtError.message : "待办保存失败，请稍后重试";
      setFormError(message);
    }
  }

  async function runTaskAction(action: () => Promise<Task>) {
    setActionError(null);
    try {
      await action();
    } catch (caughtError) {
      const message =
        caughtError instanceof ApiError ? caughtError.message : "待办状态更新失败，请稍后重试";
      setActionError(message);
    }
  }

  const hasCourses = courses.length > 0;
  const isMutating =
    createMutation.isPending ||
    updateMutation.isPending ||
    completeMutation.isPending ||
    reopenMutation.isPending ||
    cancelMutation.isPending ||
    postponeMutation.isPending;

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">阶段十待办任务管理</p>
          <h2>待办任务</h2>
        </div>
        <button className="primary-button" type="button" onClick={openCreateForm} disabled={!hasCourses}>
          <Plus size={18} />
          新增待办
        </button>
      </header>

      <section className="task-filter panel">
        <label>
          课程
          <select
            value={filters.course_id}
            onChange={(event) => setFilters({ ...filters, course_id: event.target.value })}
          >
            <option value="">全部课程</option>
            {courses.map((course) => (
              <option key={course.id} value={course.id}>
                {course.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          状态
          <select
            value={filters.status}
            onChange={(event) =>
              setFilters({ ...filters, status: event.target.value as TaskStatus | "" })
            }
          >
            <option value="">全部状态</option>
            {Object.entries(statusLabels).map(([status, label]) => (
              <option key={status} value={status}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          开始日期
          <input
            type="date"
            value={filters.due_from}
            onChange={(event) => setFilters({ ...filters, due_from: event.target.value })}
          />
        </label>
        <label>
          结束日期
          <input
            type="date"
            value={filters.due_to}
            onChange={(event) => setFilters({ ...filters, due_to: event.target.value })}
          />
        </label>
        <button className="secondary-button" type="button" onClick={() => setFilters(defaultFilters)}>
          <RotateCcw size={16} />
          重置
        </button>
      </section>

      {actionError && <p className="form-error task-action-error">{actionError}</p>}

      {coursesQuery.isLoading || tasksQuery.isLoading ? (
        <section className="panel empty-state">
          <ClipboardList size={34} />
          <h3>待办加载中</h3>
        </section>
      ) : !hasCourses ? (
        <section className="panel empty-state">
          <ClipboardList size={34} />
          <h3>先创建课程</h3>
          <p>待办需要关联到课程；创建课程后就可以手动添加，或从学习计划一键生成。</p>
        </section>
      ) : tasks.length === 0 ? (
        <section className="panel empty-state">
          <ClipboardList size={34} />
          <h3>还没有匹配待办</h3>
          <p>可以手动新增待办，也可以在学习计划页预览并加入待办。</p>
          <button className="primary-button" type="button" onClick={openCreateForm}>
            <Plus size={18} />
            新增待办
          </button>
        </section>
      ) : (
        <section className="task-list" aria-label="待办列表">
          {tasks.map((task) => (
            <TaskRow
              courseName={courseMap.get(task.course_id)?.name ?? "课程"}
              disabled={isMutating}
              key={task.id}
              task={task}
              onCancel={() => runTaskAction(() => cancelMutation.mutateAsync(task.id))}
              onEdit={() => openEditForm(task)}
              onPostpone={() => runTaskAction(() => postponeMutation.mutateAsync(task))}
              onToggleDone={() =>
                runTaskAction(() =>
                  task.status === "DONE"
                    ? reopenMutation.mutateAsync(task.id)
                    : completeMutation.mutateAsync(task.id)
                )
              }
            />
          ))}
        </section>
      )}

      {formOpen && (
        <div className="modal-backdrop" role="presentation">
          <section className="modal" aria-label={editingTask ? "编辑待办" : "新增待办"}>
            <div className="modal-header">
              <h3>{editingTask ? "编辑待办" : "新增待办"}</h3>
              <button className="icon-button light" type="button" onClick={closeForm} aria-label="关闭">
                <X size={18} />
              </button>
            </div>
            <form className="form" onSubmit={handleSubmit}>
              <label>
                课程
                <select
                  value={form.course_id}
                  onChange={(event) => setForm({ ...form, course_id: event.target.value })}
                  required
                >
                  {courses.map((course) => (
                    <option key={course.id} value={course.id}>
                      {course.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                标题
                <input
                  value={form.title}
                  maxLength={160}
                  onChange={(event) => setForm({ ...form, title: event.target.value })}
                  required
                />
              </label>
              <label>
                说明
                <textarea
                  value={form.description}
                  maxLength={1200}
                  onChange={(event) => setForm({ ...form, description: event.target.value })}
                />
              </label>
              <div className="task-form-grid">
                <label>
                  日期
                  <input
                    type="date"
                    value={form.due_date}
                    onChange={(event) => setForm({ ...form, due_date: event.target.value })}
                    required
                  />
                </label>
                <label>
                  分钟
                  <input
                    type="number"
                    min={5}
                    max={720}
                    step={5}
                    value={form.estimated_minutes}
                    onChange={(event) =>
                      setForm({ ...form, estimated_minutes: Number(event.target.value) })
                    }
                    required
                  />
                </label>
                <label>
                  优先级
                  <select
                    value={form.priority}
                    onChange={(event) =>
                      setForm({ ...form, priority: event.target.value as TaskPriority })
                    }
                  >
                    <option value="LOW">低</option>
                    <option value="MEDIUM">中</option>
                    <option value="HIGH">高</option>
                  </select>
                </label>
                <label>
                  状态
                  <select
                    value={form.status}
                    onChange={(event) =>
                      setForm({ ...form, status: event.target.value as TaskStatus })
                    }
                    disabled={!editingTask}
                  >
                    {Object.entries(statusLabels).map(([status, label]) => (
                      <option key={status} value={status}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              {formError && <p className="form-error">{formError}</p>}
              <button className="primary-button" type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
                {createMutation.isPending || updateMutation.isPending ? "保存中" : "保存待办"}
              </button>
            </form>
          </section>
        </div>
      )}
    </>
  );
}

function TaskRow({
  courseName,
  disabled,
  task,
  onCancel,
  onEdit,
  onPostpone,
  onToggleDone
}: {
  courseName: string;
  disabled: boolean;
  task: Task;
  onCancel: () => void;
  onEdit: () => void;
  onPostpone: () => void;
  onToggleDone: () => void;
}) {
  const isDone = task.status === "DONE";
  return (
    <article className={`task-item ${task.status.toLowerCase()} priority-${task.priority.toLowerCase()}`}>
      <button
        className="icon-button light"
        type="button"
        onClick={onToggleDone}
        disabled={disabled || task.status === "CANCELED"}
        aria-label={isDone ? "重新打开待办" : "完成待办"}
      >
        <CheckCircle2 size={18} />
      </button>
      <div className="task-main">
        <div className="task-title-row">
          <h3>{task.title}</h3>
          <span className={`task-priority ${task.priority.toLowerCase()}`}>
            {priorityLabels[task.priority]}优先级
          </span>
        </div>
        <p>{task.description || "暂无说明"}</p>
        <div className="task-meta">
          <span>{courseName}</span>
          <span>{formatDate(task.due_date)}</span>
          <span>{task.estimated_minutes} 分钟</span>
          <span className={`task-status ${task.status.toLowerCase()}`}>
            {statusLabels[task.status]}
          </span>
        </div>
      </div>
      <div className="task-actions">
        <button className="icon-button light" type="button" onClick={onEdit} disabled={disabled} aria-label="编辑待办">
          <Edit3 size={17} />
        </button>
        <button className="icon-button light" type="button" onClick={onPostpone} disabled={disabled} aria-label="延期一天">
          <CalendarClock size={17} />
        </button>
        <button
          className="icon-button danger"
          type="button"
          onClick={onCancel}
          disabled={disabled || task.status === "CANCELED"}
          aria-label="取消待办"
        >
          <X size={17} />
        </button>
      </div>
    </article>
  );
}

function toDateInput(date: Date) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 10);
}

function nextDay(value: string) {
  const date = new Date(value);
  date.setDate(date.getDate() + 1);
  return toDateInput(date);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "short",
    day: "numeric",
    weekday: "short"
  }).format(new Date(value));
}
