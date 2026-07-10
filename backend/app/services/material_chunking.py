from dataclasses import dataclass, field
from hashlib import sha256

from app.services.material_parsing import ParsedBlock, clean_text

DEFAULT_CHUNK_SIZE = 700
DEFAULT_CHUNK_OVERLAP = 100


@dataclass(slots=True)
class ChunkDraft:
    id: str
    position: int
    text: str
    token_count: int
    page_no: int | None = None
    slide_no: int | None = None
    section_title: str | None = None
    metadata: dict = field(default_factory=dict)


def chunk_blocks(
    material_id: str,
    blocks: list[ParsedBlock],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[ChunkDraft]:
    drafts: list[ChunkDraft] = []
    for block in blocks:
        text = clean_text(block.text)
        if not text:
            continue
        for part in _split_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap):
            position = len(drafts)
            metadata = dict(block.metadata)
            metadata.update(
                {
                    "source_position": position,
                    "char_count": len(part),
                }
            )
            drafts.append(
                ChunkDraft(
                    id=_stable_chunk_id(material_id, position, part),
                    position=position,
                    text=part,
                    token_count=estimate_token_count(part),
                    page_no=block.page_no,
                    slide_no=block.slide_no,
                    section_title=block.section_title,
                    metadata=metadata,
                )
            )
    return drafts


def estimate_token_count(text: str) -> int:
    # Good enough for scheduling and chunk sizing; LLM-specific tokenizers can replace it later.
    ascii_words = len([part for part in text.split() if part.isascii()])
    non_ascii_chars = sum(1 for char in text if not char.isascii() and not char.isspace())
    return max(1, ascii_words + non_ascii_chars)


def _split_text(text: str, *, chunk_size: int, chunk_overlap: int) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_long_text(paragraph, chunk_size, chunk_overlap))
            continue

        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            chunks.append(current.strip())
            current = _with_overlap(current, chunk_overlap, paragraph)

    if current:
        chunks.append(current.strip())
    return [chunk for chunk in chunks if chunk]


def _split_long_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(end - chunk_overlap, start + 1)
    return [chunk for chunk in chunks if chunk]


def _with_overlap(previous: str, overlap: int, next_paragraph: str) -> str:
    if overlap <= 0:
        return next_paragraph
    tail = previous[-overlap:].strip()
    return f"{tail}\n\n{next_paragraph}".strip() if tail else next_paragraph


def _stable_chunk_id(material_id: str, position: int, text: str) -> str:
    digest = sha256(f"{material_id}:{position}:{text}".encode()).hexdigest()[:32]
    return f"chk_{digest}"
