import pytest

from app.services.embeddings import deterministic_embedding


def test_deterministic_embedding_has_expected_dimension_and_norm():
    embedding = deterministic_embedding("极限定义", 8)
    again = deterministic_embedding("极限定义", 8)

    assert embedding == again
    assert len(embedding) == 8
    assert sum(value * value for value in embedding) == pytest.approx(1.0)
