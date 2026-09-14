from django.urls import path

from . import views

app_name = 'geo'

urlpatterns = [
    path('map/', views.map_view, name='map'),
    path('api/posts/nearby/', views.nearby_posts_api, name='nearby_api'),
    path('api/search-location/', views.search_location_api, name='search_location_api'),
]
