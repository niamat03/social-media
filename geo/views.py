import json
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.cache import cache
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.urls import reverse

from config.throttle import rate_limit
from posts.models import Post
from social.block_utils import blocked_user_ids_either_way
from social.models import Follow

MAX_RESULTS = 200
DEFAULT_RADIUS_KM = 5

NOMINATIM_SEARCH_URL = 'https://nominatim.openstreetmap.org/search'
NOMINATIM_USER_AGENT = 'NearbySocialApp/1.0 (dev/demo use)'


def nearby_posts_api(request):
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
    except (TypeError, ValueError):
        return HttpResponseBadRequest('lat and lng are required numbers')

    try:
        radius_km = float(request.GET.get('radius', DEFAULT_RADIUS_KM))
    except ValueError:
        return HttpResponseBadRequest('radius must be a number')

    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return HttpResponseBadRequest('Invalid coordinates')

    radius_km = min(max(radius_km, 0.1), settings.GEO_MAX_RADIUS_KM)
    user_point = Point(lng, lat, srid=4326)
    scope = request.GET.get('scope', 'all')

    posts = (
        Post.objects.filter(location__isnull=False)
        .filter(location__distance_lte=(user_point, D(km=radius_km)))
        .exclude(author_id__in=blocked_user_ids_either_way(request.user))
    )

    if scope == 'following' and request.user.is_authenticated:
        following_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
        posts = posts.filter(author_id__in=following_ids)

    posts = (
        posts.annotate(distance=Distance('location', user_point))
        .select_related('author')
        .order_by('distance')[:MAX_RESULTS]
    )

    features = [
        {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [post.location.x, post.location.y],
            },
            'properties': {
                'id': post.id,
                'author': post.author.get_display_name(),
                'author_username': post.author.username,
                'content': post.content[:140],
                'created_at': post.created_at.strftime('%b %d, %Y'),
                'location_name': post.location_name,
                'city': post.city,
                'like_count': post.like_count,
                'comment_count': post.comment_count,
                'distance_km': round(post.distance.km, 2),
                'url': reverse('posts:detail', args=[post.id]),
            },
        }
        for post in posts
    ]

    return JsonResponse({'type': 'FeatureCollection', 'features': features})


@rate_limit('geocode', limit=15, window=60)
def search_location_api(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return HttpResponseBadRequest('q is required')
    if len(query) > 200:
        return HttpResponseBadRequest('query is too long')

    cache_key = f'geocode:{query.lower()}'
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse({'results': cached})

    params = urllib.parse.urlencode({'q': query, 'format': 'json', 'limit': 5})
    request_obj = urllib.request.Request(
        f'{NOMINATIM_SEARCH_URL}?{params}',
        headers={'User-Agent': NOMINATIM_USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request_obj, timeout=5) as response:
            raw_results = json.loads(response.read().decode('utf-8'))
    except Exception:
        return JsonResponse({'results': []})

    results = [
        {
            'display_name': item.get('display_name', ''),
            'lat': float(item['lat']),
            'lon': float(item['lon']),
        }
        for item in raw_results[:5]
        if 'lat' in item and 'lon' in item
    ]
    cache.set(cache_key, results, timeout=3600)
    return JsonResponse({'results': results})


def map_view(request):
    return render(request, 'geo/map.html')
