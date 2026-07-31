"""Unit tests for the Request Handler interface."""

from typing import get_type_hints

import pytest

from aifme_scout.engine.request_handler import handle
from aifme_scout.utils.models import ScanRequest


def test_handle_raises_not_implemented() -> None:
    request = ScanRequest(target_url="https://example.com")
    with pytest.raises(NotImplementedError):
        handle(request)


def test_handle_signature_matches_architecture() -> None:
    hints = get_type_hints(handle)
    assert "return" in hints
