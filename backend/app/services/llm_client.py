import httpx

from app.core.config import settings
from app.core.errors import AppError
from app.schemas.chat import SearchResultRead


class LLMClient:
    async def answer_question(self, *, question: str, contexts: list[SearchResultRead]) -> str:
        if settings.llm_api_url and settings.llm_api_key:
            return await self._answer_remote(question=question, contexts=contexts)
        return self._answer_locally(question=question, contexts=contexts)

    async def _answer_remote(self, *, question: str, contexts: list[SearchResultRead]) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是课程学习助手。只根据提供的课程资料片段回答。"
                    "如果资料不足，请明确说明不足，不要编造。"
                ),
            },
            {
                "role": "user",
                "content": build_course_prompt(question=question, contexts=contexts),
            },
        ]
        payload = {
            "model": settings.llm_model,
            "messages": messages,
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                response = await client.post(settings.llm_api_url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise AppError("AGENT_LLM_TIMEOUT", "LLM request timed out.", status_code=504) from exc
        except httpx.HTTPError as exc:
            raise AppError("AGENT_LLM_FAILED", "LLM request failed.", status_code=502) from exc

        body = response.json()
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise AppError("AGENT_LLM_INVALID_RESPONSE", "LLM returned no answer.", status_code=502)
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise AppError(
                "AGENT_LLM_INVALID_RESPONSE",
                "LLM returned an empty answer.",
                status_code=502,
            )
        return content.strip()

    def _answer_locally(self, *, question: str, contexts: list[SearchResultRead]) -> str:
        if not contexts:
            return (
                "当前课程没有检索到足够相关的 READY 资料。"
                "请先上传并等待资料解析、索引完成，或换一个问题试试。"
            )

        lines = [
            f"我根据已索引的课程资料，先围绕“{question}”整理出这些要点：",
            "",
        ]
        for index, context in enumerate(contexts[:3], start=1):
            source = _format_source(context)
            excerpt = _compact_text(context.text, 220)
            lines.append(f"{index}. {excerpt}（来源：{source}）")
        lines.extend(
            [
                "",
                (
                    "这是本地开发模式生成的资料归纳回答。配置 LLM API 后，"
                    "系统会基于同一批检索片段生成更自然的回答。"
                ),
            ]
        )
        return "\n".join(lines)


def build_course_prompt(*, question: str, contexts: list[SearchResultRead]) -> str:
    context_text = "\n\n".join(
        f"[片段 {index}]\n来源：{_format_source(context)}\n内容：{context.text}"
        for index, context in enumerate(contexts, start=1)
    )
    return (
        f"用户问题：{question}\n\n"
        f"课程资料片段：\n{context_text}\n\n"
        "请用中文回答，结构清晰。回答必须基于片段内容；资料不足时直接说明。"
    )


def _format_source(context: SearchResultRead) -> str:
    parts = [context.material_title]
    if context.section_title:
        parts.append(context.section_title)
    if context.page_no is not None:
        parts.append(f"第 {context.page_no} 页")
    if context.slide_no is not None:
        parts.append(f"第 {context.slide_no} 页幻灯片")
    return " / ".join(parts)


def _compact_text(text: str, max_length: int) -> str:
    compacted = " ".join(text.split())
    if len(compacted) <= max_length:
        return compacted
    return f"{compacted[: max_length - 1]}…"
