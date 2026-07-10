import pytest

from app.api.routes.materials import (
    MAX_MATERIAL_FILE_SIZE,
    _normalize_material_type,
    _validate_file_size,
    _validate_file_type,
)
from app.core.errors import AppError


def test_supported_material_file_types_are_inferred_from_extension():
    assert _validate_file_type("slides.PDF", "application/pdf") == "pdf"
    assert _validate_file_type("notes.docx", None) == "docx"
    assert _validate_file_type("diagram.jpg", "image/jpeg") == "image"


def test_unsupported_extension_is_rejected():
    with pytest.raises(AppError) as exc_info:
        _validate_file_type("malware.exe", "application/octet-stream")

    assert exc_info.value.code == "MATERIAL_UNSUPPORTED_TYPE"
    assert exc_info.value.status_code == 415


def test_unsupported_mime_type_is_rejected():
    with pytest.raises(AppError) as exc_info:
        _validate_file_type("notes.pdf", "application/x-msdownload")

    assert exc_info.value.code == "MATERIAL_UNSUPPORTED_TYPE"
    assert exc_info.value.status_code == 415


def test_material_file_size_limits_are_enforced():
    _validate_file_size(MAX_MATERIAL_FILE_SIZE)

    with pytest.raises(AppError) as empty_file:
        _validate_file_size(0)
    with pytest.raises(AppError) as too_large:
        _validate_file_size(MAX_MATERIAL_FILE_SIZE + 1)

    assert empty_file.value.code == "MATERIAL_EMPTY_FILE"
    assert too_large.value.code == "MATERIAL_TOO_LARGE"


def test_material_type_defaults_to_inferred_type_and_validates_override():
    assert _normalize_material_type(None, "pdf") == "pdf"
    assert _normalize_material_type(" image ", "png") == "image"

    with pytest.raises(AppError) as exc_info:
        _normalize_material_type("video", "pdf")

    assert exc_info.value.code == "MATERIAL_UNSUPPORTED_TYPE"
