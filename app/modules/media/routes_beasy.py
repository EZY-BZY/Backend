"""Beasy-only media upload endpoints (chunked saves)."""

from fastapi import APIRouter, File, UploadFile

from app.common.api_response import ApiResponse, json_error, json_success
from app.common.allenums import ResponseEnum
from app.core.config import get_settings
from app.modules.beasy_employees.dependencies import CurrentEmployeeRequired
from app.modules.media.schemas import MediaBatchItemResponse, MediaUploadResponse
from app.services.media.upload_service import (
    MediaUploadError,
    save_many_uploads_auto,
    save_uploaded_file,
    save_uploaded_file_auto,
)

router = APIRouter(prefix="/media", tags=["Media Uploads (Beasy)"])


@router.post(
    "/upload/image",
    response_model=ApiResponse[MediaUploadResponse],
    summary="Upload image (chunked)",
)
async def upload_image(
    _: CurrentEmployeeRequired,
    file: UploadFile = File(..., description="Image file"),
):
    settings = get_settings()
    try:
        result = await save_uploaded_file(file, kind="image", settings=settings, strict_content_type=True)
    except MediaUploadError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        MediaUploadResponse(
            file_name=result.file_name,
            file_path=result.file_path,
            file_url=result.file_url,
            file_type=result.file_type,
            file_size=result.file_size,
        ).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "/upload/video",
    response_model=ApiResponse[MediaUploadResponse],
    summary="Upload video (chunked)",
)
async def upload_video(
    _: CurrentEmployeeRequired,
    file: UploadFile = File(..., description="Video file"),
):
    settings = get_settings()
    try:
        result = await save_uploaded_file(file, kind="video", settings=settings, strict_content_type=True)
    except MediaUploadError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        MediaUploadResponse(
            file_name=result.file_name,
            file_path=result.file_path,
            file_url=result.file_url,
            file_type=result.file_type,
            file_size=result.file_size,
        ).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "/upload/file",
    response_model=ApiResponse[MediaUploadResponse],
    summary="Upload general file (chunked)",
)
async def upload_general_file(
    _: CurrentEmployeeRequired,
    file: UploadFile = File(..., description="Document or other allowed file"),
):
    settings = get_settings()
    try:
        result = await save_uploaded_file(file, kind="file", settings=settings, strict_content_type=True)
    except MediaUploadError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        MediaUploadResponse(
            file_name=result.file_name,
            file_path=result.file_path,
            file_url=result.file_url,
            file_type=result.file_type,
            file_size=result.file_size,
        ).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "/upload/auto",
    response_model=ApiResponse[MediaUploadResponse],
    summary="Upload one file; type detected automatically",
)
async def upload_auto(
    _: CurrentEmployeeRequired,
    file: UploadFile = File(..., description="Image, video, or allowed document"),
):
    """Saves under images/, videos/, or files/ based on extension (and Content-Type if ambiguous)."""
    settings = get_settings()
    try:
        result = await save_uploaded_file_auto(file, settings=settings, strict_content_type=False)
    except MediaUploadError as e:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details=str(e))
    return json_success(
        MediaUploadResponse(
            file_name=result.file_name,
            file_path=result.file_path,
            file_url=result.file_url,
            file_type=result.file_type,
            file_size=result.file_size,
        ).model_dump(),
        message=ResponseEnum.SUCCESS.value,
    )


@router.post(
    "/upload/batch",
    response_model=ApiResponse[list[MediaBatchItemResponse]],
    summary="Upload many files; each type detected automatically",
)
async def upload_batch_auto(
    _: CurrentEmployeeRequired,
    files: list[UploadFile] = File(..., description="Multiple files (repeat form field 'files')"),
):
    """
    Each part is classified independently (image / video / general file) and stored
    in the matching folder. Per-file failures do not roll back successful uploads in the same request.
    """
    settings = get_settings()
    if not files:
        return json_error(ResponseEnum.FAIL.value, http_status=400, details="No files were uploaded.")
    if len(files) > settings.max_batch_upload_files:
        return json_error(
            ResponseEnum.FAIL.value,
            http_status=400,
            details=f"Too many files. Maximum is {settings.max_batch_upload_files}.",
        )
    rows = await save_many_uploads_auto(files, settings=settings)
    items: list[MediaBatchItemResponse] = []
    for upload, result, err in rows:
        if result is not None:
            items.append(
                MediaBatchItemResponse(
                    original_filename=upload.filename,
                    success=True,
                    detail=MediaUploadResponse(
                        file_name=result.file_name,
                        file_path=result.file_path,
                        file_url=result.file_url,
                        file_type=result.file_type,
                        file_size=result.file_size,
                    ),
                    error=None,
                )
            )
        else:
            items.append(
                MediaBatchItemResponse(
                    original_filename=upload.filename,
                    success=False,
                    detail=None,
                    error=err or "Upload failed",
                )
            )
    ok = sum(1 for i in items if i.success)
    return json_success([i.model_dump() for i in items], message=ResponseEnum.SUCCESS.value)
