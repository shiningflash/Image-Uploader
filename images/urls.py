from django.urls import path

from .views import ImageDetailView, ImageListView, ImageUploadView, delete_image

urlpatterns = [
    path("", ImageUploadView.as_view(), name="image_upload"),
    path("image/<uuid:public_id>/", ImageDetailView.as_view(), name="image_detail"),
    path("image/<uuid:public_id>/delete/", delete_image, name="image_delete"),
    path("images/", ImageListView.as_view(), name="image_list"),
]
