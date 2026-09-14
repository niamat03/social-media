import random

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import transaction

from posts.models import Comment, Like, Post
from social.models import Follow

User = get_user_model()

DEMO_PASSWORD = 'DemoPass123!'

# (first name, last name) pairs used to build usernames/display names.
NAMES = [
    ('Youssef', 'Amrani'), ('Salma', 'Idrissi'), ('Omar', 'Bennis'),
    ('Imane', 'Chaoui'), ('Karim', 'Fassi'), ('Nadia', 'Ziani'),
    ('Yassine', 'Alaoui'), ('Meryem', 'Tazi'), ('Anas', 'Benjelloun'),
    ('Douae', 'Saidi'), ('Reda', 'Naciri'), ('Hind', 'Lahlou'),
    ('Sofia', 'Bakkali'), ('Mehdi', 'Rifai'), ('Ines', 'Chraibi'),
    ('Adam', 'Berrada'), ('Lina', 'Mouline'), ('Zakaria', 'Idrissi'),
    ('Rim', 'Tahiri'), ('Amine', 'Sabri'),
]

# Real towns around Tangier so radius filtering (5/10/25/50 km) produces
# a realistic, varied spread of nearby vs. excluded results.
LOCATIONS = [
    ('Tangier city center', 'Tangier', 35.7595, -5.8340),
    ('Malabata beach', 'Tangier', 35.7830, -5.7890),
    ('Cap Spartel', 'Tangier', 35.7930, -5.9210),
    ('Ksar Sghir', 'Ksar Sghir', 35.8083, -5.5658),
    ('Fnideq corniche', 'Fnideq', 35.8497, -5.3572),
    ("M'diq marina", "M'diq", 35.6845, -5.3273),
    ('Tetouan medina', 'Tetouan', 35.5785, -5.3684),
    ('Asilah ramparts', 'Asilah', 35.4650, -6.0349),
    ('Chefchaouen blue streets', 'Chefchaouen', 35.1688, -5.2636),
]

POST_TEXTS = [
    'Amazing sunset by the strait today!',
    'New cafe just opened downtown, coffee is great.',
    'Anyone up for a walk along the medina this weekend?',
    'Traffic was crazy this morning.',
    'Just finished a great book, highly recommend it.',
    'Beautiful view from the beach this afternoon.',
    'Working on a new project, excited to share soon.',
    'Best tagine I have had in a while.',
    'Rainy day, perfect for staying in and reading.',
    'Exploring the old town, so much history here.',
    'Weekend market was packed but worth it.',
    'Caught a great show at the local theatre tonight.',
    'Early morning run along the corniche.',
    'Trying out a new recipe tonight, wish me luck.',
    'The view from up here never gets old.',
]

COMMENT_TEXTS = [
    'Love this!', 'So nice, take me next time.', 'Great shot.',
    'This looks amazing.', 'Where is this exactly?', 'Totally agree.',
    'Nice one!', 'Adding this to my list.',
]


def jitter(lat, lng, max_km=2.0):
    lat_offset = random.uniform(-max_km, max_km) / 111.0
    lng_offset = random.uniform(-max_km, max_km) / (111.0 * 0.81)  # ~cos(35.7deg)
    return lat + lat_offset, lng + lng_offset


class Command(BaseCommand):
    help = 'Seed the database with demo users and geolocated posts around Tangier for testing.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete previously seeded demo users (and their content) before reseeding.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reset']:
            deleted, _ = User.objects.filter(username__startswith='demo_').delete()
            self.stdout.write(self.style.WARNING(f'Removed {deleted} existing demo objects.'))

        users = []
        for first, last in NAMES:
            username = f'demo_{first.lower()}{last.lower()}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'display_name': f'{first} {last}',
                    'bio': random.choice([
                        'Coffee, code, and long walks.',
                        'Photographer at heart.',
                        'Exploring the north of Morocco.',
                        'Always up for good food and good company.',
                        'Sharing moments from around town.',
                    ]),
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            users.append(user)

        self.stdout.write(self.style.SUCCESS(f'{len(users)} demo users ready.'))

        posts = []
        for user in users:
            for _ in range(random.randint(1, 3)):
                has_location = random.random() < 0.75
                post = Post(author=user, content=random.choice(POST_TEXTS))
                if has_location:
                    name, city, lat, lng = random.choice(LOCATIONS)
                    jlat, jlng = jitter(lat, lng)
                    post.location = Point(jlng, jlat, srid=4326)
                    post.location_name = name
                    post.city = city
                post.save()
                posts.append(post)

        self.stdout.write(self.style.SUCCESS(f'{len(posts)} demo posts created.'))

        # Follow graph: each user follows a handful of random others.
        follow_count = 0
        for user in users:
            targets = random.sample([u for u in users if u != user], k=random.randint(3, 7))
            for target in targets:
                _, created = Follow.objects.get_or_create(follower=user, following=target)
                follow_count += created

        self.stdout.write(self.style.SUCCESS(f'{follow_count} follow relationships created.'))

        # Likes and comments for a livelier feed.
        like_count = 0
        comment_count = 0
        for post in posts:
            likers = random.sample(users, k=random.randint(0, min(8, len(users))))
            for liker in likers:
                _, created = Like.objects.get_or_create(user=liker, post=post)
                like_count += created

            for _ in range(random.randint(0, 3)):
                commenter = random.choice(users)
                Comment.objects.create(
                    post=post, author=commenter, content=random.choice(COMMENT_TEXTS)
                )
                comment_count += 1

        self.stdout.write(self.style.SUCCESS(f'{like_count} likes and {comment_count} comments created.'))
        self.stdout.write(self.style.SUCCESS(f'All demo accounts use password: {DEMO_PASSWORD}'))
