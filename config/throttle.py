from functools import wraps

from django.core.cache import cache
from django.http import JsonResponse


def rate_limit(action, limit=20, window=60):
    """Cap how many times an authenticated user can hit a view within `window` seconds.

    Uses Django's default cache (in-memory for a single dev process), which is
    enough to blunt accidental double-clicks and scripted abuse without adding
    infrastructure for what is still a small app.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            identifier = request.user.pk if request.user.is_authenticated else request.META.get('REMOTE_ADDR', 'anon')
            cache_key = f'throttle:{action}:{identifier}'
            count = cache.get(cache_key, 0)
            if count >= limit:
                return JsonResponse(
                    {'error': 'Too many requests. Please slow down and try again shortly.'},
                    status=429,
                )
            cache.set(cache_key, count + 1, timeout=window)
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
