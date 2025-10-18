from __future__ import annotations

from django.db import models

from core.models import PublicIdMixin, TimeStampedModel


class ImageAsset(PublicIdMixin, TimeStampedModel):
    """
    Minimal, explicit domain model for uploaded images.
    - public_id: shareable stable ID (from PublicIdMixin)
    - created_at/updated_at: audit & ordering (from TimeStampedModel)
    """

    image = models.ImageField(upload_to="uploads/%Y/%m/%d/")
    uploader_ip = models.GenericIPAddressField()

    class Meta:
        indexes = [
            models.Index(fields=["uploader_ip", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.public_id}"
