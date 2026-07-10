import math
from hashlib import blake2b

import httpx

from app.core.config import settings
from app.core.errors import AppError


class EmbeddingClient:
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if settings.embedding_api_url and settings.embedding_api_key:
            return await self._embed_remote(texts)
        return [deterministic_embedding(text, settings.embedding_dimension) for text in texts]

    async def _embed_remote(self, texts: list[str]) -> list[list[float]]:
        headers = {
            "Authorization": f"Bearer {settings.embedding_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.embedding_model,
            "input": texts,
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    settings.embedding_api_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AppError("SEARCH_EMBEDDING_FAILED", "Embedding API request failed.") from exc

        body = response.json()
        data = body.get("data")
        if not isinstance(data, list):
            raise AppError("SEARCH_EMBEDDING_FAILED", "Embedding API returned invalid data.")

        sorted_data = sorted(data, key=lambda item: item.get("index", 0))
        embeddings = [item.get("embedding") for item in sorted_data]
        if len(embeddings) != len(texts) or any(not isinstance(item, list) for item in embeddings):
            raise AppError("SEARCH_EMBEDDING_FAILED", "Embedding API returned incomplete vectors.")
        return embeddings


def deterministic_embedding(text: str, dimensions: int) -> list[float]:
    values: list[float] = []
    seed = text.encode("utf-8")
    counter = 0
    while len(values) < dimensions:
        digest = blake2b(seed + counter.to_bytes(4, "big"), digest_size=32).digest()
        for index in range(0, len(digest), 2):
            integer = int.from_bytes(digest[index : index + 2], "big")
            values.append((integer / 32767.5) - 1.0)
            if len(values) == dimensions:
                break
        counter += 1

    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]
