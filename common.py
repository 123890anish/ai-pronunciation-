"""
Reusable common utilities for Pronunciation Assessment.
Contains pure helpers for text processing, timing, and error response structures.
"""
from __future__ import annotations

import os
import re
import string
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def get_current_utc_timestamp() -> str:
    """Return an ISO 8601 formatted UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


def normalize_text(text: Optional[str]) -> str:
    """
    Standardize text for comparison and scoring:
    - Unicode NFKC normalization
    - Stripping trailing/leading whitespace
    - Normalizing multiple spaces to single space
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", str(text))
    # Normalize fancy punctuation like smart quotes
    text = (
        text.replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
        .replace("—", "-")
    )
    return " ".join(text.split()).strip()


def strip_punctuation_lower(text: Optional[str]) -> str:
    """Return lowercase text stripped of punctuation for linguistic similarity comparisons."""
    normalized = normalize_text(text).lower()
    table = str.maketrans("", "", string.punctuation)
    return normalized.translate(table)


def calculate_levenshtein_distance(s1: str, s2: str) -> int:
    """
    Compute Levenshtein edit distance between two strings s1 and s2.
    Implemented iteratively to avoid heavy external dependencies.
    """
    if s1 == s2:
        return 0
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)

    v0 = list(range(len(s2) + 1))
    v1 = [0] * (len(s2) + 1)

    for i in range(len(s1)):
        v1[0] = i + 1
        for j in range(len(s2)):
            cost = 0 if s1[i] == s2[j] else 1
            v1[j + 1] = min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost)
        v0[:] = v1

    return v1[len(s2)]


def calculate_word_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity score between 0.0 and 100.0 based on word edit distance.
    """
    words1 = [w for w in strip_punctuation_lower(text1).split() if w]
    words2 = [w for w in strip_punctuation_lower(text2).split() if w]

    if not words1 and not words2:
        return 100.0
    if not words1 or not words2:
        return 0.0

    len1, len2 = len(words1), len(words2)
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if words1[i - 1] == words2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # deletion
                dp[i][j - 1] + 1,       # insertion
                dp[i - 1][j - 1] + cost # substitution
            )

    edit_dist = dp[len1][len2]
    max_len = max(len1, len2)
    similarity = max(0.0, 1.0 - (edit_dist / max_len))
    return round(similarity * 100.0, 1)


def build_error_response(
    message: str,
    error_code: str = "PROCESSING_ERROR",
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400
) -> Dict[str, Any]:
    """Create a standardized error response dictionary."""
    return {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {},
            "timestamp": get_current_utc_timestamp(),
        },
        "status_code": status_code,
    }


def build_success_response(
    data: Dict[str, Any],
    message: str = "Operation completed successfully"
) -> Dict[str, Any]:
    """Create a standardized success response dictionary."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": get_current_utc_timestamp(),
    }


def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filenames to prevent directory traversal and special chars."""
    basename = os.path.basename(filename)
    clean = re.sub(r"[^a-zA-Z0-9_\.-]", "_", basename)
    return clean[:120]
