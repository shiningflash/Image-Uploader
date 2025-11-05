from __future__ import annotations

import uuid

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from core.utils import get_client_ip, validate_image_size
from .forms import ImageUploadForm
from .models import ImageAsset
from .services import is_daily_quota_exceeded


class ImageUploadView(LoginRequiredMixin, View):
    """Authenticated users can upload an image (max 5 MB, 10 uploads per IP/day)."""

    template_name = "images/upload.html"
    login_url = "login"

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name, {"form": ImageUploadForm()})

    def post(self, request: HttpRequest) -> HttpResponse:
        client_ip = get_client_ip(request)

        # Enforce per-IP upload quota (10 uploads / 24h)
        if is_daily_quota_exceeded(client_ip):
            return render(
                request,
                self.template_name,
                {
                    "form": ImageUploadForm(),
                    "error": "Daily quota reached (10 uploads per IP). Try again tomorrow.",
                },
                status=429,
            )

        form = ImageUploadForm(request.POST, request.FILES)

        if form.is_valid():
            image_file = form.cleaned_data["image"]

            # Validate file size (max 5 MB)
            try:
                validate_image_size(image_file)
            except ValidationError as e:
                form.add_error("image", e.message)
                return render(request, self.template_name, {"form": form}, status=400)

            # Save image linked to current user
            image_obj = ImageAsset.objects.create(
                image=image_file,
                uploader_ip=client_ip,
                user=request.user,
            )

            return redirect("image_detail", public_id=image_obj.public_id)

        # Re-render form with validation errors
        return render(request, self.template_name, {"form": form}, status=400)


class ImageDetailView(LoginRequiredMixin, View):
    """Show a single image detail page with delete option for the owner."""

    template_name = "images/detail.html"
    login_url = "login"

    def get(self, request: HttpRequest, public_id: str) -> HttpResponse:
        try:
            uuid.UUID(str(public_id))
        except ValueError:
            raise Http404("Invalid image identifier")

        image_obj = get_object_or_404(ImageAsset, public_id=public_id)

        return render(
            request,
            self.template_name,
            {
                "image": image_obj,
                "can_delete": image_obj.user == request.user,
            },
        )


@login_required(login_url="login")
def delete_image(request: HttpRequest, public_id: str) -> HttpResponse:
    """Delete an image if and only if the current user is the owner."""

    if request.method != "POST":
        raise Http404()

    image_obj = get_object_or_404(ImageAsset, public_id=public_id)

    if image_obj.user != request.user:
        return HttpResponseForbidden("You are not authorized to delete this image.")

    # Delete file and DB record
    image_obj.image.delete(save=False)
    image_obj.delete()

    return HttpResponseRedirect(reverse("image_list"))


class ImageListView(LoginRequiredMixin, View):
    """Paginated list of all images uploaded by the logged-in user."""

    template_name = "images/list.html"
    login_url = "login"

    def get(self, request: HttpRequest) -> HttpResponse:
        page_number = request.GET.get("page", 1)
        per_page = 10

        queryset = (
            ImageAsset.objects.filter(user=request.user)
            .only("public_id", "image", "created_at", "uploader_ip")
            .order_by("-created_at")
        )

        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page_number)

        return render(
            request,
            self.template_name,
            {
                "images": page_obj.object_list,
                "page_obj": page_obj,
                "is_paginated": page_obj.has_other_pages(),
            },
        )
