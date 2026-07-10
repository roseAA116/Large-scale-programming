import { FormEvent, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, Edit3, FileText, Plus, Search, Trash2, UploadCloud, X } from "lucide-react";

import {
  ApiError,
  Course,
  CoursePayload,
  Material,
  MaterialStatus,
  createCourse,
  deleteCourse,
  deleteMaterial,
  listMaterials,
  listCourses,
  updateCourse,
  uploadMaterial
} from "../api/client";

type CourseFormState = {
  name: string;
  description: string;
  teacher: string;
  semester: string;
};

const emptyForm: CourseFormState = {
  name: "",
  description: "",
  teacher: "",
  semester: ""
};

function toFormState(course: Course): CourseFormState {
  return {
    name: course.name,
    description: course.description ?? "",
    teacher: course.teacher ?? "",
    semester: course.semester ?? ""
  };
}

function toPayload(form: CourseFormState): CoursePayload {
  return {
    name: form.name,
    description: form.description || null,
    teacher: form.teacher || null,
    semester: form.semester || null
  };
}

const materialStatusLabels: Record<MaterialStatus, string> = {
  UPLOADED: "已上传",
  PARSING: "解析中",
  PARSED: "已解析",
  INDEXING: "索引中",
  READY: "可使用",
  FAILED: "失败"
};

const materialTypeLabels: Record<string, string> = {
  pdf: "PDF",
  docx: "DOCX",
  pptx: "PPTX",
  txt: "TXT",
  md: "Markdown",
  image: "图片"
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function CoursesPage() {
  const queryClient = useQueryClient();
  const [keyword, setKeyword] = useState("");
  const [appliedKeyword, setAppliedKeyword] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editingCourse, setEditingCourse] = useState<Course | null>(null);
  const [deletingCourse, setDeletingCourse] = useState<Course | null>(null);
  const [form, setForm] = useState<CourseFormState>(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const coursesQuery = useQuery({
    queryKey: ["courses", appliedKeyword],
    queryFn: () => listCourses(appliedKeyword),
    retry: 1
  });

  const courses = useMemo(() => coursesQuery.data ?? [], [coursesQuery.data]);

  const createMutation = useMutation({
    mutationFn: createCourse,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["courses"] });
      closeForm();
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CoursePayload }) => updateCourse(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["courses"] });
      closeForm();
    }
  });

  const deleteMutation = useMutation({
    mutationFn: deleteCourse,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["courses"] });
      setDeletingCourse(null);
      setDeleteError(null);
    }
  });

  function openCreateForm() {
    setEditingCourse(null);
    setForm(emptyForm);
    setFormError(null);
    setFormOpen(true);
  }

  function openEditForm(course: Course) {
    setEditingCourse(course);
    setForm(toFormState(course));
    setFormError(null);
    setFormOpen(true);
  }

  function closeForm() {
    setEditingCourse(null);
    setForm(emptyForm);
    setFormError(null);
    setFormOpen(false);
  }

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAppliedKeyword(keyword);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);

    try {
      if (editingCourse) {
        await updateMutation.mutateAsync({ id: editingCourse.id, payload: toPayload(form) });
      } else {
        await createMutation.mutateAsync(toPayload(form));
      }
    } catch (caughtError) {
      const message =
        caughtError instanceof ApiError ? caughtError.message : "课程保存失败，请稍后重试";
      setFormError(message);
    }
  }

  async function confirmDelete() {
    if (!deletingCourse) {
      return;
    }
    setDeleteError(null);
    try {
      await deleteMutation.mutateAsync(deletingCourse.id);
    } catch (caughtError) {
      const message =
        caughtError instanceof ApiError ? caughtError.message : "课程删除失败，请稍后重试";
      setDeleteError(message);
    }
  }

  const submitting = createMutation.isPending || updateMutation.isPending;

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">阶段三课程管理</p>
          <h2>课程</h2>
        </div>
        <button className="primary-button" type="button" onClick={openCreateForm}>
          <Plus size={18} />
          新增课程
        </button>
      </header>

      <section className="course-toolbar">
        <form className="search-box" onSubmit={handleSearch}>
          <Search size={18} />
          <input
            value={keyword}
            placeholder="搜索课程、教师、学期"
            onChange={(event) => setKeyword(event.target.value)}
          />
          <button type="submit">搜索</button>
        </form>
      </section>

      {coursesQuery.isLoading ? (
        <section className="panel empty-state">
          <BookOpen size={30} />
          <h3>课程加载中</h3>
        </section>
      ) : courses.length === 0 ? (
        <section className="panel empty-state">
          <BookOpen size={34} />
          <h3>{appliedKeyword ? "没有匹配课程" : "还没有课程"}</h3>
          <p>{appliedKeyword ? "换个关键词再试试。" : "创建第一门课程后，资料和 Agent 问答会围绕它展开。"}</p>
          <button className="primary-button" type="button" onClick={openCreateForm}>
            <Plus size={18} />
            新增课程
          </button>
        </section>
      ) : (
        <section className="course-list" aria-label="课程列表">
          {courses.map((course) => (
            <article className="course-item" key={course.id}>
              <div className="course-row">
                <div className="course-main">
                  <BookOpen size={22} />
                  <div>
                    <h3>{course.name}</h3>
                    <p>{course.description || "暂无课程简介"}</p>
                    <div className="course-meta">
                      <span>{course.teacher || "未填写教师"}</span>
                      <span>{course.semester || "未填写学期"}</span>
                    </div>
                  </div>
                </div>
                <div className="course-actions">
                  <button className="icon-button light" type="button" onClick={() => openEditForm(course)} aria-label="编辑课程">
                    <Edit3 size={17} />
                  </button>
                  <button className="icon-button danger" type="button" onClick={() => setDeletingCourse(course)} aria-label="删除课程">
                    <Trash2 size={17} />
                  </button>
                </div>
              </div>
              <CourseMaterials courseId={course.id} />
            </article>
          ))}
        </section>
      )}

      {formOpen && (
        <div className="modal-backdrop" role="presentation">
          <section className="modal" aria-label={editingCourse ? "编辑课程" : "新增课程"}>
            <div className="modal-header">
              <h3>{editingCourse ? "编辑课程" : "新增课程"}</h3>
              <button className="icon-button light" type="button" onClick={closeForm} aria-label="关闭">
                <X size={18} />
              </button>
            </div>
            <form className="form" onSubmit={handleSubmit}>
              <label>
                课程名称
                <input
                  value={form.name}
                  maxLength={100}
                  onChange={(event) => setForm({ ...form, name: event.target.value })}
                  required
                />
              </label>
              <label>
                课程简介
                <textarea
                  value={form.description}
                  maxLength={2000}
                  onChange={(event) => setForm({ ...form, description: event.target.value })}
                />
              </label>
              <label>
                授课教师
                <input
                  value={form.teacher}
                  maxLength={120}
                  onChange={(event) => setForm({ ...form, teacher: event.target.value })}
                />
              </label>
              <label>
                学期
                <input
                  value={form.semester}
                  maxLength={60}
                  placeholder="例如 2026 春季"
                  onChange={(event) => setForm({ ...form, semester: event.target.value })}
                />
              </label>
              {formError && <p className="form-error">{formError}</p>}
              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "保存中" : "保存课程"}
              </button>
            </form>
          </section>
        </div>
      )}

      {deletingCourse && (
        <div className="modal-backdrop" role="presentation">
          <section className="modal confirm-modal" aria-label="删除课程确认">
            <div className="modal-header">
              <h3>删除课程</h3>
              <button className="icon-button light" type="button" onClick={() => setDeletingCourse(null)} aria-label="关闭">
                <X size={18} />
              </button>
            </div>
            <p>确认删除“{deletingCourse.name}”？删除后课程将不会出现在列表中。</p>
            {deleteError && <p className="form-error">{deleteError}</p>}
            <div className="confirm-actions">
              <button className="secondary-button" type="button" onClick={() => setDeletingCourse(null)}>
                取消
              </button>
              <button className="danger-button" type="button" onClick={confirmDelete} disabled={deleteMutation.isPending}>
                {deleteMutation.isPending ? "删除中" : "确认删除"}
              </button>
            </div>
          </section>
        </div>
      )}
    </>
  );
}

function CourseMaterials({ courseId }: { courseId: string }) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [title, setTitle] = useState("");
  const [materialType, setMaterialType] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const materialsQuery = useQuery({
    queryKey: ["materials", courseId],
    queryFn: () => listMaterials(courseId),
    retry: 1
  });

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!selectedFile) {
        throw new ApiError("请选择要上传的资料", "MATERIAL_FILE_REQUIRED", 400);
      }
      return uploadMaterial(courseId, {
        file: selectedFile,
        title,
        material_type: materialType,
        onProgress: setUploadProgress
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["materials", courseId] });
      setSelectedFile(null);
      setTitle("");
      setMaterialType("");
      setUploadProgress(0);
      setUploadError(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  });

  const deleteMutation = useMutation({
    mutationFn: deleteMaterial,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["materials", courseId] });
      setDeleteError(null);
    }
  });

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setUploadError(null);
    setUploadProgress(0);
    try {
      await uploadMutation.mutateAsync();
    } catch (caughtError) {
      const message = caughtError instanceof ApiError ? caughtError.message : "资料上传失败，请稍后重试";
      setUploadError(message);
    }
  }

  async function handleDelete(material: Material) {
    setDeleteError(null);
    try {
      await deleteMutation.mutateAsync(material.id);
    } catch (caughtError) {
      const message = caughtError instanceof ApiError ? caughtError.message : "资料删除失败，请稍后重试";
      setDeleteError(message);
    }
  }

  const materials = materialsQuery.data ?? [];

  return (
    <section className="materials-section" aria-label="课程资料">
      <div className="materials-header">
        <div>
          <h4>课程资料</h4>
          <p>支持 PDF、DOCX、PPTX、TXT、MD 和图片，单文件 100MB 内。</p>
        </div>
      </div>

      <form className="material-upload" onSubmit={handleUpload}>
        <label className="file-picker">
          <UploadCloud size={18} />
          <span>{selectedFile ? selectedFile.name : "选择资料文件"}</span>
          <input
            accept=".pdf,.docx,.pptx,.txt,.md,.png,.jpg,.jpeg"
            ref={fileInputRef}
            type="file"
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <input
          value={title}
          maxLength={255}
          placeholder="资料标题（可选）"
          onChange={(event) => setTitle(event.target.value)}
        />
        <select value={materialType} onChange={(event) => setMaterialType(event.target.value)}>
          <option value="">自动识别类型</option>
          <option value="pdf">PDF</option>
          <option value="docx">DOCX</option>
          <option value="pptx">PPTX</option>
          <option value="txt">TXT</option>
          <option value="md">Markdown</option>
          <option value="image">图片</option>
        </select>
        <button className="primary-button" type="submit" disabled={uploadMutation.isPending}>
          {uploadMutation.isPending ? "上传中" : "上传"}
        </button>
      </form>

      {uploadMutation.isPending && (
        <div className="upload-progress" aria-label="上传进度">
          <span style={{ width: `${uploadProgress}%` }} />
        </div>
      )}
      {uploadError && <p className="form-error">{uploadError}</p>}
      {deleteError && <p className="form-error">{deleteError}</p>}

      {materialsQuery.isLoading ? (
        <p className="materials-hint">资料加载中</p>
      ) : materials.length === 0 ? (
        <p className="materials-hint">还没有资料，上传后会在这里显示解析状态。</p>
      ) : (
        <div className="materials-list">
          {materials.map((material) => (
            <article className="material-item" key={material.id}>
              <FileText size={18} />
              <div className="material-main">
                <strong>{material.title}</strong>
                <span>
                  {material.original_filename} · {materialTypeLabels[material.material_type] ?? material.material_type} ·{" "}
                  {formatFileSize(material.file_size)}
                </span>
              </div>
              <span className={`material-status ${material.status.toLowerCase()}`}>
                {materialStatusLabels[material.status]}
              </span>
              <button
                className="icon-button danger"
                type="button"
                onClick={() => handleDelete(material)}
                disabled={deleteMutation.isPending}
                aria-label="删除资料"
              >
                <Trash2 size={16} />
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
