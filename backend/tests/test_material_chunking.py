from app.services.material_chunking import chunk_blocks, estimate_token_count
from app.services.material_parsing import ParsedBlock


def test_chunk_blocks_preserves_metadata_and_generates_stable_ids():
    blocks = [
        ParsedBlock(
            text="第一段内容。\n\n第二段内容。",
            page_no=3,
            section_title="第一章",
            metadata={"kind": "pdf_page"},
        )
    ]

    first = chunk_blocks("mat_1", blocks, chunk_size=200)
    second = chunk_blocks("mat_1", blocks, chunk_size=200)

    assert len(first) == 1
    assert first[0].id == second[0].id
    assert first[0].page_no == 3
    assert first[0].section_title == "第一章"
    assert first[0].metadata["kind"] == "pdf_page"
    assert first[0].token_count > 0


def test_long_text_is_split_with_ordered_positions():
    text = "知识点" * 400
    chunks = chunk_blocks("mat_2", [ParsedBlock(text=text)], chunk_size=120, chunk_overlap=20)

    assert len(chunks) > 1
    assert [chunk.position for chunk in chunks] == list(range(len(chunks)))
    assert all(len(chunk.text) <= 120 for chunk in chunks)


def test_estimate_token_count_handles_mixed_text():
    assert estimate_token_count("hello world 知识点") == 5
