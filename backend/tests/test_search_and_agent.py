import pytest

from app.models import ChatMessage, ChatMessageRole
from app.schemas.chat import SearchResultRead
from app.services.agent_service import _build_citations
from app.services.llm_client import LLMClient, build_course_prompt
from app.services.search_service import _cosine_similarity, _keyword_score, _tokenize


def test_keyword_score_matches_title_and_text():
    tokens = _tokenize("极限 定义")

    score = _keyword_score(tokens, "极限 定义", "极限是微积分中的基础定义。", "高等数学")

    assert score > 0


def test_cosine_similarity_is_normalized():
    assert _cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)
    assert _cosine_similarity([1, 0], [-1, 0]) == pytest.approx(0.0)
    assert _cosine_similarity(None, [1, 0]) == 0.0


def test_prompt_contains_question_and_sources():
    context = SearchResultRead(
        chunk_id="chunk-1",
        material_id="mat-1",
        material_title="第一章",
        material_type="pdf",
        text="导数描述函数变化率。",
        score=0.9,
        keyword_score=0.5,
        vector_score=0.8,
        page_no=3,
        slide_no=None,
        section_title="导数",
    )

    prompt = build_course_prompt(question="导数是什么？", contexts=[context])

    assert "导数是什么？" in prompt
    assert "第一章 / 导数 / 第 3 页" in prompt
    assert "导数描述函数变化率。" in prompt


@pytest.mark.asyncio
async def test_local_llm_fallback_uses_contexts():
    context = SearchResultRead(
        chunk_id="chunk-1",
        material_id="mat-1",
        material_title="课堂笔记",
        material_type="md",
        text="牛顿第二定律说明力等于质量乘以加速度。",
        score=0.9,
        keyword_score=0.5,
        vector_score=0.8,
        page_no=None,
        slide_no=None,
        section_title=None,
    )

    answer = await LLMClient().answer_question(question="牛顿第二定律是什么？", contexts=[context])

    assert "牛顿第二定律" in answer
    assert "课堂笔记" in answer


def test_answer_citations_preserve_source_fields():
    context = SearchResultRead(
        chunk_id="chunk-1",
        material_id="mat-1",
        material_title="课堂讲义",
        material_type="pdf",
        text="函数极限描述自变量趋近某点时函数值的趋势。",
        score=0.91,
        keyword_score=0.6,
        vector_score=0.8,
        page_no=5,
        slide_no=None,
        section_title="极限",
    )
    message = ChatMessage(
        id="answer-1",
        session_id="session-1",
        user_id="user-1",
        course_id="course-1",
        role=ChatMessageRole.ASSISTANT,
        content="回答",
    )

    citations = _build_citations(answer_message=message, contexts=[context], user_id="user-1")

    assert len(citations) == 1
    assert citations[0].answer_message_id == "answer-1"
    assert citations[0].material_id == "mat-1"
    assert citations[0].chunk_id == "chunk-1"
    assert citations[0].page_no == 5
    assert "函数极限" in citations[0].quote
