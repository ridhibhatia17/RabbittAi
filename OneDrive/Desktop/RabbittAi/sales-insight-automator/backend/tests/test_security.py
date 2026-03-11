"""Tests for the security module."""

import pytest
from unittest.mock import MagicMock

from app.security import validate_file, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES


def _make_upload(filename: str, size: int | None = None) -> MagicMock:
    mock = MagicMock()
    mock.filename = filename
    mock.size = size
    return mock


def test_valid_csv():
    validate_file(_make_upload("report.csv", 1024))


def test_valid_xlsx():
    validate_file(_make_upload("report.xlsx", 1024))


def test_invalid_extension():
    with pytest.raises(Exception) as exc_info:
        validate_file(_make_upload("report.pdf", 100))
    assert "Invalid file type" in str(exc_info.value.detail)


def test_file_too_large():
    with pytest.raises(Exception) as exc_info:
        validate_file(_make_upload("big.csv", MAX_FILE_SIZE_BYTES + 1))
    assert "exceeds maximum size" in str(exc_info.value.detail)


def test_file_size_none_passes():
    # When size header is absent, validation should still pass
    validate_file(_make_upload("ok.csv", None))
