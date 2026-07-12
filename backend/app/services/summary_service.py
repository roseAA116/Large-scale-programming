from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models import Course, CourseSummary, Material, MaterialChunk, MaterialStatus
from app.schemas.summary import CourseSummaryRead


class SummaryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def generate_summary(
        self,
        *,
        user_id: str,
        course_id: str,
        material_id: str | None = None,
    ) -> CourseSummaryRead:
        course = await self._get_course(user_id=user_id, course_id=course_id)
        material = None
        if material_id:
            material = await self._get_material(
                user_id=user_id,
                course_id=course_id,
                material_id=material_id,
            )
        chunks = await self._load_chunks(
            user_id=user_id,
            course_id=course_id,
            material_id=material_id,
        )
        if not chunks:
            raise AppError(
                "SUMMARY_SOURCE_EMPTY",
                "No indexed chunks are available for summary generation.",
                status_code=409,
            )

        scope = "MATERIAL" if material_id else "COURSE"
        version = await self._next_version(user_id=user_id, course_id=course_id, material_id=material_id)
        knowledge_points = build_knowledge_points(chunks)
        outline = build_outline_markdown(
            course_name=course.name,
            material_title=material.title if material else None,
            knowledge_points=knowledge_points,
            chunk_count=len(chunks),
        )
        summary = CourseSummary(
            user_id=user_id,
            course_id=course_id,
            material_id=material_id,
            scope=scope,
            version=version,
            title=f"{course.name}{' - ' + material.title if material else ''} 复习提纲 v{version}",
            outline_md=outline,
            knowledge_points=knowledge_points,
            status="READY",
        )
        self.db.add(summary)
        await self.db.commit()
        await self.db.refresh(summary)
        return CourseSummaryRead.model_validate(summary)

    async def list_summaries(
        self,
        *,
        user_id: str,
        course_id: str | None = None,
        material_id: str | None = None,
    ) -> tuple[list[CourseSummaryRead], int]:
        statement = select(CourseSummary).where(CourseSummary.user_id == user_id)
        count_statement = select(func.count()).select_from(CourseSummary).where(
            CourseSummary.user_id == user_id
        )
        if course_id:
            statement = statement.where(CourseSummary.course_id == course_id)
            count_statement = count_statement.where(CourseSummary.course_id == course_id)
        if material_id:
            statement = statement.where(CourseSummary.material_id == material_id)
            count_statement = count_statement.where(CourseSummary.material_id == material_id)

        total = await self.db.scalar(count_statement) or 0
        summaries = (
            await self.db.scalars(statement.order_by(CourseSummary.updated_at.desc()).limit(50))
        ).all()
        return [CourseSummaryRead.model_validate(summary) for summary in summaries], total

    async def read_summary(self, *, user_id: str, summary_id: str) -> CourseSummaryRead:
        summary = await self.db.scalar(
            select(CourseSummary).where(
                CourseSummary.id == summary_id,
                CourseSummary.user_id == user_id,
            )
        )
        if summary is None:
            raise AppError("SUMMARY_NOT_FOUND", "Summary not found.", status_code=404)
        return CourseSummaryRead.model_validate(summary)

    async def _get_course(self, *, user_id: str, course_id: str) -> Course:
        course = await self.db.scalar(
            select(Course).where(
                Course.id == course_id,
                Course.user_id == user_id,
                Course.deleted_at.is_(None),
            )
        )
        if course is None:
            raise AppError("SUMMARY_COURSE_NOT_FOUND", "Course not found.", status_code=404)
        return course

    async def _get_material(self, *, user_id: str, course_id: str, material_id: str) -> Material:
        material = await self.db.scalar(
            select(Material).where(
                Material.id == material_id,
                Material.user_id == user_id,
                Material.course_id == course_id,
                Material.deleted_at.is_(None),
                Material.status == MaterialStatus.READY,
            )
        )
        if material is None:
            raise AppError("SUMMARY_MATERIAL_NOT_FOUND", "Ready material not found.", status_code=404)
        return material

    async def _load_chunks(
        self,
        *,
        user_id: str,
        course_id: str,
        material_id: str | None,
    ) -> list[MaterialChunk]:
        statement = (
            select(MaterialChunk)
            .join(Material, Material.id == MaterialChunk.material_id)
            .where(
                MaterialChunk.user_id == user_id,
                MaterialChunk.course_id == course_id,
                Material.user_id == user_id,
                Material.course_id == course_id,
                Material.deleted_at.is_(None),
                Material.status == MaterialStatus.READY,
            )
            .order_by(MaterialChunk.material_id.asc(), MaterialChunk.position.asc())
            .limit(80)
        )
        if material_id:
            statement = statement.where(MaterialChunk.material_id == material_id)
        return list((await self.db.scalars(statement)).all())

    async def _next_version(
        self,
        *,
        user_id: str,
        course_id: str,
        material_id: str | None,
    ) -> int:
        statement = select(func.max(CourseSummary.version)).where(
            CourseSummary.user_id == user_id,
            CourseSummary.course_id == course_id,
            CourseSummary.material_id.is_(None) if material_id is None else CourseSummary.material_id == material_id,
        )
        current = await self.db.scalar(statement)
        return int(current or 0) + 1


def build_knowledge_points(chunks: list[MaterialChunk], *, limit: int = 8) -> list[dict]:
    section_counter: Counter[str] = Counter()
    examples: dict[str, str] = {}
    for chunk in chunks:
        title = (chunk.section_title or _first_sentence(chunk.text) or "核心知识点").strip()
        normalized = title[:48]
        section_counter[normalized] += 1
        examples.setdefault(normalized, _compact(chunk.text, 180))

    points = []
    for title, count in section_counter.most_common(limit):
        points.append(
            {
                "title": title,
                "detail": examples[title],
                "source_count": count,
            }
        )
    return points


def build_outline_markdown(
    *,
    course_name: str,
    material_title: str | None,
    knowledge_points: list[dict],
    chunk_count: int,
) -> str:
    title = material_title or course_name
    lines = [
        f"# {title} 复习提纲",
        "",
        f"- 覆盖资料片段：{chunk_count} 个",
        f"- 生成范围：{'单个资料' if material_title else '整门课程'}",
        "",
        "## 重点知识点",
    ]
    for index, point in enumerate(knowledge_points, start=1):
        lines.extend(
            [
                f"{index}. **{point['title']}**",
                f"   - {point['detail']}",
            ]
        )
    lines.extend(
        [
            "",
            "## 复习建议",
            "- 先按提纲扫清概念，再回到课程问答页针对薄弱点追问。",
            "- 将每个知识点转化为可完成的待办任务，并在复习后标记完成。",
        ]
    )
    return "\n".join(lines)


def _first_sentence(text: str) -> str:
    for separator in ("。", ".", "\n"):
        if separator in text:
            return text.split(separator, 1)[0]
    return text[:48]


def _compact(text: str, max_length: int) -> str:
    compacted = " ".join(text.split())
    if len(compacted) <= max_length:
        return compacted
    return f"{compacted[: max_length - 1]}…"
