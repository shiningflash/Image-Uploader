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
    template_name = "images/upload.html"
    login_url = "login"

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name, {"form": ImageUploadForm()})

    def post(self, request: HttpRequest) -> HttpResponse:
        client_ip = get_client_ip(request)

        # Quota enforcement
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

            # Save image
            image_obj = ImageAsset.objects.create(
                image=image_file,
                uploader_ip=client_ip,
            )

            # Track ownership in session
            owned = request.session.get("owned_public_ids", [])
            owned.append(str(image_obj.public_id))
            request.session["owned_public_ids"] = owned
            request.session.modified = True

            return redirect("image_detail", public_id=image_obj.public_id)

        # If invalid, re-render with errors
        return render(request, self.template_name, {"form": form}, status=400)


class ImageDetailView(LoginRequiredMixin, View):
    template_name = "images/detail.html"
    login_url = "login"

    def get(self, request: HttpRequest, public_id: str) -> HttpResponse:
        try:
            uuid.UUID(str(public_id))
        except ValueError:
            raise Http404("Invalid image identifier")

        image_obj = get_object_or_404(ImageAsset, public_id=public_id)
        owned = request.session.get("owned_public_ids", [])
        return render(
            request,
            self.template_name,
            {
                "image": image_obj,
                "can_delete": str(image_obj.public_id) in owned,
            },
        )


@login_required(login_url="login")
def delete_image(request: HttpRequest, public_id: str) -> HttpResponse:
    if request.method != "POST":
        raise Http404()

    image_obj = get_object_or_404(ImageAsset, public_id=public_id)
    owned = request.session.get("owned_public_ids", [])

    if str(image_obj.public_id) not in owned:
        return HttpResponseForbidden("You are not authorized to delete this image.")

    image_obj.image.delete(save=False)
    image_obj.delete()

    # Update session ownership
    request.session["owned_public_ids"] = [
        pid for pid in owned if pid != str(public_id)
    ]
    request.session.modified = True

    return HttpResponseRedirect(reverse("image_upload"))


class ImageListView(LoginRequiredMixin, View):
    template_name = "images/list.html"
    login_url = "login"

    def get(self, request: HttpRequest) -> HttpResponse:
        page_number = request.GET.get("page", 1)
        per_page = 10

        paginator = Paginator(
            ImageAsset.objects.order_by("-created_at").only(
                "public_id", "image", "created_at", "uploader_ip"
            ),
            per_page,
        )
        page_obj = paginator.get_page(page_number)

        return render(
            request,
            self.template_name,
            {
                "images": page_obj.object_list,  # paginated result
                "page_obj": page_obj,
                "is_paginated": page_obj.has_other_pages(),
            },
        )
