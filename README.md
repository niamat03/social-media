# Nearby

A social media platform with an integrated geospatial layer: posts, profiles, comments, likes, follows, direct messages and notifications, plus location-aware discovery (nearby posts, an interactive map, and location search) built on PostgreSQL + PostGIS.

## Stack

- **Backend**: Django 6, PostgreSQL, PostGIS (GeoDjango)
- **Frontend**: Django templates, vanilla JavaScript (fetch API, no framework), hand-written CSS
- **Maps**: Leaflet + Esri World Street Map tiles, Nominatim (OpenStreetMap) for place search

## Features

- Authentication (register/login/logout), profiles with followers/following lists, avatars
- Posts with optional image, editing, deletion, hashtags, @mentions
- Comments (create/edit/delete), likes, saved posts
- Follow system, blocking, reporting
- Notifications (likes, comments, follows, mentions) and direct messages, both with lightweight polling for near-real-time updates
- Feed (Following/Recent), Explore (trending posts, suggested users), search
- Geolocated posts (optional, never auto-published), "near me" search via PostGIS `ST_DWithin`, GeoJSON API, interactive map with clustering and text-based location search
- Server-side authorization on every mutation, rate limiting on write endpoints, image upload validation

## Prerequisites

- Python 3.11+
- PostgreSQL with the **PostGIS** extension available
- On Windows, GeoDjango needs GDAL/GEOS/PROJ. If you have PostgreSQL installed via the official Windows installer, these DLLs usually already ship alongside it (see `GDAL_LIBRARY_PATH` / `GEOS_LIBRARY_PATH` below). Otherwise install [OSGeo4W](https://trac.osgeo.org/osgeo4w/).

## Setup

1. **Clone and create a virtual environment**

   ```bash
   git clone <this-repo-url>
   cd social-media
   python -m venv venv
   venv\Scripts\activate        # Windows
   # source venv/bin/activate   # macOS/Linux
   pip install -r requirements.txt
   ```

2. **Create the database and enable PostGIS**

   ```sql
   CREATE DATABASE social_media WITH ENCODING 'UTF8';
   \c social_media
   CREATE EXTENSION postgis;
   ```

3. **Configure environment variables**

   Copy `.env.example` to `.env` and fill in your own values:

   ```bash
   cp .env.example .env
   ```

   ```env
   DEBUG=True
   SECRET_KEY=generate-your-own-secret-key
   ALLOWED_HOSTS=127.0.0.1,localhost

   DB_NAME=social_media
   DB_USER=postgres
   DB_PASSWORD=your-own-postgres-password
   DB_HOST=localhost
   DB_PORT=5432

   # Windows only — point these at the GDAL/GEOS DLLs on your machine
   # (commonly found under the PostgreSQL install's bin/ folder, or an OSGeo4W install)
   GDAL_LIBRARY_PATH=C:/Program Files/PostgreSQL/16/bin/libgdal-34.dll
   GEOS_LIBRARY_PATH=C:/Program Files/PostgreSQL/16/bin/libgeos_c.dll
   ```

   `.env` is git-ignored — never commit it. `.env.example` documents the required variables without real values.

4. **Migrate and run**

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

   Visit `http://127.0.0.1:8000/`.

5. **(Optional) Seed demo data** — 20 demo users with geolocated posts around a sample area, for exercising the nearby-search/map features:

   ```bash
   python manage.py seed_demo_data
   # or, to wipe and reseed:
   python manage.py seed_demo_data --reset
   ```

## Project layout

```
config/       # settings, root urls
accounts/     # custom User model, auth, profiles, followers/following
posts/        # posts, comments, likes, saved posts, hashtags, reports
social/       # follow graph, blocking, notifications, explore, search
geo/          # nearby search (PostGIS), GeoJSON API, map page, location search
messaging/    # direct messages (conversations)
templates/    # Django templates
static/       # CSS, JS, icon sprite
```

## Running tests

```bash
python manage.py test
```
