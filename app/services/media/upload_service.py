"""Chunked file writes with extension allowlists (no trusted original names)."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from fastapi import UploadFile

if TYPE_CHECKING:
    from app.core.config import Settings


class MediaUploadError(ValueError):
    """Invalid type, size, or missing extension."""


@dataclass(frozen=True)
class MediaUploadResult:
    file_name: str
    file_path: str
    file_url: str
    file_type: Literal["image", "video", "file"]
    file_size: int


_EXT_RE = re.compile(r"^[a-z0-9]{1,15}$")


def _parse_extension(filename: str | None) -> str:
    if not filename or "." not in filename:
        raise MediaUploadError("Could not determine a file extension. Upload a file with a valid extension.")
    raw = filename.rsplit(".", 1)[-1].strip().lower().lstrip(".")
    if not _EXT_RE.match(raw):
        raise MediaUploadError("Invalid file extension.")
    return raw


def _safe_extension(filename: str | None, allow: set[str]) -> str:
    raw = _parse_extension(filename)
    if raw not in allow:
        raise MediaUploadError(f"Extension .{raw} is not allowed for this upload type.")
    return raw


def detect_media_kind(upload: UploadFile, settings: Settings) -> Literal["image", "video", "file"]:
    """
    Decide storage category from extension lists and optional Content-Type.
    If an extension appears in more than one list, Content-Type is used when possible;
    otherwise priority is video, then image, then general file.
    """
    ext = _parse_extension(upload.filename)
    img = settings.media_extension_allowlist("image")
    vid = settings.media_extension_allowlist("video")
    doc = settings.media_extension_allowlist("file")
    in_v = ext in vid
    in_i = ext in img
    in_d = ext in doc
    if not (in_v or in_i or in_d):
        raise MediaUploadError(
            f"Extension .{ext} is not allowed. Configure ACCEPTED_IMAGE_TYPES, "
            "ACCEPTED_VIDEO_TYPES, and/or ACCEPTED_FILE_TYPES."
        )

    if in_v and not in_i and not in_d:
        return "video"
    if in_i and not in_v and not in_d:
        return "image"
    if in_d and not in_v and not in_i:
        return "file"

    ct = (upload.content_type or "").lower()
    if ct.startswith("video/"):
        return "video"
    if ct.startswith("image/"):
        return "image"
    if ct.startswith("application/") or ct.startswith("text/"):
        return "file"

    if in_v:
        return "video"
    if in_i:
        return "image"
    return "file"


def _subdir_for(kind: Literal["image", "video", "file"]) -> str:
    return {"image": "images", "video": "videos", "file": "files"}[kind]


async def save_uploaded_file(
    upload: UploadFile,
    *,
    kind: Literal["image", "video", "file"],
    settings: Settings,
    strict_content_type: bool = True,
) -> MediaUploadResult:
    """
    Stream `upload` to disk in chunks; never loads the whole file into memory.
    Generates a new random base name; only the extension is taken from the client filename.
    """
    allow = settings.media_extension_allowlist(kind)
    ext = _safe_extension(upload.filename, allow)
    max_bytes = {
        "image": settings.max_image_upload_bytes,
        "video": settings.max_video_upload_bytes,
        "file": settings.max_general_file_upload_bytes,
    }[kind]

    if strict_content_type and upload.content_type:
        ct = upload.content_type.lower()
        if kind == "image" and not ct.startswith("image/"):
            raise MediaUploadError("Content-Type must be an image type for this endpoint.")
        if kind == "video" and not ct.startswith("video/"):
            raise MediaUploadError("Content-Type must be a video type for this endpoint.")

    sub = _subdir_for(kind)
    root = settings.media_assets_path
    dest_dir = root / sub
    dest_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"{secrets.token_hex(16)}.{ext}"
    dest_path = dest_dir / file_name

    chunk = settings.upload_chunk_size_bytes
    total = 0
    try:
        with dest_path.open("wb") as out:
            while True:
                block = await upload.read(chunk)
                if not block:
                    break
                total += len(block)
                if total > max_bytes:
                    raise MediaUploadError("File exceeds the maximum allowed size for this type.")
                out.write(block)
    except MediaUploadError:
        dest_path.unlink(missing_ok=True)
        raise
    except Exception:
        dest_path.unlink(missing_ok=True)
        raise

    if total == 0:
        dest_path.unlink(missing_ok=True)
        raise MediaUploadError("Empty upload.")

    rel = f"{sub}/{file_name}"
    prefix = settings.assets_url_path_prefix.rstrip("/")
    url = f"{prefix}/{rel}"
    return MediaUploadResult(
        file_name=file_name,
        file_path=rel,
        file_url=url,
        file_type=kind,
        file_size=total,
    )


async def save_uploaded_file_auto(
    upload: UploadFile,
    *,
    settings: Settings,
    strict_content_type: bool = False,
) -> MediaUploadResult:
    """Detect image vs video vs file, then save with the correct limits and folder."""
    kind = detect_media_kind(upload, settings)
    return await save_uploaded_file(
        upload,
        kind=kind,
        settings=settings,
        strict_content_type=strict_content_type,
    )


async def save_many_uploads_auto(
    uploads: list[UploadFile],
    *,
    settings: Settings,
) -> list[tuple[UploadFile, MediaUploadResult | None, str | None]]:
    """
    Process each upload independently. Does not stop on first failure.
    Returns (upload, result_or_none, error_message_or_none) per item.
    """
    out: list[tuple[UploadFile, MediaUploadResult | None, str | None]] = []
    for upload in uploads:
        try:
            res = await save_uploaded_file_auto(upload, settings=settings, strict_content_type=False)
            out.append((upload, res, None))
        except MediaUploadError as e:
            out.append((upload, None, str(e)))
        except Exception as e:  # pragma: no cover - defensive
            out.append((upload, None, str(e)))
    return out
