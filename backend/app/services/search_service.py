import math
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Material, MaterialChunk, MaterialStatus
from app.schemas.chat import SearchMode, SearchResultRead
from app.services.embeddings import EmbeddingClient


@dataclass
class ChunkCandidate:
    chunk: MaterialChunk
    material: Material
    keyword_score: float
    vector_score: float

    @property
    def score(self) -> float:
        if self.keyword_score == 0:
            return self.vector_score
        if self.vector_score == 0:
            return self.keyword_score
        return (self.keyword_score * 0.42) + (self.vector_score * 0.58)


class SearchService:
    def __init__(self, db: AsyncSession, embedding_client: EmbeddingClient | None = None) -> None:
        self.db = db
        self.embedding_client = embedding_client or EmbeddingClient()

    async def search_course_materials(
        self,
        *,
        user_id: str,
        course_id: str,
        query: str,
        material_type: str | None = None,
        mode: SearchMode = "hybrid",
        limit: int = 8,
    ) -> list[SearchResultRead]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        candidates = await self._load_candidates(user_id, course_id, material_type)
        if not candidates:
            return []

        query_embedding: list[float] | None = None
        if mode in {"vector", "hybrid"}:
            query_embedding = (await self.embedding_client.embed_texts([normalized_query]))[0]

        tokens = _tokenize(normalized_query)
        scored: list[ChunkCandidate] = []
        for chunk, material in candidates:
            keyword_score = _keyword_score(tokens, normalized_query, chunk.text, material.title)
            vector_score = _cosine_similarity(query_embedding, chunk.embedding)
            if mode == "keyword":
                vector_score = 0
            elif mode == "vector":
                keyword_score = 0
            if keyword_score > 0 or vector_score > 0:
                scored.append(
                    ChunkCandidate(
                        chunk=chunk,
                        material=material,
                        keyword_score=keyword_score,
                        vector_score=vector_score,
                    )
                )

        scored.sort(key=lambda item: (item.score, item.chunk.updated_at), reverse=True)
        return [_to_search_result(item) for item in scored[:limit]]

    async def ready_material_count(self, *, user_id: str, course_id: str) -> int:
        statement = select(Material.id).where(
            Material.user_id == user_id,
            Material.course_id == course_id,
            Material.deleted_at.is_(None),
            Material.status == MaterialStatus.READY,
        )
        return len((await self.db.scalars(statement)).all())

    async def _load_candidates(
        self,
        user_id: str,
        course_id: str,
        material_type: str | None,
    ) -> list[tuple[MaterialChunk, Material]]:
        statement = (
            select(MaterialChunk, Material)
            .join(Material, Material.id == MaterialChunk.material_id)
            .where(
                MaterialChunk.user_id == user_id,
                MaterialChunk.course_id == course_id,
                Material.user_id == user_id,
                Material.course_id == course_id,
                Material.deleted_at.is_(None),
                Material.status == MaterialStatus.READY,
            )
            .order_by(MaterialChunk.updated_at.desc())
        )
        if material_type:
            statement = statement.where(Material.material_type == material_type.strip().lower())

        rows = (await self.db.execute(statement)).all()
        return [(row[0], row[1]) for row in rows]


def _tokenize(query: str) -> list[str]:
    tokens = [token.lower() for token in re.findall(r"[\w\u4e00-\u9fff]+", query)]
    if not tokens and query.strip():
        return [query.strip().lower()]
    return tokens


def _keyword_score(tokens: list[str], query: str, text: str, title: str) -> float:
    lower_text = text.lower()
    lower_title = title.lower()
    score = 0.0
    for token in tokens:
        if token in lower_title:
            score += 0.32
        occurrences = lower_text.count(token)
        if occurrences:
            score += min(0.56, 0.14 * occurrences)
    if query.lower() in lower_text:
        score += 0.28
    return min(score, 1.0)


def _cosine_similarity(
    query_embedding: list[float] | None,
    chunk_embedding: list[float] | None,
) -> float:
    if not query_embedding or not chunk_embedding:
        return 0.0
    size = min(len(query_embedding), len(chunk_embedding))
    if size == 0:
        return 0.0
    dot = sum(query_embedding[index] * chunk_embedding[index] for index in range(size))
    query_norm = math.sqrt(sum(value * value for value in query_embedding[:size]))
    chunk_norm = math.sqrt(sum(value * value for value in chunk_embedding[:size]))
    if query_norm == 0 or chunk_norm == 0:
        return 0.0
    return max(0.0, min(1.0, (dot / (query_norm * chunk_norm) + 1) / 2))


def _to_search_result(candidate: ChunkCandidate) -> SearchResultRead:
    chunk = candidate.chunk
    material = candidate.material
    return SearchResultRead(
        chunk_id=chunk.id,
        material_id=material.id,
        material_title=material.title,
        material_type=material.material_type,
        text=chunk.text,
        score=round(candidate.score, 6),
        keyword_score=round(candidate.keyword_score, 6),
        vector_score=round(candidate.vector_score, 6),
        page_no=chunk.page_no,
        slide_no=chunk.slide_no,
        section_title=chunk.section_title,
    )
