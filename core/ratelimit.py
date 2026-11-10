"""Tiny fixed-window rate limiter backed by Django's cache."""
import hashlib

from django.conf import settings
from django.core.cache import cache


def client_ip(request):
    """Return the client address, honouring X-Forwarded-For only for the configured number of proxies."""
    proxies = getattr(settings, "TRUSTED_PROXY_COUNT", 0)
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if proxies and forwarded:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if len(parts) >= proxies:
            return parts[-proxies]
    return request.META.get("REMOTE_ADDR", "")


def hit(scope, identifier, limit, window):
    """Count one event. Returns True when the caller has gone over ``limit`` within ``window`` seconds."""
    key = f"rl:{scope}:{hashlib.sha256(identifier.encode()).hexdigest()[:32]}"
    cache.add(key, 0, window)
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
        count = 1
    return count > limit
