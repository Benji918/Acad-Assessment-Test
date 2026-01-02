import json
import logging
from django.http import JsonResponse
from decouple import config
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
import time
from core.utils import is_token_blacklisted
from rest_framework_simplejwt.tokens import AccessToken, TokenError

logger = logging.getLogger(__name__)

class RedisJWTBlacklistMiddleware(MiddlewareMixin):
    """
    Reject requests with a blacklisted JWT (Bearer token).
    Place this middleware early so blocked tokens are rejected before hitting views.
    """
    def process_request(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth:
            return None

        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.debug("Authorization header not Bearer")
            return None

        token = parts[1].strip()
        try:
            if is_token_blacklisted(token):
                logger.info("Rejected request with blacklisted token")
                return JsonResponse({"detail": "Token has been revoked."}, status=401)
        except Exception:
            return None

        return None


class ResponseTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time
        duration_ms = round(duration * 1000, 2)

        # Log it
        logger.info(f"{request.method} {request.path} - {response.status_code} - {duration_ms}ms")

        # Optionally add to response header
        response['X-Response-Time'] = f"{duration_ms}ms"

        return response