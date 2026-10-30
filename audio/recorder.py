"""
Audio recorder storage and file management utilities.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional, Union

from common import sanitize_filename
from configure import get_config


def generate_audio_storage_path(user_id: Union[int, str], original_filename: str) -> str:
    """
    Generate an isolated, non-colliding storage path for a user's recording:
    media/recordings/user_<id>/<year>/<month>/<uuid>_<clean_filename>
    """
    clean_name = sanitize_filename(original_filename)
    now = datetime.now()
    unique_prefix = uuid.uuid4().hex[:8]
    rel_path = os.path.join(
        "recordings",
        f"user_{user_id}",
        now.strftime("%Y"),
        now.strftime("%m"),
        f"{unique_prefix}_{clean_name}",
    )
    return rel_path


def save_uploaded_audio(
    file_obj: BinaryIO,
    user_id: Union[int, str],
    filename: str,
) -> Path:
    """
    Saves an in-memory or uploaded file stream into the configured media root.
    """
    config = get_config()
    media_root = Path(config.audio.media_root).resolve()
    rel_path = generate_audio_storage_path(user_id, filename)
    target_path = media_root / rel_path

    target_path.parent.mkdir(parents=True, exist_ok=True)

    with open(target_path, "wb") as dest:
        for chunk in file_obj.chunks() if hasattr(file_obj, "chunks") else [file_obj.read()]:
            dest.write(chunk)

    return target_path
