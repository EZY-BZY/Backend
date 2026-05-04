"""API schemas for media upload responses."""

from typing import Literal

from pydantic import BaseModel, Field


class MediaUploadResponse(BaseModel):
    """Returned after a successful chunked upload."""

    file_name: str = Field(..., description="Stored file name (random + original extension)")
    file_path: str = Field(..., description="Path relative to the assets root, e.g. images/abc.jpg")
    file_url: str = Field(..., description="URL path clients can join with the API host")
    file_type: Literal["image", "video", "file"]
    file_size: int = Field(..., ge=0, description="Final size in bytes")


class MediaBatchItemResponse(BaseModel):
    """One entry from a multi-file auto-detect upload."""

    original_filename: str | None = Field(None, description="Client-provided name (untrusted)")
    success: bool
    detail: MediaUploadResponse | None = None
    error: str | None = Field(None, description="Present when success is false")
