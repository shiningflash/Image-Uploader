import logging
import time

from django.conf import settings
from django.http import JsonResponse
from django.urls import resolve

from core.utils import get_client_ip
from images.services import is_daily_quota_exceeded

logger = logging.getLogger(__name__)


class QuotaCheckMiddleware:
    """
    Middleware to reject requests from IPs that exceeded the daily upload quota
    *before* the view executes. This is especially useful for POSTs to `/`.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply to the upload endpoint and POST requests
        if (
            request.method == "POST"
            and resolve(request.path_info).url_name == "image_upload"
        ):
            client_ip = get_client_ip(request)
            if is_daily_quota_exceeded(client_ip):
                return JsonResponse(
                    {
                        "detail": "Daily quota reached (10 uploads per IP). Try again tomorrow."
                    },
                    status=429,
                )

        return self.get_response(request)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration = (time.time() - start) * 1000
        logger.info(
            f"{request.method} {request.path} from {request.META.get('REMOTE_ADDR')} - {response.status_code} ({duration:.2f} ms)"
        )
        return response


class FileSizeLimitMiddleware:
    """
    Rejects requests with a total body size above MAX_UPLOAD_SIZE before Django parses them.
    Prevents memory waste and unnecessary form validation.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.max_upload_size = getattr(
            settings, "MAX_UPLOAD_SIZE", 5 * 1024 * 1024
        )  # 5 MB default

    def __call__(self, request):
        content_length = request.META.get("CONTENT_LENGTH")
        if content_length is not None:
            try:
                size = int(content_length)
                if size > self.max_upload_size:
                    return JsonResponse(
                        {
                            "detail": f"File too large. Max size is {self.max_upload_size // (1024 * 1024)} MB."
                        },
                        status=413,  # 413 Payload Too Large
                    )
            except ValueError:
                pass
        return self.get_response(request)
