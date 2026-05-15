"""Main image upload helpers (uses shared media service rules)."""

from __future__ import annotations

from fastapi import UploadFile

from app.core.config import Settings, get_settings
from app.services.media.upload_service import MediaUploadError, save_uploaded_file_auto


def validate_main_image_url(url: str | None, settings: Settings | None = None) -> None:
    """Reject ``main_image`` URLs whose extension is not an allowed image type."""
    if not url or not str(url).strip():
        return
    s = settings or get_settings()
    path = str(url).split("?")[0]
    if "." not in path:
        raise ValueError("main_image URL must include a file extension.")
    ext = path.rsplit(".", 1)[-1].lower().lstrip(".")
    if ext not in s.media_extension_allowlist("image"):
        allowed = ", ".join(sorted(s.media_extension_allowlist("image")))
        raise ValueError(f"main_image must use an allowed image extension: {allowed}")


async def resolve_main_image(
    *,
    upload: UploadFile | None,
    url: str | None,
    settings: Settings | None = None,
) -> str | None:
    """
    Prefer uploaded file (validated as image); otherwise use URL (extension-checked).
  """
    s = settings or get_settings()
    if upload is not None and upload.filename:
        try:
            result = await save_uploaded_file_auto(upload, settings=s, strict_content_type=False)
        except MediaUploadError as e:
            raise ValueError(str(e)) from e
        if result.file_type != "image":
            raise ValueError("main_image file must be an image (jpg, jpeg, png, webp).")
        return result.file_url
    if url is not None and str(url).strip():
        validate_main_image_url(url, s)
        return str(url).strip()
    return None
