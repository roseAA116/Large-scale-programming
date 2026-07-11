import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, BookOpen, FileText, MessageSquare, Quote, Send, Sparkles, UserRound } from "lucide-react";

import {
  AnswerCitation,
  ApiError,
  ChatMessage,
  ChatSession,
  Course,
  SearchMode,
  SearchResult,
  askAgent,
  getChatSession,
  listChatSessions,
  listCourses
} from "../api/client";

const searchModeLabels: Record<SearchMode, string> = {
  hybrid: "混合",
  keyword: "关键词",
  vector: "向量"
};

export function ChatPage() {
  const queryClient = useQueryClient();
  const [courseId, setCourseId] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [materialType, setMaterialType] = useState("");
  const [searchMode, setSearchMode] = useState<SearchMode>("hybrid");
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);
  const [contexts, setContexts] = useState<SearchResult[]>([]);
  const [activeCitation, setActiveCitation] = useState<AnswerCitation | null>(null);
  const [askError, setAskError] = useState<string | null>(null);

  const coursesQuery = useQuery({
    queryKey: ["courses", "chat"],
    queryFn: () => listCourses(),
    retry: 1
  });

  const courses = useMemo(() => coursesQuery.data ?? [], [coursesQuery.data]);

  useEffect(() => {
    if (!courseId && courses.length > 0) {
      setCourseId(courses[0].id);
    }
  }, [courseId, courses]);

  const sessionsQuery = useQuery({
    enabled: Boolean(courseId),
    queryKey: ["chat-sessions", courseId],
    queryFn: () => listChatSessions(courseId),
    retry: 1
  });

  const sessionDetailQuery = useQuery({
    enabled: Boolean(sessionId),
    queryKey: ["chat-session", sessionId],
    queryFn: () => getChatSession(sessionId as string),
    retry: 1
  });

  useEffect(() => {
    setLocalMessages(sessionDetailQuery.data?.messages ?? []);
  }, [sessionDetailQuery.data]);

  const askMutation = useMutation({
    mutationFn: () =>
      askAgent({
        course_id: courseId,
        question,
        session_id: sessionId,
        material_type: materialType || null,
        search_mode: searchMode
      }),
    onSuccess: (result) => {
      setSessionId(result.session.id);
      setLocalMessages((messages) => [...messages, result.question, result.answer]);
      setContexts(result.contexts);
      setQuestion("");
      setAskError(null);
      queryClient.invalidateQueries({ queryKey: ["chat-sessions", courseId] });
      queryClient.setQueryData(["chat-session", result.session.id], {
        session: result.session,
        messages: [...localMessages, result.question, result.answer]
      });
    }
  });

  function handleCourseChange(nextCourseId: string) {
    setCourseId(nextCourseId);
    setSessionId(null);
    setLocalMessages([]);
    setContexts([]);
    setAskError(null);
  }

  function startNewSession() {
    setSessionId(null);
    setLocalMessages([]);
    setContexts([]);
    setAskError(null);
  }

  async function handleAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!courseId || !question.trim()) {
      return;
    }
    setAskError(null);
    try {
      await askMutation.mutateAsync();
    } catch (caughtError) {
      const message =
        caughtError instanceof ApiError ? caughtError.message : "Agent 回答失败，请稍后重试";
      setAskError(message);
    }
  }

  const activeCourse = courses.find((course) => course.id === courseId) ?? null;
  const sessions = sessionsQuery.data ?? [];

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">阶段六检索与 Agent 问答</p>
          <h2>课程问答</h2>
        </div>
        <div className="chat-filter-row">
          <label>
            <span>课程</span>
            <select value={courseId} onChange={(event) => handleCourseChange(event.target.value)}>
              {courses.map((course) => (
                <option value={course.id} key={course.id}>
                  {course.name}
                </option>
              ))}
            </select>
          </label>
          <button className="secondary-button" type="button" onClick={startNewSession}>
            新对话
          </button>
        </div>
      </header>

      {coursesQuery.isLoading ? (
        <section className="panel empty-state">
          <BookOpen size={30} />
          <h3>课程加载中</h3>
        </section>
      ) : courses.length === 0 ? (
        <section className="panel empty-state">
          <BookOpen size={34} />
          <h3>还没有课程</h3>
          <p>先创建课程并上传资料，Agent 才能围绕课程内容回答问题。</p>
        </section>
      ) : (
        <section className="chat-layout">
          <aside className="chat-sidebar panel">
            <div className="chat-sidebar-header">
              <h3>{activeCourse?.name ?? "课程"}</h3>
              <p>{sessions.length} 个历史对话</p>
            </div>
            <div className="session-list">
              {sessionsQuery.isLoading ? (
                <p className="materials-hint">历史对话加载中</p>
              ) : sessions.length === 0 ? (
                <p className="materials-hint">还没有历史对话。</p>
              ) : (
                sessions.map((session) => (
                  <SessionButton
                    active={session.id === sessionId}
                    key={session.id}
                    session={session}
                    onClick={() => {
                      setSessionId(session.id);
                      setContexts([]);
                      setAskError(null);
                    }}
                  />
                ))
              )}
            </div>
          </aside>

          <section className="chat-panel panel">
            <div className="message-list" aria-label="对话消息">
              {sessionDetailQuery.isLoading ? (
                <div className="empty-state chat-empty">
                  <MessageSquare size={34} />
                  <h3>对话加载中</h3>
                </div>
              ) : localMessages.length === 0 ? (
                <div className="empty-state chat-empty">
                  <Sparkles size={34} />
                  <h3>问一个课程资料里的问题</h3>
                  <p>选择课程后，Agent 会先检索 READY 资料，再基于相关片段回答。</p>
                </div>
              ) : (
                localMessages.map((message) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    onOpenCitation={setActiveCitation}
                  />
                ))
              )}
              {askMutation.isPending && (
                <div className="message assistant">
                  <Bot size={18} />
                  <div className="message-body">
                    <span className="typing">正在检索资料并生成回答</span>
                  </div>
                </div>
              )}
            </div>

            {contexts.length > 0 && <ContextStrip contexts={contexts} />}
            {askError && <p className="form-error chat-error">{askError}</p>}

            <form className="chat-composer" onSubmit={handleAsk}>
              <div className="chat-options">
                <select value={materialType} onChange={(event) => setMaterialType(event.target.value)}>
                  <option value="">全部资料类型</option>
                  <option value="pdf">PDF</option>
                  <option value="docx">DOCX</option>
                  <option value="pptx">PPTX</option>
                  <option value="txt">TXT</option>
                  <option value="md">Markdown</option>
                  <option value="image">图片</option>
                </select>
                <div className="segmented" role="group" aria-label="检索模式">
                  {(Object.keys(searchModeLabels) as SearchMode[]).map((mode) => (
                    <button
                      className={searchMode === mode ? "active" : ""}
                      key={mode}
                      type="button"
                      onClick={() => setSearchMode(mode)}
                    >
                      {searchModeLabels[mode]}
                    </button>
                  ))}
                </div>
              </div>
              <label className="chat-input">
                <textarea
                  value={question}
                  maxLength={2000}
                  placeholder="输入你的问题，例如：这章的核心概念是什么？"
                  onChange={(event) => setQuestion(event.target.value)}
                />
                <button
                  className="primary-button"
                  type="submit"
                  disabled={!courseId || !question.trim() || askMutation.isPending}
                  aria-label="发送问题"
                >
                  <Send size={18} />
                  发送
                </button>
              </label>
            </form>
          </section>
        </section>
      )}

      {activeCitation && (
        <CitationModal citation={activeCitation} onClose={() => setActiveCitation(null)} />
      )}
    </>
  );
}

function SessionButton({
  active,
  session,
  onClick
}: {
  active: boolean;
  session: ChatSession;
  onClick: () => void;
}) {
  return (
    <button className={`session-button ${active ? "active" : ""}`} type="button" onClick={onClick}>
      <MessageSquare size={16} />
      <span>{session.title}</span>
    </button>
  );
}

function MessageBubble({
  message,
  onOpenCitation
}: {
  message: ChatMessage;
  onOpenCitation: (citation: AnswerCitation) => void;
}) {
  const assistant = message.role === "ASSISTANT";
  return (
    <article className={`message ${assistant ? "assistant" : "user"}`}>
      {assistant ? <Bot size={18} /> : <UserRound size={18} />}
      <div className="message-body">
        {message.content.split("\n").map((line, index) => (
          <p key={`${message.id}-${index}`}>{line || " "}</p>
        ))}
        {assistant && (
          <CitationList citations={message.citations ?? []} onOpenCitation={onOpenCitation} />
        )}
      </div>
    </article>
  );
}

function CitationList({
  citations,
  onOpenCitation
}: {
  citations: AnswerCitation[];
  onOpenCitation: (citation: AnswerCitation) => void;
}) {
  if (citations.length === 0) {
    return <p className="citation-empty">本次回答没有可靠引用来源。</p>;
  }

  return (
    <div className="citation-list" aria-label="回答引用">
      {citations.slice(0, 6).map((citation) => (
        <button
          className="citation-button"
          key={citation.id}
          type="button"
          onClick={() => onOpenCitation(citation)}
        >
          <Quote size={14} />
          <span>{formatCitationLabel(citation)}</span>
        </button>
      ))}
    </div>
  );
}

function CitationModal({
  citation,
  onClose
}: {
  citation: AnswerCitation;
  onClose: () => void;
}) {
  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <section className="modal citation-modal" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <div>
            <p className="eyebrow">来源片段</p>
            <h3>{citation.material_title}</h3>
          </div>
          <button className="icon-button light" type="button" onClick={onClose} aria-label="关闭">
            ×
          </button>
        </div>
        <div className="citation-source">
          <FileText size={18} />
          <span>{formatCitationLabel(citation)}</span>
        </div>
        <blockquote>{citation.quote}</blockquote>
      </section>
    </div>
  );
}

function formatCitationLabel(citation: AnswerCitation) {
  const parts = [citation.material_title];
  if (citation.section_title) {
    parts.push(citation.section_title);
  }
  if (citation.page_no !== null) {
    parts.push(`第 ${citation.page_no} 页`);
  }
  if (citation.slide_no !== null) {
    parts.push(`第 ${citation.slide_no} 页幻灯片`);
  }
  return parts.join(" / ");
}

function ContextStrip({ contexts }: { contexts: SearchResult[] }) {
  return (
    <div className="context-strip" aria-label="检索片段">
      {contexts.slice(0, 4).map((context) => (
        <article className="context-chip" key={context.chunk_id}>
          <strong>{context.material_title}</strong>
          <span>{context.section_title || context.material_type.toUpperCase()}</span>
        </article>
      ))}
    </div>
  );
}
