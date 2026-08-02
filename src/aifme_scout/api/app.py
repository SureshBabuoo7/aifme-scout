"""REST API for AIFME Scout OSS."""

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from aifme_scout import __version__
from aifme_scout.engine.request_handler import handle
from aifme_scout.scanner import (
    FetchError,
    InvalidURLError,
    ResponseTooLargeError,
    RobotsDisallowedError,
    SSRFViolationError,
    UnsupportedContentTypeError,
)
from aifme_scout.utils.constants import ScanMode
from aifme_scout.utils.exceptions import ConfigurationError
from aifme_scout.utils.models import ScanRequest, ScanResult


class ScanApiRequest(BaseModel):
    """Request body for the /scan endpoint."""

    url: str = Field(..., description="Target URL to scan")
    output: Literal["json", "markdown", "both"] = Field(
        "both", description="Export format"
    )
    timeout: float | None = Field(None, description="Request timeout in seconds")
    user_agent: str | None = Field(None, description="Custom User-Agent header")
    mode: Literal["no-llm", "llm"] = Field("no-llm", description="Summary generation mode")

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("URL must not be empty")
        return value.strip()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str


class VersionResponse(BaseModel):
    """Version response."""

    version: str


app = FastAPI(
    title="AIFME Scout OSS API",
    description="Website and marketing intelligence toolkit API",
    version=__version__,
)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Redirect to API documentation."""
    return {"docs": "/docs", "openapi": "/openapi.json"}


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", version=__version__)


@app.get("/version", response_model=VersionResponse)
async def version() -> VersionResponse:
    """Version endpoint."""
    return VersionResponse(version=__version__)


@app.post("/scan", response_model=ScanResult)
async def scan(request: ScanApiRequest) -> ScanResult:
    """Scan a website and return the scan result.

    Args:
        request: The scan request body.

    Returns:
        ScanResult with the assembled scan output.

    Raises:
        HTTPException: With appropriate status code on failure.
    """
    try:
        scan_request = ScanRequest(
            target_url=request.url,
            mode=ScanMode(request.mode),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid request: {exc}") from exc

    try:
        result = handle(scan_request)
    except HTTPException:
        raise
    except InvalidURLError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FetchError as exc:
        raise HTTPException(status_code=408, detail=str(exc)) from exc
    except (
        RobotsDisallowedError,
        SSRFViolationError,
        ResponseTooLargeError,
        UnsupportedContentTypeError,
    ) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {exc}"
        ) from exc

    return result

