from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Count
from django.utils import timezone

from .models import ImageAsset


def is_daily_quota_exceeded(ip: str, max_uploads: int = 10) -> bool:
    """
    Returns True if the given IP has reached its daily upload quota (resets at midnight).
    This is the simpler version (per calendar day).
    """
    today = date.today()
    return (
        ImageAsset.objects.filter(uploader_ip=ip, created_at__date=today).aggregate(
            count=Count("id")
        )["count"]
        >= max_uploads
    )


def is_24h_quota_exceeded(ip: str, max_uploads: int = 10) -> bool:
    """
    Returns True if the given IP has reached its quota within the *last 24 hours*.
    This is stricter and not tied to calendar reset.
    """
    window_start = timezone.now() - timedelta(hours=24)
    return (
        ImageAsset.objects.filter(
            uploader_ip=ip, created_at__gte=window_start
        ).aggregate(count=Count("id"))["count"]
        >= max_uploads
    )
