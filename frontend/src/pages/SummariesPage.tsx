import { BookOpenText, FileText, RefreshCcw } from "lucide-react";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  CourseSummary,
  CourseSummaryPage,
  generateCourseSummary,
  listCourseSummaries,
  listCourses
} from "../api/client";

export function SummariesPage() {
  const queryClient = useQueryClient();
  const [courseId, setCourseId] = useState("");
  const [activeSummaryId, setActiveSummaryId] = useState<string | null>(null);

  const coursesQuery = useQuery({ queryKey: ["courses", "summaries"], queryFn: () => listCourses(), retry: 1 });
  const courses = coursesQuery.data ?? [];
  const activeCourseId = courseId || courses[0]?.id || "";
  const summariesQuery = useQuery({
    enabled: Boolean(activeCourseId),
    queryKey: ["summaries", activeCourseId],
    queryFn: () => listCourseSummaries(activeCourseId),
    retry: 1
  });
  const summaries = summariesQuery.data?.items ?? [];
  const activeSummary = useMemo(
    () => summaries.find((item) => item.id === activeSummaryId) ?? summaries[0] ?? null,
    [activeSummaryId, summaries]
  );

  const generateMutation = useMutation({
    mutationFn: () => generateCourseSummary(activeCourseId),
    onSuccess: (summary) => {
      setActiveSummaryId(summary.id);
      queryClient.setQueryData<CourseSummaryPage>(["summaries", activeCourseId], (current) => ({
        ...(current ?? { items: [], total: 0 }),
        items: [summary, ...(current?.items ?? [])],
        total: (current?.total ?? 0) + 1
      }));
    }
  });

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">知识点整理</p>
          <h2>复习提纲</h2>
        </div>
        <div className="chat-filter-row">
          <label>
            <span>课程</span>
            <select value={activeCourseId} onChange={(event) => setCourseId(event.target.value)}>
              {courses.map((course) => (
                <option value={course.id} key={course.id}>{course.name}</option>
              ))}
            </select>
          </label>
          <button
            className="primary-button"
            type="button"
            disabled={!activeCourseId || generateMutation.isPending}
            onClick={() => generateMutation.mutate()}
          >
            <RefreshCcw size={17} />
            生成提纲
          </button>
        </div>
      </header>

      {courses.length === 0 ? (
        <section className="panel empty-state">
          <BookOpenText size={34} />
          <h3>先创建课程并上传资料</h3>
          <p>资料解析并进入 READY 状态后，可以生成结构化复习提纲。</p>
        </section>
      ) : (
        <section className="summary-layout">
          <aside className="panel summary-list">
            {summariesQuery.isLoading ? (
              <p className="materials-hint">提纲加载中</p>
            ) : summaries.length === 0 ? (
              <p className="materials-hint">还没有提纲，点击生成。</p>
            ) : (
              summaries.map((summary) => (
                <button
                  className={summary.id === activeSummary?.id ? "active" : ""}
                  key={summary.id}
                  type="button"
                  onClick={() => setActiveSummaryId(summary.id)}
                >
                  <FileText size={16} />
                  <span>{summary.title}</span>
                </button>
              ))
            )}
          </aside>

          {activeSummary ? <SummaryDetail summary={activeSummary} /> : (
            <section className="panel empty-state">
              <FileText size={34} />
              <h3>生成第一份复习提纲</h3>
              <p>系统会从课程资料 chunk 中提取重点知识点，并保存版本。</p>
            </section>
          )}
        </section>
      )}
    </>
  );
}

function SummaryDetail({ summary }: { summary: CourseSummary }) {
  return (
    <section className="panel summary-detail">
      <div className="panel-header">
        <div>
          <p className="eyebrow">{summary.scope} v{summary.version}</p>
          <h3>{summary.title}</h3>
        </div>
      </div>
      <div className="knowledge-grid">
        {summary.knowledge_points.map((point) => (
          <article className="knowledge-card" key={point.title}>
            <strong>{point.title}</strong>
            <p>{point.detail}</p>
            <span>{point.source_count} 个来源片段</span>
          </article>
        ))}
      </div>
      <pre className="markdown-preview">{summary.outline_md}</pre>
    </section>
  );
}
