import tempfile
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete, select

from app.core.config import settings
from app.core.errors import AppError
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models import Material, MaterialChunk, MaterialStatus
from app.services.embeddings import EmbeddingClient
from app.services.material_chunking import chunk_blocks
from app.services.material_parsing import parse_material_file
from app.services.storage import download_material_object
from app.services.task_queue import enqueue_index_material

logger = get_logger(__name__)


async def process_parse_material(material_id: str) -> None:
    async with AsyncSessionLocal() as db:
        material = await _get_material(db, material_id)
        if material is None:
            logger.warning("parse_material_missing", extra={"material_id": material_id})
            return
        if material.deleted_at is not None:
            logger.info("parse_material_deleted_skip", extra={"material_id": material_id})
            return

        material.status = MaterialStatus.PARSING
        material.error_message = None
        await db.commit()

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / Path(material.original_filename).name
            download_material_object(
                object_key=material.object_key,
                destination_path=str(file_path),
            )
            parsed_document = parse_material_file(file_path, material.material_type)
            chunk_drafts = chunk_blocks(material.id, parsed_document.blocks)
            if not chunk_drafts:
                raise AppError("PARSE_EMPTY_CONTENT", "No chunks were generated from material.")

        async with AsyncSessionLocal() as db:
            material = await _get_material(db, material_id)
            if material is None or material.deleted_at is not None:
                return
            await db.execute(delete(MaterialChunk).where(MaterialChunk.material_id == material.id))
            for draft in chunk_drafts:
                db.add(
                    MaterialChunk(
                        id=draft.id,
                        material_id=material.id,
                        course_id=material.course_id,
                        user_id=material.user_id,
                        position=draft.position,
                        text=draft.text,
                        token_count=draft.token_count,
                        page_no=draft.page_no,
                        slide_no=draft.slide_no,
                        section_title=draft.section_title,
                        chunk_metadata=draft.metadata,
                    )
                )
            material.status = MaterialStatus.PARSED
            material.error_message = None
            material.updated_at = datetime.now(UTC)
            await db.commit()
        enqueue_index_material(material_id)
        logger.info(
            "parse_material_completed",
            extra={"material_id": material_id, "chunk_count": len(chunk_drafts)},
        )
    except Exception as exc:
        await mark_material_failed(material_id, exc)
        raise


async def process_index_material(material_id: str) -> None:
    async with AsyncSessionLocal() as db:
        material = await _get_material(db, material_id)
        if material is None:
            logger.warning("index_material_missing", extra={"material_id": material_id})
            return
        if material.deleted_at is not None:
            logger.info("index_material_deleted_skip", extra={"material_id": material_id})
            return
        material.status = MaterialStatus.INDEXING
        material.error_message = None
        await db.commit()

    try:
        client = EmbeddingClient()
        async with AsyncSessionLocal() as db:
            chunks = (
                await db.scalars(
                    select(MaterialChunk)
                    .where(MaterialChunk.material_id == material_id)
                    .order_by(MaterialChunk.position)
                )
            ).all()
            if not chunks:
                raise AppError("SEARCH_INDEX_NOT_READY", "Material has no chunks to index.")

            for start in range(0, len(chunks), settings.embedding_batch_size):
                batch = chunks[start : start + settings.embedding_batch_size]
                embeddings = await client.embed_texts([chunk.text for chunk in batch])
                for chunk, embedding in zip(batch, embeddings, strict=True):
                    chunk.embedding = embedding
                    chunk.indexing_error = None

            material = await _get_material(db, material_id)
            if material is None or material.deleted_at is not None:
                return
            material.status = MaterialStatus.READY
            material.error_message = None
            material.updated_at = datetime.now(UTC)
            await db.commit()
        logger.info("index_material_completed", extra={"material_id": material_id})
    except Exception as exc:
        await mark_material_failed(material_id, exc)
        raise


async def mark_material_failed(material_id: str, exc: Exception) -> None:
    async with AsyncSessionLocal() as db:
        material = await _get_material(db, material_id)
        if material is None:
            return
        material.status = MaterialStatus.FAILED
        material.error_message = _error_message(exc)
        material.updated_at = datetime.now(UTC)
        await db.commit()


async def _get_material(db, material_id: str) -> Material | None:
    return await db.scalar(select(Material).where(Material.id == material_id))


def _error_message(exc: Exception) -> str:
    if isinstance(exc, AppError):
        return f"{exc.code}: {exc.message}"
    return f"{exc.__class__.__name__}: {exc}"
