from django.conf import settings
from django.db import models

from core.models import PublicIdMixin, TimeStampedModel


class ImageAsset(PublicIdMixin, TimeStampedModel):
    """
    Minimal, explicit domain model for uploaded images.
    """

    image = models.ImageField(upload_to="uploads/%Y/%m/%d/")
    uploader_ip = models.GenericIPAddressField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="images",
        null=True,
        blank=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["uploader_ip", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.public_id}"
