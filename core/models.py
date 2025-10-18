from __future__ import annotations

import uuid as _uuid

from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base with auto-managed timestamps.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PublicIdMixin(models.Model):
    """
    Abstract mixin for a stable, shareable, non-PK public identifier.
    """

    public_id = models.UUIDField(
        default=_uuid.uuid4, unique=True, editable=False, db_index=True
    )

    class Meta:
        abstract = True
