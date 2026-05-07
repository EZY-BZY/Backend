"""Map local upload results to domain media_type strings."""

from __future__ import annotations

from typing import Literal

from app.common.allenums import DocumentMediaKind

UploadKind = Literal["image", "video", "file"]


def fixed_asset_media_type_from_upload(kind: UploadKind) -> str:
    """Store upload category on ``assets_media.media_type`` (image / video / file)."""
    return kind


def document_media_kind_from_upload(kind: UploadKind) -> DocumentMediaKind:
    """Map detected upload kind to ``documents_media.media_type`` enum."""
    return {
        "image": DocumentMediaKind.IMAGES,
        "video": DocumentMediaKind.VIDEOS,
        "file": DocumentMediaKind.FILES,
    }[kind]
