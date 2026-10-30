"""
Audio file validation utilities.
Enforces file format, size, mime type, and integrity constraints.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO, Optional, Tuple, Union

from configure import get_config
from llm.exceptions import AudioValidationError


def validate_audio_file(
    file_or_path: Union[str, Path, BinaryIO],
    filename: Optional[str] = None,
    size_bytes: Optional[int] = None,
    content_type: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validates audio file against configured constraints:
    - Non-empty
    - File extension
    - File size limit (e.g. max 20MB)
    - MIME type if provided

    Returns:
        (is_valid, error_message_or_none)
    """
    config = get_config()
    max_bytes = config.audio.max_upload_mb * 1024 * 1024
    allowed_exts = [ext.lower().lstrip(".") for ext in config.audio.allowed_extensions]

    # Resolve filename
    actual_name = filename
    if not actual_name and isinstance(file_or_path, (str, Path)):
        actual_name = os.path.basename(str(file_or_path))

    if not actual_name:
        return False, "Audio filename could not be determined."

    ext = actual_name.split(".")[-1].lower() if "." in actual_name else ""
    if ext not in allowed_exts:
        return False, f"File format '.{ext}' is not supported. Allowed formats: {', '.join(allowed_exts)}"

    # Resolve size
    actual_size = size_bytes
    if actual_size is None and isinstance(file_or_path, (str, Path)):
        p = Path(file_or_path)
        if p.exists():
            actual_size = p.stat().st_size
    elif actual_size is None and hasattr(file_or_path, "size"):
        actual_size = getattr(file_or_path, "size")

    if actual_size is not None:
        if actual_size <= 0:
            return False, "Audio file is empty (0 bytes)."
        if actual_size > max_bytes:
            mb_actual = round(actual_size / (1024 * 1024), 2)
            return False, f"File size ({mb_actual}MB) exceeds the maximum allowed limit of {config.audio.max_upload_mb}MB."

    # Validate content-type if provided
    if content_type:
        clean_mime = content_type.split(";")[0].strip().lower()
        # Accept if mime starts with audio/ or matches allowed list
        if not clean_mime.startswith("audio/") and clean_mime not in config.audio.allowed_mime_types:
            return False, f"Invalid MIME type '{clean_mime}'. Expected an audio file."

    return True, None
