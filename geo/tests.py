from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse

from posts.models import Post

User = get_user_model()

TANGIER = (35.7595, -5.8340)
RABAT = (34.0209, -6.8417)  # ~250 km from Tangier


class NearbySearchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.near_post = Post.objects.create(
            author=self.user,
            content='near',
            location=Point(TANGIER[1], TANGIER[0], srid=4326),
            city='Tangier',
        )
        self.far_post = Post.objects.create(
            author=self.user,
            content='far',
            location=Point(RABAT[1], RABAT[0], srid=4326),
            city='Rabat',
        )

    def test_nearby_search_includes_close_post_and_excludes_far_post(self):
        url = reverse('geo:nearby_api')
        response = self.client.get(url, {'lat': TANGIER[0], 'lng': TANGIER[1], 'radius': 10})
        self.assertEqual(response.status_code, 200)
        ids = [f['properties']['id'] for f in response.json()['features']]
        self.assertIn(self.near_post.id, ids)
        self.assertNotIn(self.far_post.id, ids)

    def test_invalid_coordinates_are_rejected(self):
        url = reverse('geo:nearby_api')
        response = self.client.get(url, {'lat': 999, 'lng': 0, 'radius': 5})
        self.assertEqual(response.status_code, 400)
