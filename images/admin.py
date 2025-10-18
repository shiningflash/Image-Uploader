from django.contrib import admin

from .models import ImageAsset


@admin.register(ImageAsset)
class ImageAssetAdmin(admin.ModelAdmin):
    list_display = ("public_id", "uploader_ip", "created_at")
    readonly_fields = ("public_id", "created_at", "updated_at")
    search_fields = ("public_id", "uploader_ip")
    list_filter = ("created_at",)
