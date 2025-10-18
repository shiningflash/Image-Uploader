from __future__ import annotations

from django.core.exceptions import ValidationError
from django.http import HttpRequest

MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024


def get_client_ip(request: HttpRequest) -> str:
    """
    Extract client IP address with reverse-proxy awareness.
    - Prefers X-Forwarded-For if present (first in chain)
    - Falls back to REMOTE_ADDR.
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def validate_image_size(uploaded_file) -> None:
    """
    Validate that uploaded image size does not exceed MAX_IMAGE_SIZE_MB.
    Raises ValidationError if too large.
    """
    if uploaded_file.size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(
            f"Image size exceeds {MAX_IMAGE_SIZE_MB} MB. Please upload a smaller file."
        )
