from pathlib import Path

import pytest

from app.core.errors import AppError
from app.services.material_parsing import ParserFactory, clean_text, parse_material_file


def test_text_parser_extracts_blocks_and_section_titles(tmp_path: Path):
    path = tmp_path / "notes.md"
    path.write_text(
        "# 第一章 导论\n\n这里是课程内容。\n\n1.1 基本概念\n\n概念解释。",
        encoding="utf-8",
    )

    document = parse_material_file(path, "md")

    assert len(document.blocks) == 4
    assert document.blocks[0].section_title == "# 第一章 导论"
    assert document.blocks[-1].section_title == "1.1 基本概念"
    assert document.metadata["parser"] == "text"


def test_clean_text_collapses_redundant_whitespace():
    assert clean_text("  hello\t world\r\n\r\n\r\n next  ") == "hello world\n\nnext"


def test_image_parser_is_reserved_for_ocr_extension(tmp_path: Path):
    path = tmp_path / "diagram.png"
    path.write_bytes(b"not-real-image")

    with pytest.raises(AppError) as exc_info:
        ParserFactory.create("image").parse(path)

    assert exc_info.value.code == "PARSE_UNSUPPORTED_TYPE"
