"""Request Handler interface.

Defines the single entry point both the CLI and REST API call into.

The orchestration body is intentionally left as a stub until EXEC-17/EXEC-18
when all upstream modules exist.
"""

from __future__ import annotations

from aifme_scout.utils.models import ScanRequest, ScanResult


def handle(request: ScanRequest) -> ScanResult:
    """Handle a scan request and return a ScanResult.

    This is the single entry point for both CLI and REST API invocations.
    It validates the request, resolves configuration, orchestrates the
    pipeline stage sequence, and assembles the final result.

    NOTE: The orchestration body is not yet implemented. It will be
    completed in EXEC-17/EXEC-18 when all upstream modules exist.
    """
    raise NotImplementedError(
        "Request Handler orchestration is not yet implemented. "
        "It will be completed in EXEC-17/EXEC-18."
    )
